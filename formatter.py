BASE_URL = "https://gis.uro.taipei/"

STATUS_EMOJI = {
    "審查中": "🔴",
    "已受理": "🟠",
    "補件中": "🟡",
    "核准": "🟢",
    "已核准": "🟢",
    "已公告": "🔵",
    "已核定": "✅",
    "已完工": "🏗️",
    "完成成果備查": "📦",
    "已失效": "⚫",
    "已駁回": "❌",
    "自行撤回": "↩️",
}

MAX_CASE_NAME = 35


def _status_icon(status: str) -> str:
    return STATUS_EMOJI.get(status, "📋")


def _shorten(name: str) -> str:
    return name[:MAX_CASE_NAME] + "…" if len(name) > MAX_CASE_NAME else name


def format_results(address: str, active: list[dict], historical: list[dict]) -> str:
    total = len(active) + len(historical)
    lines = [f"📍 *查詢地址：{address}*", f"共找到 {total} 筆相關案件", ""]

    if not active and not historical:
        lines.append("✅ 查無都更相關案件")
        return "\n".join(lines)

    if active:
        lines.append(f"🔴 *進行中案件（{len(active)} 筆）*")
        for c in active:
            icon = _status_icon(c["schedule"])
            lines.append(f"{icon} {c['schedule']} ｜ {_shorten(c['case_name'])}")
            lines.append(f"   案號：`{c['case_id']}`")
            lines.append(f"   [查看詳情]({BASE_URL}{c['details']})")
            lines.append("")

    if historical:
        lines.append(f"📋 *歷史案件（{len(historical)} 筆）*")
        for c in historical[:5]:
            icon = _status_icon(c["schedule"])
            lines.append(f"{icon} {c['schedule']} ｜ {_shorten(c['case_name'])}")
        if len(historical) > 5:
            lines.append(f"   … 另有 {len(historical) - 5} 筆已結案")

    return "\n".join(lines)


def format_no_result(address: str) -> str:
    return f"📍 查詢地址：{address}\n\n✅ 目前查無都更相關案件\n（資料來源：臺北市都市更新審議服務平台）"


def format_error() -> str:
    return "❌ 查詢失敗，請稍後再試，或確認地址格式是否正確。"
