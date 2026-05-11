import urllib3
import requests

# gis.uro.taipei has a misconfigured SSL cert (missing Subject Key Identifier)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

API_URL = "https://gis.uro.taipei/ashx/Get_updcase_list.ashx"
HEADERS = {
    "Referer": "https://gis.uro.taipei/r_progress.aspx",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Content-Type": "application/x-www-form-urlencoded",
}

INACTIVE_STATUSES = {"已完工", "已失效", "已駁回", "自行撤回", "完成成果備查", "已核定", "已核准", "已公告"}


def query_by_address(address: str) -> list[dict]:
    resp = requests.post(
        API_URL,
        data=f"qitem=qAddr&road={address}",
        headers=HEADERS,
        timeout=10,
        verify=False,
    )
    resp.raise_for_status()
    text = resp.text.strip()
    if not text or text in ("[]", ""):
        return []
    return resp.json()


def split_cases(cases: list[dict]) -> tuple[list[dict], list[dict]]:
    active = [c for c in cases if c.get("schedule") not in INACTIVE_STATUSES]
    historical = [c for c in cases if c.get("schedule") in INACTIVE_STATUSES]
    return active, historical
