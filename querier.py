import time

import httpx
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

API_URL = "https://gis.uro.taipei/ashx/Get_updcase_list.ashx"
HEADERS = {
    "Referer": "https://gis.uro.taipei/r_progress.aspx",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Content-Type": "application/x-www-form-urlencoded",
}
CACHE_TTL = 3600  # 1 hour

INACTIVE_STATUSES = {"已完工", "已失效", "已駁回", "自行撤回", "完成成果備查", "已核定", "已核准", "已公告"}

_cache: dict[str, tuple[list, float]] = {}
_client: httpx.AsyncClient | None = None


def get_client() -> httpx.AsyncClient:
    global _client
    if _client is None or _client.is_closed:
        _client = httpx.AsyncClient(verify=False, timeout=10)
    return _client


async def query_by_address(address: str) -> list[dict]:
    now = time.monotonic()
    if address in _cache:
        result, ts = _cache[address]
        if now - ts < CACHE_TTL:
            return result

    resp = await get_client().post(API_URL, data=f"qitem=qAddr&road={address}", headers=HEADERS)
    resp.raise_for_status()
    text = resp.text.strip()
    result = [] if not text or text in ("[]", "") else resp.json()

    _cache[address] = (result, now)
    return result


def split_cases(cases: list[dict]) -> tuple[list[dict], list[dict]]:
    active = [c for c in cases if c.get("schedule") not in INACTIVE_STATUSES]
    historical = [c for c in cases if c.get("schedule") in INACTIVE_STATUSES]
    return active, historical
