param(
    [string]$RefinementRoot,
    [switch]$ShowPrompt
)

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$skillDir = Split-Path -Parent $scriptDir
if (-not $RefinementRoot) {
    $RefinementRoot = Join-Path $skillDir "output\refinements"
}

if (-not (Test-Path -LiteralPath $RefinementRoot)) {
    throw "Refinement directory not found: $RefinementRoot"
}

$task = Get-ChildItem -LiteralPath $RefinementRoot -Recurse -File -Filter "*-agent-refinement-task.md" |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 1

if (-not $task) {
    throw "No agent refinement task found under: $RefinementRoot"
}

$metadata = Get-ChildItem -LiteralPath $task.DirectoryName -File -Filter "*-agent-refinement-metadata.json" |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 1

$outputPath = $null
if ($metadata) {
    $meta = Get-Content -Raw -Encoding UTF8 -LiteralPath $metadata.FullName | ConvertFrom-Json
    $outputPath = $meta.output_path
}

Write-Output "Latest refinement task:"
Write-Output $task.FullName
if ($outputPath) {
    Write-Output ""
    Write-Output "Expected output:"
    Write-Output $outputPath
}
Write-Output ""
Write-Output "Ask the IDE agent:"
Write-Output "Run the refinement task and write the refined review package to the metadata output_path."

if ($ShowPrompt) {
    Write-Output ""
    Write-Output "----- TASK CONTENT -----"
    Get-Content -Raw -Encoding UTF8 -LiteralPath $task.FullName
}

