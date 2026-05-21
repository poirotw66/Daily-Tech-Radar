param(
    [string]$RunDate = (Get-Date -Format "yyyy-MM-dd"),
    [int]$RssLimit = 5,
    [int]$ArxivLimit = 8,
    [int]$GithubLimit = 8,
    [int]$GithubDays = 30,
    [int]$GithubMinStars = 100,
    [switch]$InsecureSkipTlsVerify,
    [switch]$PrepareAgentRefinement,
    [switch]$IncludeArxiv
)

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$skillDir = Split-Path -Parent $scriptDir
$runPython = Join-Path $scriptDir "Run-Python.ps1"
$sourceDir = Join-Path $skillDir "data\sources"
$normalizedDir = Join-Path $skillDir "data\normalized"
$briefDir = Join-Path $skillDir "output\source_briefs"
$candidateDir = Join-Path $skillDir "output\candidates"
$draftDir = Join-Path $skillDir "output\drafts"
$reviewPackageDir = Join-Path $skillDir "output\review_packages"
$refinementDir = Join-Path $skillDir "output\refinements"
$healthDir = Join-Path $skillDir "output\source_health"
$logDir = Join-Path $skillDir "output\logs"
$memoryDir = Join-Path $skillDir "memory"
$rssConfig = Join-Path $skillDir "config\rss_sources.yaml"
$scoringConfig = Join-Path $skillDir "config\scoring.yaml"

New-Item -ItemType Directory -Force -Path $sourceDir,$normalizedDir,$briefDir,$candidateDir,$draftDir,$reviewPackageDir,$refinementDir,$healthDir,$logDir,$memoryDir | Out-Null

$tlsFlag = @()
if ($InsecureSkipTlsVerify) {
    $tlsFlag = @("--insecure-skip-tls-verify")
}

$rssOutput = Join-Path $sourceDir "$RunDate-rss.json"
$arxivOutput = Join-Path $sourceDir "$RunDate-arxiv.json"
$githubOutput = Join-Path $sourceDir "$RunDate-github.json"
$rawOutput = Join-Path $sourceDir "$RunDate-raw.json"
$normalizedOutput = Join-Path $normalizedDir "$RunDate-normalized.json"
$briefOutput = Join-Path $briefDir "$RunDate-source-brief.md"
$candidatesOutput = Join-Path $candidateDir "$RunDate-candidates.json"
$scoresOutput = Join-Path $candidateDir "$RunDate-scores.json"
$topicBriefOutput = Join-Path $candidateDir "$RunDate-topic-selection-brief.md"
$draftOutputDir = Join-Path $draftDir $RunDate
$refinementOutputDir = Join-Path $refinementDir $RunDate
$topicMemoryOutput = Join-Path $memoryDir "topic_memory.json"
$sourceHealthOutput = Join-Path $healthDir "$RunDate-source-health.md"
$logOutput = Join-Path $logDir "$RunDate-daily-run.json"

$rssArgs = @(
    (Join-Path $scriptDir "fetch_rss_from_config.py"),
    "--config",
    $rssConfig,
    "--limit",
    "$RssLimit"
)
$rssArgs += $tlsFlag
$rssArgs += @("--output", $rssOutput)

$arxivArgs = @(
    (Join-Path $scriptDir "fetch_arxiv.py"),
    "--category", "cs.AI",
    "--category", "cs.CL",
    "--category", "cs.LG",
    "--max-results", "$ArxivLimit"
) + $tlsFlag + @("--output", $arxivOutput)

$githubArgs = @(
    (Join-Path $scriptDir "fetch_github_repos.py"),
    "--days", "$GithubDays",
    "--min-stars", "$GithubMinStars",
    "--per-page", "$GithubLimit"
) + $tlsFlag + @("--output", $githubOutput)

$steps = @()

function Invoke-Step {
    param(
        [string]$Name,
        [string[]]$Arguments,
        [string]$FallbackOutput
    )

    $started = Get-Date
    Write-Host "[$($started.ToString('HH:mm:ss'))] $Name"
    & $runPython @Arguments
    $ended = Get-Date
    $status = "ok"
    if ($LASTEXITCODE -ne 0) {
        if ($FallbackOutput) {
            "[]" | Set-Content -Encoding UTF8 -LiteralPath $FallbackOutput
            $status = "failed_with_empty_fallback"
            Write-Warning "$Name failed with exit code $LASTEXITCODE. Wrote empty fallback: $FallbackOutput"
        } else {
            throw "$Name failed with exit code $LASTEXITCODE"
        }
    }
    $script:steps += [ordered]@{
        name = $Name
        status = $status
        started_at = $started.ToString("o")
        ended_at = $ended.ToString("o")
        seconds = [math]::Round(($ended - $started).TotalSeconds, 2)
    }
}

Invoke-Step -Name "Fetch RSS" -Arguments $rssArgs -FallbackOutput $rssOutput
if ($IncludeArxiv) {
    Invoke-Step -Name "Fetch arXiv" -Arguments $arxivArgs -FallbackOutput $arxivOutput
} else {
    "[]" | Set-Content -Encoding UTF8 -LiteralPath $arxivOutput
    $now = Get-Date
    $steps += [ordered]@{
        name = "Fetch arXiv"
        status = "skipped_optional_source"
        started_at = $now.ToString("o")
        ended_at = $now.ToString("o")
        seconds = 0
    }
    Write-Host "[$($now.ToString('HH:mm:ss'))] Fetch arXiv skipped. Use -IncludeArxiv to enable it."
}
Invoke-Step -Name "Fetch GitHub repos" -Arguments $githubArgs -FallbackOutput $githubOutput

