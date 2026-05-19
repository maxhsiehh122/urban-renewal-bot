import re

from linebot.v3 import WebhookParser
from linebot.v3.messaging import (
    AsyncApiClient,
    AsyncMessagingApi,
    Configuration,
    PushMessageRequest,
    TextMessage,
)
from linebot.v3.webhooks import MessageEvent, TextMessageContent

from formatter import format_error, format_no_result, format_results
from querier import query_by_address, split_cases

ADDRESS_PATTERN = re.compile(r"[路街道巷弄號]")


def _plain(text: str) -> str:
    return text.replace("*", "").replace("`", "").replace("[查看詳情]", "").replace("(https", " https")


def build_parser(channel_secret: str) -> WebhookParser:
    return WebhookParser(channel_secret)


async def handle_event(event: MessageEvent, config: Configuration) -> None:
    address = event.message.text.strip()

    async with AsyncApiClient(config) as client:
        api = AsyncMessagingApi(client)

        user_id = event.source.user_id

        if not ADDRESS_PATTERN.search(address):
            await api.push_message(PushMessageRequest(
                to=user_id,
                messages=[TextMessage(text="⚠️ 請輸入完整地址（需含路名及號碼）\n範例：和平東路一段100號")]
            ))
            return

        try:
            cases = await query_by_address(address)
        except Exception:
            await api.push_message(PushMessageRequest(
                to=user_id,
                messages=[TextMessage(text=format_error())]
            ))
            return

        if not cases:
            text = _plain(format_no_result(address))
        else:
            active, historical = split_cases(cases)
            text = _plain(format_results(address, active, historical))

        await api.push_message(PushMessageRequest(
            to=user_id,
            messages=[TextMessage(text=text)]
        ))
