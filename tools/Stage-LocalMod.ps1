param(
    [ValidateSet('Stage','Install')][string]$Mode = 'Stage',
    [string]$GameDirectory = 'D:\steam\steamapps\common\Kenshi'
)
$ErrorActionPreference = 'Stop'
# 不调用任何编译器。用户先编译 Release|x64，Stage 只复制自建 DLL 到项目分发包。
$projectRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$compiledDll = Join-Path $projectRoot '..\bin\Release\JudgementCutEnd.dll'
$packageRoot = Join-Path $projectRoot 'package\JudgementCutEnd'
$backupStamp = 'JudgementCutEnd-' + (Get-Date -Format 'yyyyMMdd-HHmmss-fffffff')
function Copy-BackedFile([string]$source, [string]$destination) {
    # 仅复制单个字面路径；覆盖前双备份；不删除旧文件，不拼接 shell 命令。
    if (Test-Path -LiteralPath $destination) {
        $absolute = [IO.Path]::GetFullPath($destination)
        $relative = $absolute.Substring(0,1) + '\' + $absolute.Substring(3)
        foreach ($backupBase in @('D:\CodexBackups', 'E:\AIWorkSpace\_backups')) {
            $backupPath = Join-Path (Join-Path $backupBase $backupStamp) $relative
            [IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($backupPath)) | Out-Null
            if (Test-Path -LiteralPath $backupPath) { throw "Backup already exists: $backupPath" }
            Copy-Item -LiteralPath $destination -Destination $backupPath
        }
    }
    [IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($destination)) | Out-Null
    Copy-Item -LiteralPath $source -Destination $destination
    if ((Get-FileHash -LiteralPath $source).Hash -ne (Get-FileHash -LiteralPath $destination).Hash) { throw "Copy verification failed: $destination" }
}
# 直接解析 PE 导出表，不调用编译器或依赖 dumpbin。
# 只检查真正导出名称，不能用 DLL 内普通字符串冒充 GetProcAddress 合同。
function Get-PeExportNames([byte[]]$buffer, [int]$pe) {
    $sections = [BitConverter]::ToUInt16($buffer,$pe+6)
    $optionalSize = [BitConverter]::ToUInt16($buffer,$pe+20)
    $optional = $pe+24
    $table = $optional+$optionalSize
    if ($sections -lt 1 -or $sections -gt 96 -or $optionalSize -lt 120 -or $table+40*$sections -gt $buffer.Length -or [BitConverter]::ToUInt16($buffer,$optional) -ne 523) { throw 'Invalid PE64 header.' }
    function Convert-PeRva([uint32]$rva, [int]$length) {
        # RVA 必须落在可读取的原始节内；拒绝溢出、虚拟未落盘数据和截断文件。
        for ($i=0; $i -lt $sections; $i++) {
            $entry=$table+40*$i
            [uint64]$start=[BitConverter]::ToUInt32($buffer,$entry+12)
            [uint64]$size=[BitConverter]::ToUInt32($buffer,$entry+16)
            [uint64]$raw=[BitConverter]::ToUInt32($buffer,$entry+20)
            [uint64]$address=$rva
            if ($address -ge $start -and $address+$length -le $start+$size -and $raw+$address-$start+$length -le $buffer.Length) { return [int]($raw+$address-$start) }
        }
        throw 'Invalid export RVA.'
    }
    $exportRva=[BitConverter]::ToUInt32($buffer,$optional+112)
    if ($exportRva -eq 0) { throw 'DLL has no exports.' }
    $export=Convert-PeRva $exportRva 40
    $count=[BitConverter]::ToUInt32($buffer,$export+24)
    if ($count -lt 1 -or $count -gt 65536) { throw 'Invalid export name count.' }
    $names=Convert-PeRva ([BitConverter]::ToUInt32($buffer,$export+32)) ([int](4*$count))
    for ($i=0; $i -lt $count; $i++) {
        $rva=[BitConverter]::ToUInt32($buffer,$names+4*$i)
        $name=Convert-PeRva $rva 1
        $end=$name
        while ($end-$name -lt 256) {
            $offset=Convert-PeRva ([uint32]($rva+($end-$name))) 1
            if ($buffer[$offset] -eq 0) { break }
            $end++
        }
        if ($end-$name -ge 256) { throw 'Unterminated export name.' }
        [Text.Encoding]::ASCII.GetString($buffer,$name,$end-$name)
    }
}
if (-not (Test-Path -LiteralPath $compiledDll)) { throw 'Build JudgementCutEnd.vcxproj in Release|x64 first; DLL is absent.' }
$dllBytes = [IO.File]::ReadAllBytes($compiledDll)
if ($dllBytes.Length -lt 1024 -or $dllBytes[0] -ne 77 -or $dllBytes[1] -ne 90) { throw 'Invalid DLL.' }
$peOffset = [BitConverter]::ToInt32($dllBytes,60)
if ($peOffset -lt 64 -or $peOffset+24 -gt $dllBytes.Length -or [BitConverter]::ToUInt32($dllBytes,$peOffset) -ne 17744 -or [BitConverter]::ToUInt16($dllBytes,$peOffset+4) -ne 34404) { throw 'DLL must be x64 PE.' }
# 本机 RE_Kenshi 按 C++ 修饰名查找入口；旧版 extern "C" DLL 必须在任何复制前拒绝。
$exports = @(Get-PeExportNames $dllBytes $peOffset)
if ($exports -cnotcontains '?startPlugin@@YAXXZ') { throw 'RE_Kenshi entry ?startPlugin@@YAXXZ is missing. Rebuild JudgementCutEnd in Release|x64; do not install the old DLL.' }
# 动画已升级JCECLIP2和JCEPHM2；不能凭新时间戳把旧DLL与新资源混装。
$sourceText=[IO.File]::ReadAllText((Join-Path $projectRoot 'JudgementCutEnd.cpp'))
$sourceMatch=[regex]::Match($sourceText,'version=([0-9]+\.[0-9]+\.[0-9]+-dev)')
if (-not $sourceMatch.Success -or -not ([Text.Encoding]::ASCII.GetString($dllBytes).Contains('version='+$sourceMatch.Groups[1].Value))) {
    throw 'DLL version does not match source/resource contract. Rebuild Release|x64 before staging/installing.'
}
# 工程/源码修正后，禁止把上次编译的旧 DLL 再安装；这里只读时间戳，不触发编译。
$latestSource = @(Get-Item -LiteralPath (Join-Path $projectRoot 'JudgementCutEnd.cpp'), (Join-Path $projectRoot 'JudgementCutEnd.vcxproj') | Sort-Object LastWriteTimeUtc -Descending)[0]
if ((Get-Item -LiteralPath $compiledDll).LastWriteTimeUtc -lt $latestSource.LastWriteTimeUtc) { throw 'DLL predates source/project changes. Rebuild JudgementCutEnd in Release|x64 before staging/installing.' }
if (Get-Process -Name 'kenshi_x64' -ErrorAction SilentlyContinue) { throw 'Close Kenshi before staging/installing. This script does not stop the game.' }
Copy-BackedFile $compiledDll (Join-Path $packageRoot 'JudgementCutEnd.dll')
Write-Output "Staged DLL: $packageRoot"
if ($Mode -eq 'Install') {
    $gameRoot = [IO.Path]::GetFullPath($GameDirectory)
    if (-not (Test-Path -LiteralPath (Join-Path $gameRoot 'kenshi_x64.exe'))) { throw 'Kenshi game directory not found.' }
    if (-not (Test-Path -LiteralPath (Join-Path $gameRoot 'KenshiLib.dll'))) { throw 'Install RE_Kenshi/KenshiLib first.' }
    $modRoot = Join-Path $gameRoot 'mods\JudgementCutEnd'
    foreach ($file in (Get-ChildItem -LiteralPath $packageRoot -Recurse -File)) {
        $relative = $file.FullName.Substring($packageRoot.Length+1)
        if ($relative.StartsWith('logs\')) { continue }
        Copy-BackedFile $file.FullName (Join-Path $modRoot $relative)
    }
    Write-Output "Installed files into $modRoot. Enable JudgementCutEnd in the launcher yourself. mods.cfg and saves were not changed."
}
Write-Output "Existing overwritten files, if any, were backed up with task directory $backupStamp."
