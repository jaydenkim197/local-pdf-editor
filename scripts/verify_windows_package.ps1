# GitHub Windows runner check; requires PowerShell 7 and installed local Tesseract.
param(
    [string]$Package = 'dist/LocalPdfUtilities',
    [string]$Fixture = 'tests/fixtures/sample.heic',
    [string]$Reports = 'reports'
)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
if (-not $IsWindows) { throw 'Run this check on Windows.' }
$packageRoot = (Resolve-Path -LiteralPath $Package).Path
$fixturePath = (Resolve-Path -LiteralPath $Fixture).Path
$reportRoot = (New-Item -ItemType Directory -Path $Reports -Force).FullName
$engine = Join-Path $env:ProgramFiles 'Tesseract-OCR/tesseract.exe'
if (-not (Test-Path -LiteralPath $engine)) { throw 'Install Tesseract 5 with eng/kor data first.' }
$temporaryRoot = Join-Path ([IO.Path]::GetTempPath()) ('PDF 실행 확인 ' + [guid]::NewGuid())
$isolated = Join-Path $temporaryRoot 'LocalPdfUtilities'
$rules = @()
$profiles = @()
$saved = @{}
$names = @('PATH', 'PYTHONPATH', 'PYTHONHOME', 'QT_PLUGIN_PATH', 'QML2_IMPORT_PATH',
           'QT_QPA_PLATFORM', 'QT_SCALE_FACTOR', 'TESSDATA_PREFIX')
foreach ($name in $names) { $saved[$name] = [Environment]::GetEnvironmentVariable($name, 'Process') }
try {
    New-Item -ItemType Directory -Path $temporaryRoot | Out-Null
    Copy-Item -LiteralPath $packageRoot -Destination $isolated -Recurse
    $inputFile = Join-Path $temporaryRoot '입력 그림.heic'
    Copy-Item -LiteralPath $fixturePath -Destination $inputFile
    $executable = Join-Path $isolated 'LocalPdfUtilities.exe'
    foreach ($name in $names) { [Environment]::SetEnvironmentVariable($name, $null, 'Process') }
    $env:PATH = "$env:SystemRoot\System32;$env:SystemRoot;$(Split-Path $engine)"
    $profiles = @(Get-NetFirewallProfile | Select-Object Name, Enabled)
    Set-NetFirewallProfile -Profile Domain,Private,Public -Enabled True
    foreach ($program in @($executable, $engine)) {
        $rule = 'LocalPdfUtilities-test-' + [guid]::NewGuid()
        New-NetFirewallRule -Name $rule -DisplayName $rule -Direction Outbound -Program $program -Action Block -Profile Any | Out-Null
        $rules += $rule
    }
    foreach ($scale in @('1', '1.5')) {
        $env:QT_SCALE_FACTOR = $scale
        $report = Join-Path $reportRoot "windows-package-$scale.json"
        $arguments = @('--smoke-test', '--heic-fixture', ('"' + $inputFile + '"'),
                       '--ocr-smoke', '--korean-ocr-smoke', '--smoke-report', ('"' + $report + '"'))
        $process = Start-Process -FilePath $executable -ArgumentList $arguments -WorkingDirectory $isolated -PassThru
        if (-not $process.WaitForExit(180000)) {
            $process.Kill($true)
            throw "Isolated package timed out at scale $scale."
        }
        $process.Refresh()
        if (-not (Test-Path -LiteralPath $report)) { throw 'Frozen executable did not write smoke evidence.' }
        $evidence = Get-Content -LiteralPath $report -Raw | ConvertFrom-Json
        if ($process.ExitCode -ne 0 -or -not $evidence.passed) {
            $detail = $evidence.error -replace '%', '%25' -replace "`r", '%0D' -replace "`n", '%0A'
            Write-Output "::error title=Windows frozen smoke::$detail"
            throw "Frozen smoke failed at scale $scale with exit $($process.ExitCode)."
        }
        if (-not $evidence.frozen -or $evidence.qt_backend -ne 'windows') {
            throw 'The check did not exercise the frozen native Windows Qt backend.'
        }
        "Windows frozen native smoke passed at scale $scale with outbound blocked and Python removed from PATH; HEIC, AES/forms/redaction, PDF-A/HTML and English/Korean OCR checked." |
            Out-File -FilePath $env:GITHUB_STEP_SUMMARY -Encoding utf8 -Append
        Write-Output "::notice title=Windows frozen verification::Native Windows backend, scale $scale, Unicode relocated package, Python-free PATH, outbound blocked, English/Korean OCR passed."
    }
} finally {
    foreach ($rule in $rules) { Remove-NetFirewallRule -Name $rule -ErrorAction Continue }
    foreach ($profile in $profiles) { Set-NetFirewallProfile -Profile $profile.Name -Enabled $profile.Enabled -ErrorAction Continue }
    foreach ($name in $names) { [Environment]::SetEnvironmentVariable($name, $saved[$name], 'Process') }
    if (Test-Path -LiteralPath $temporaryRoot) { Remove-Item -LiteralPath $temporaryRoot -Recurse -Force -ErrorAction Continue }
}
