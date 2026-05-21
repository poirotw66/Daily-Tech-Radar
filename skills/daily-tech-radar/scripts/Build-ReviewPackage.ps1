param(
    [Parameter(Mandatory=$true)][string]$InputJson,
    [Parameter(Mandatory=$true)][string]$Output
)

function ConvertTo-Slug([string]$Text) {
    $slug = $Text.ToLower() -replace "[^a-z0-9\u4e00-\u9fff]+", "-"
    $slug = $slug -replace "-+", "-"
    $slug = $slug.Trim("-")
    if (-not $slug) { return "daily-tech-radar" }
    if ($slug.Length -gt 80) { return $slug.Substring(0, 80) }
    return $slug
}

function Format-Sources($Sources) {
    if (-not $Sources -or $Sources.Count -eq 0) { return "- No sources provided." }
    $lines = @()
    $i = 1
    foreach ($source in $Sources) {
        $lines += "$i. [$($source.title)]($($source.url)) - $($source.publisher), trust: $($source.trust_level)"
        $i++
    }
    return ($lines -join "`n")
}

function Format-Issues($Issues) {
    if (-not $Issues -or $Issues.Count -eq 0) { return "- No issues reported." }
    $lines = @()
    foreach ($issue in $Issues) {
        $severity = if ($issue.severity) { $issue.severity } else { "unknown" }
        $problem = if ($issue.problem) { $issue.problem } elseif ($issue.text) { $issue.text } else { ($issue | ConvertTo-Json -Compress) }
        $fix = if ($issue.suggested_fix) { " Suggested fix: $($issue.suggested_fix)" } else { "" }
        $lines += "- [$severity] $problem$fix"
    }
    return ($lines -join "`n")
}

function Format-ClaimTable($Rows) {
    $lines = @("| Claim | Source | Status | Note |", "|---|---|---|---|")
    if (-not $Rows -or $Rows.Count -eq 0) {
        $lines += "| 未提供 | 需要補來源 | needs_review | 請人工確認 |"
        return ($lines -join "`n")
    }
    foreach ($row in $Rows) {
        $claim = "$($row.claim)" -replace "\|", "/"
        $source = "$($row.source)" -replace "\|", "/"
        $status = "$($row.status)" -replace "\|", "/"
        $note = "$($row.note)" -replace "\|", "/"
        $lines += "| $claim | $source | $status | $note |"
    }
    return ($lines -join "`n")
}

$data = Get-Content -Raw -Encoding UTF8 -LiteralPath $InputJson | ConvertFrom-Json
$fact = $data.fact_check
$dist = $data.distribution
$seo = $data.seo
$confirmations = @($data.user_confirmation_needed)
if ($confirmations.Count -eq 0) {
    $confirmations = @(
        "是否加入個人使用經驗或案例？",
        "是否有任何公司、客戶或工作內容需要刪除？",
        "是否同意目前選題與發布角度？"
    )
}
$confirmationText = (($confirmations | ForEach-Object { "- $_" }) -join "`n")
$tags = if ($seo.tags) { ($seo.tags -join ", ") } else { "AI Engineering, DevTools" }
$slug = if ($seo.slug) { $seo.slug } else { ConvertTo-Slug $data.topic }

$lines = @(
    "# 今日技術文章審稿包",
    "",
    "## 1. 今日主題",
    "$($data.topic)",
    "",
    "## 2. 為什麼選這題",
    "$($data.selection_reason)",
    "",
    "## 3. 來源清單",
    "$(Format-Sources $data.sources)",
    "",
    "## 4. 文章草稿",
    "$($data.article_markdown)",
    "",
    "## 5. 事實檢查結果",
    "Status: ``$($fact.status)``",
    "",
    "$(Format-Issues $fact.issues)",
    "",
    "### Claim-Source Table",
    "$(Format-ClaimTable $fact.claim_source_table)",
    "",
    "## 6. 需要你特別確認的地方",
    "$confirmationText",
    "",
    "## 7. LinkedIn 貼文",
    "$($dist.linkedin)",
    "",
    "## 8. Threads 貼文",
    "$($dist.threads)",
    "",
    "## 9. Facebook 社團貼文",
    "$($dist.facebook)",
    "",
    "## 10. Newsletter 摘要",
    "$($dist.newsletter)",
    "",
    "## 11. SEO Metadata",
    "- Title: $($seo.title)",
    "- Description: $($seo.description)",
    "- Slug: $slug",
    "- Tags: $tags",
    "",
    "## 12. 建議發布標籤",
    "$tags",
    "",
    "## 13. 發布前 Checklist",
    "- [ ] 主要事實都有來源",
    "- [ ] 推論與個人判斷已清楚標示",
    "- [ ] 沒有公司內部資訊或客戶資料",
    "- [ ] 金融/企業情境已加入資料、權限、治理或合規限制",
    "- [ ] 已補上必要的個人觀點",
    "- [ ] 已確認是否發布到網站與社群"
)
$markdown = $lines -join "`n"

$target = $Output
if ((Test-Path -LiteralPath $Output -PathType Container) -or -not ([IO.Path]::GetExtension($Output))) {
    New-Item -ItemType Directory -Force -Path $Output | Out-Null
    $target = Join-Path $Output ("{0}-{1}.md" -f (Get-Date -Format "yyyy-MM-dd"), $slug)
}

$parent = Split-Path -Parent $target
if ($parent) { New-Item -ItemType Directory -Force -Path $parent | Out-Null }
Set-Content -LiteralPath $target -Value $markdown -Encoding UTF8
Write-Output $target


