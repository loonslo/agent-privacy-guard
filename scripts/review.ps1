# One-command delivery launcher. No installation, PATH changes, hooks or target writes.
param($Repo = '.', $Paths = @(), $Mode = 'files', $Source = 'auto', $Tip = $null, $Base = $null)

$ErrorActionPreference = 'Stop'
$global:LASTEXITCODE = 1
try {
    if ($args.Count -ne 0 -or $Mode -notin @('files', 'staged', 'push', 'doctor')) {
        throw 'Invalid launcher arguments'
    }
    if ($Source -notin @('auto', 'memory', 'chat_history')) { throw 'Invalid source' }
    if ($Mode -eq 'files' -and @($Paths).Count -eq 0) { throw 'Explicit files required' }
    if ($Mode -ne 'files' -and (@($Paths).Count -ne 0 -or $Source -ne 'auto')) {
        throw 'Files and source require files mode'
    }
    if ($Mode -eq 'push' -and (-not $Tip -or -not $Base)) { throw 'Explicit push range required' }
    if ($Mode -ne 'push' -and ($Tip -or $Base)) { throw 'Push range requires push mode' }
    if (-not [Environment]::Is64BitProcess -or [Environment]::OSVersion.Platform -ne [PlatformID]::Win32NT) {
        throw 'Windows x64 launcher required'
    }
    $reviewRoot = [IO.Path]::GetFullPath((Resolve-Path -LiteralPath $Repo).Path)
    if (-not (Test-Path -LiteralPath $reviewRoot -PathType Container)) { throw 'Review root required' }
    $temporaryRoot = [IO.Path]::GetFullPath([IO.Path]::GetTempPath()).TrimEnd('\', '/')
    $rootPrefix = $reviewRoot.TrimEnd('\', '/') + [IO.Path]::DirectorySeparatorChar
    if ($temporaryRoot.Equals($reviewRoot.TrimEnd('\', '/'), [StringComparison]::OrdinalIgnoreCase) -or
        $temporaryRoot.StartsWith($rootPrefix, [StringComparison]::OrdinalIgnoreCase)) {
        throw 'Temporary directory must be outside review root'
    }
    $deliveryRoot = Join-Path $temporaryRoot ('privacy-review-run-' + [guid]::NewGuid().ToString('N'))
    New-Item -ItemType Directory -Path $deliveryRoot | Out-Null
    $release = 'https://github.com/loonslo/agent-privacy-guard/releases/download/v0.4.0'
    $archive = Join-Path $deliveryRoot 'privacy-guard-0.4.0-windows-x64.zip'
    Invoke-WebRequest -Uri "$release/privacy-guard-0.4.0-windows-x64.zip" -OutFile $archive -UseBasicParsing
    # Pinned in the versioned launcher, not taken from the downloaded ZIP.
    $expectedSHA256 = '424798c8f16ccef1ae343f0a6d7ea7ddda8cb7f612b91f23a2f846274c21e524'
    $hashAlgorithm = [Security.Cryptography.SHA256]::Create()
    $archiveStream = [IO.File]::OpenRead($archive)
    try {
        $actualSHA256 = [BitConverter]::ToString($hashAlgorithm.ComputeHash($archiveStream)).Replace('-', '')
    } finally {
        $archiveStream.Dispose()
        $hashAlgorithm.Dispose()
    }
    if ($actualSHA256 -ne $expectedSHA256) {
        throw 'Release checksum mismatch'
    }
    $unpacked = Join-Path $deliveryRoot 'tool'
    [Reflection.Assembly]::LoadWithPartialName('System.IO.Compression.FileSystem') | Out-Null
    [IO.Compression.ZipFile]::ExtractToDirectory($archive, $unpacked)
    $reviewExecutable = Join-Path $unpacked 'privacy-guard.exe'
    $reviewArguments = @($Mode, '--repo', $reviewRoot)
    if ($Mode -eq 'files') { $reviewArguments += @('--paths') + @($Paths) + @('--source', $Source) }
    if ($Mode -eq 'push') { $reviewArguments += @('--push-range', $Tip, $Base) }
    # Prevent single-file extraction and scanner intermediates from entering the review target.
    $previousTemp = $env:TEMP
    $previousTmp = $env:TMP
    try {
        $env:TEMP = $temporaryRoot
        $env:TMP = $temporaryRoot
        & $reviewExecutable @reviewArguments
        $reviewExitCode = $LASTEXITCODE
    } finally {
        $env:TEMP = $previousTemp
        $env:TMP = $previousTmp
    }
    $global:LASTEXITCODE = $reviewExitCode
} catch {
    # Never echo arguments, paths, network diagnostics or arbitrary exception content.
    '{"mode":"advisory","review_complete":false,"findings":[],"errors":["Download or review launcher incomplete; details suppressed"]}'
    $global:LASTEXITCODE = 1
}