Invoke-Step -Name "Merge sources" -Arguments @(
    (Join-Path $scriptDir "merge_sources.py"),
    $rssOutput,
    $arxivOutput,
    $githubOutput,
    "--output",
    $rawOutput
)

Invoke-Step -Name "Normalize sources" -Arguments @(
    (Join-Path $scriptDir "normalize_sources.py"),
    $rawOutput,
    "--output",
    $normalizedOutput
)

Invoke-Step -Name "Build source brief" -Arguments @(
    (Join-Path $scriptDir "build_source_brief.py"),
    $normalizedOutput,
    "--run-date",
    $RunDate,
    "--output",
    $briefOutput
)

Invoke-Step -Name "Generate topic candidates" -Arguments @(
    (Join-Path $scriptDir "generate_candidates_from_sources.py"),
    $normalizedOutput,
    "--limit",
    "5",
    "--topic-memory",
    $topicMemoryOutput,
    "--output",
    $candidatesOutput
)

Invoke-Step -Name "Score topic candidates" -Arguments @(
    (Join-Path $scriptDir "score_topics.py"),
    $candidatesOutput,
    "--scoring",
    $scoringConfig,
    "--output",
    $scoresOutput
)

Invoke-Step -Name "Build topic selection brief" -Arguments @(
    (Join-Path $scriptDir "build_topic_selection_brief.py"),
    $scoresOutput,
    "--sources",
    $normalizedOutput,
    "--output",
    $topicBriefOutput
)

Invoke-Step -Name "Update topic memory" -Arguments @(
    (Join-Path $scriptDir "update_topic_memory.py"),
    "--scores",
    $scoresOutput,
    "--memory",
    $topicMemoryOutput,
    "--run-date",
    $RunDate
)

Invoke-Step -Name "Build Traditional Chinese draft package" -Arguments @(
    (Join-Path $scriptDir "build_draft_package.py"),
    "--candidates",
    $candidatesOutput,
    "--scores",
    $scoresOutput,
    "--sources",
    $normalizedOutput,
    "--run-date",
    $RunDate,
    "--output-dir",
    $draftOutputDir
)

$reviewPackageJson = Get-ChildItem -LiteralPath $draftOutputDir -Filter "*-review-package.json" | Sort-Object LastWriteTime -Descending | Select-Object -First 1
if ($reviewPackageJson) {
    Invoke-Step -Name "Build Markdown review package" -Arguments @(
        (Join-Path $scriptDir "build_review_package.py"),
        $reviewPackageJson.FullName,
        "--output",
        $reviewPackageDir
    )

    if ($PrepareAgentRefinement) {
        Invoke-Step -Name "Prepare IDE agent refinement task" -Arguments @(
            (Join-Path $scriptDir "prepare_agent_refinement.py"),
            "--review-package-json",
            $reviewPackageJson.FullName,
            "--prompt",
            (Join-Path $skillDir "prompts\refine_review_package.md"),
            "--output-dir",
            $refinementOutputDir
        )
    }
}

$rawCount = @((Get-Content -Raw -Encoding UTF8 -LiteralPath $rawOutput | ConvertFrom-Json)).Count
$normalizedCount = @((Get-Content -Raw -Encoding UTF8 -LiteralPath $normalizedOutput | ConvertFrom-Json)).Count

$log = [ordered]@{
    run_date = $RunDate
    insecure_skip_tls_verify = [bool]$InsecureSkipTlsVerify
    include_arxiv = [bool]$IncludeArxiv
    outputs = [ordered]@{
        rss = $rssOutput
        arxiv = $arxivOutput
        github = $githubOutput
        raw = $rawOutput
        normalized = $normalizedOutput
        source_brief = $briefOutput
        candidates = $candidatesOutput
        scores = $scoresOutput
        topic_selection_brief = $topicBriefOutput
        draft_dir = $draftOutputDir
        review_packages_dir = $reviewPackageDir
        refinement_dir = $refinementOutputDir
        topic_memory = $topicMemoryOutput
        source_health = $sourceHealthOutput
    }
    counts = [ordered]@{
        raw = $rawCount
        normalized = $normalizedCount
    }
    steps = $steps
}

$log | ConvertTo-Json -Depth 20 | Set-Content -Encoding UTF8 -LiteralPath $logOutput

Invoke-Step -Name "Build source health report" -Arguments @(
    (Join-Path $scriptDir "build_source_health_report.py"),
    "--logs-dir",
    $logDir,
    "--limit",
    "30",
    "--output",
    $sourceHealthOutput
)
$log.steps = $steps
$log | ConvertTo-Json -Depth 20 | Set-Content -Encoding UTF8 -LiteralPath $logOutput

Write-Host ""
Write-Host "Daily Tech Radar source run complete."
Write-Host "Raw sources: $rawCount"
Write-Host "Normalized sources: $normalizedCount"
Write-Host "Source brief: $briefOutput"
Write-Host "Topic selection brief: $topicBriefOutput"
Write-Host "Draft dir: $draftOutputDir"
Write-Host "Review packages dir: $reviewPackageDir"
Write-Host "Topic memory: $topicMemoryOutput"
Write-Host "Source health: $sourceHealthOutput"
if ($PrepareAgentRefinement) {
    Write-Host "Refinement dir: $refinementOutputDir"
}
Write-Host "Next: review the Markdown package or ask the IDE agent to execute the generated refinement task."

