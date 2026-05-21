param(
    [Parameter(Mandatory=$true, ValueFromRemainingArguments=$true)]
    [string[]]$Arguments
)

$python = Join-Path $env:LocalAppData "Programs\PythonPortable\Python313\python.exe"
if (-not (Test-Path -LiteralPath $python)) {
    $cmd = Get-Command python -ErrorAction SilentlyContinue
    if ($cmd) {
        $python = $cmd.Source
    } else {
        throw "Python runtime not found. Expected $python or python on PATH."
    }
}

& $python @Arguments
exit $LASTEXITCODE

