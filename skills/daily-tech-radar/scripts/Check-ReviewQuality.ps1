param(
    [Parameter(Mandatory=$true)][string]$Package
)

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$runPython = Join-Path $scriptDir "Run-Python.ps1"
& $runPython (Join-Path $scriptDir "check_review_quality.py") $Package
exit $LASTEXITCODE

