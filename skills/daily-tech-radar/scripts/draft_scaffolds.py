"""Article scaffold templates keyed by content_angle."""

from __future__ import annotations


def resolve_angle(candidate: dict, sources: list[dict]) -> str:
    angle = str(candidate.get("content_angle") or "practical_guide").strip()
    title = str(candidate.get("title", "")).lower()
    tags = " ".join(str(t) for s in sources for t in (s.get("tags") or [])).lower()
    blob = f"{title} {tags}"
    if angle == "workflow_case" and any(k in blob for k in ("casb", "compliance", "security", "governance", "zero trust")):
        return "enterprise_governance"
    return angle


def subtitle_for_angle(angle: str) -> str:
    return {
        "enterprise_governance": "企業 AI 可見度、合規與政策閉環",
        "workflow_case": "工程與自動化 workflow 的落地觀察",
        "technical_explainer": "技術變化與工程意義",
        "tool_review": "開源工具與 DevTools 實用性",
        "practical_guide": "對 builder 與 PM 的實務啟發",
        "opinion": "趨勢判斷與取捨",
        "weekly_digest": "本週技術重點整理",
    }.get(angle, "今日技術觀察")


def tldr_for_angle(angle: str, publisher: str, published_at: str, title: str) -> list[str]:
    base = [
        f"{publisher} 在 {published_at} 發布了與「{title}」相關的更新。",
    ]
    extras_by_angle = {
        "enterprise_governance": [
            "重點在可見度、audit trail、DLP／政策銜接，而非產品口號。",
            "正式導入前需釐清合約範圍、資料讀取與內部責任分工。",
        ],
        "workflow_case": [
            "重點在 workflow 邊界、human-in-the-loop 與工具權限。",
            "適合先從低風險流程試行，再擴到 production 相關路徑。",
        ],
        "technical_explainer": [
            "重點在技術機制是否改變工程實作方式。",
            "需對照官方文件確認細節，避免只靠標題推論。",
        ],
        "tool_review": [
            "重點在 repo／工具是否解決真問題，而非 star 數。",
            "評估維護度、授權、與你現有 toolchain 的整合成本。",
        ],
        "practical_guide": [
            "重點在誰該現在投入、誰可以觀望。",
            "建議搭配小規模實驗驗證假設。",
        ],
        "opinion": [
            "以下含作者判斷，事實與詮釋已分開標示。",
        ],
    }
    return base + extras_by_angle.get(angle, extras_by_angle["practical_guide"])


def why_notable_for_angle(angle: str) -> str:
    return {
        "enterprise_governance": (
            "真正值得注意的不是「又多一個整合」，而是核准使用的 AI／SaaS 能否納入既有資安營運"
            "（CASB、DLP、Gateway、Access），而不是留在影子 IT。"
        ),
        "workflow_case": (
            "真正值得注意的不是 Agent 會不會寫 code，而是權限、紀錄與審核節點能否設計好。"
        ),
        "technical_explainer": (
            "真正值得注意的不是新名詞，而是底層機制是否改變你們的架構或成本結構。"
        ),
        "tool_review": (
            "真正值得注意的不是 GitHub 熱度，而是團隊能不能在一週內驗證有用性。"
        ),
        "practical_guide": (
            "真正值得注意的不是新聞本身，而是對你的產品或交付節奏有沒有具體影響。"
        ),
        "opinion": (
            "真正值得注意的不是單一事件，而是它是否改變你對趨勢的優先順序。"
        ),
    }.get(angle, why_notable_for_angle("practical_guide"))


def application_for_angle(angle: str) -> str:
    return {
        "enterprise_governance": """### 資安與 IT
1. 盤點已核准的 AI／SaaS 與資料分類。
2. 對照公告中的監控範圍與內部必記錄事件。
3. 定義發現 → 政策（Gateway／IAM）的 runbook。

### 工程與 Agent
- 僅允許走 Enterprise／已監控實例；MCP 與工具權限與 CASB 敘述分開評估。""",
        "tool_review": """1. Fork 或本地跑一個最小場景（30–60 分鐘）。
2. 檢查 license、issue 活躍度、與現有 CI 的整合點。
3. 決定是採用、觀望或僅追蹤 release。""",
        "technical_explainer": """1. 畫一張「之前／之後」資料流或責任邊界圖。
2. 列出要改的元件與回滾方式。
3. 用一個非 production 環境驗證關鍵假設。""",
    }.get(
        angle,
        """對小團隊可先從低風險場景試行：文件摘要、內部 FAQ、工程支援 triage。
若進企業場景，先回答：誰能看哪些資料、每一步能否追蹤、誰負責批准。""",
    )


def judgment_for_angle(angle: str) -> str:
    return {
        "enterprise_governance": (
            "我會把它看成企業 AI 治理「可接線」變成熟的訊號；短期先把核准工具納入可見與可政策化，"
            "再談擴大 Agent 權限。"
        ),
        "tool_review": (
            "我會先把它當「值得花半天試用」的候選，而不是「必須上線」；star 數只當參考。"
        ),
        "technical_explainer": (
            "我會等到團隊能說清楚「改哪一層、不回滾風險」再對外寫深度文。"
        ),
    }.get(
        angle,
        "我會先標記為值得追蹤，但發布前仍要對照一級來源與你方場域限制。",
    )
