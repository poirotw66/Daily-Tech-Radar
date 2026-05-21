param(
    [int]$KeepDays = 14,
    [switch]$DryRun
)

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$skillDir = Split-Path -Parent $scriptDir
$runPython = Join-Path $scriptDir "Run-Python.ps1"

$argsList = @(
    (Join-Path $scriptDir "cleanup_outputs.py"),
    "--skill-dir",
    $skillDir,
    "--keep-days",
    "$KeepDays"
)
if ($DryRun) {
    $argsList += "--dry-run"
}

& $runPython @argsList
exit $LASTEXITCODE
