param(
    [Parameter(Mandatory=$true)][string]$Candidates,
    [string]$Scoring,
    [string]$Output
)

$weights = @{
    relevance = 0.25
    timeliness = 0.15
    practicality = 0.20
    differentiation = 0.20
    business_value = 0.10
    source_quality = 0.10
}

if ($Scoring -and (Test-Path -LiteralPath $Scoring)) {
    $inWeights = $false
    Get-Content -LiteralPath $Scoring -Encoding UTF8 | ForEach-Object {
        $line = $_
        if ($line.Trim() -eq "weights:") {
            $inWeights = $true
            return
        }
        if ($inWeights -and $line -and -not $line.StartsWith(" ")) {
            $inWeights = $false
        }
        if ($inWeights -and $line.Trim() -match "^([^:]+):\s*([0-9.]+)") {
            $weights[$matches[1].Trim()] = [double]$matches[2]
        }
    }
}

$parsed = Get-Content -Raw -Encoding UTF8 -LiteralPath $Candidates | ConvertFrom-Json
if ($parsed -is [System.Array]) {
    $items = @($parsed)
} elseif ($parsed.PSObject.Properties.Name -contains "candidates") {
    $items = @($parsed.candidates)
} else {
    $items = @($parsed)
}

$scored = foreach ($item in $items) {
    if ($null -eq $item) { continue }
    $weighted = 0.0
    foreach ($key in $weights.Keys) {
        if ($null -ne $item.scores.$key) {
            $weighted += ([double]$item.scores.$key) * ([double]$weights[$key])
        }
    }
    $item | Add-Member -NotePropertyName weighted_score -NotePropertyValue ([math]::Round($weighted, 3)) -Force
    $item
}

$scored = @($scored | Sort-Object -Property weighted_score -Descending)
$payload = [ordered]@{
    selected_candidate_id = if ($scored.Count -gt 0) { $scored[0].candidate_id } else { $null }
    score_table = $scored
    selection_reason = "Selected by weighted score. Review qualitative fit before drafting."
}

$json = $payload | ConvertTo-Json -Depth 20
if ($Output) {
    $parent = Split-Path -Parent $Output
    if ($parent) { New-Item -ItemType Directory -Force -Path $parent | Out-Null }
    Set-Content -LiteralPath $Output -Value $json -Encoding UTF8
} else {
    $json
}


