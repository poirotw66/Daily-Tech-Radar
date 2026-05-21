param(
    [Parameter(Mandatory=$true)][string]$Package
)

$required = @(
    "## 1. 今日主題",
    "## 2. 為什麼選這題",
    "## 3. 來源清單",
    "## 4. 文章草稿",
    "## 5. 事實檢查結果",
    "## 6. 需要你特別確認的地方",
    "## 7. LinkedIn 貼文",
    "## 8. Threads 貼文",
    "## 9. Facebook 社團貼文",
    "## 10. Newsletter 摘要",
    "## 11. SEO Metadata",
    "## 12. 建議發布標籤",
    "## 13. 發布前 Checklist"
)

$text = Get-Content -Raw -Encoding UTF8 -LiteralPath $Package
$missing = @($required | Where-Object { $text -notlike "*$_*" })

if ($missing.Count -gt 0) {
    Write-Output "Missing sections:"
    $missing | ForEach-Object { Write-Output "- $_" }
    exit 1
}

Write-Output "Review package structure looks good."


