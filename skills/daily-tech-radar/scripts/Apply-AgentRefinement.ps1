param(
    [Parameter(Mandatory=$true)][string]$TaskFile,
    [string]$OutputFile
)

if (-not (Test-Path -LiteralPath $TaskFile)) {
    throw "Task file not found: $TaskFile"
}

$task = Get-Content -Raw -Encoding UTF8 -LiteralPath $TaskFile

if (-not $OutputFile) {
    if ($task -match "write the final Markdown review package to:\s*```text\s*(.*?)\s*```") {
        $OutputFile = $matches[1].Trim()
    } else {
        throw "Could not infer output file from task. Provide -OutputFile."
    }
}

Write-Output "This task is intended for the IDE agent to execute."
Write-Output "Task file: $TaskFile"
Write-Output "Expected output: $OutputFile"
Write-Output ""
Write-Output "Open the task file and ask the IDE agent:"
Write-Output "依照這份 task file 執行 refinement，並把結果寫到指定 output path。"

