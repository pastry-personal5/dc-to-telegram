#!/usr/bin/env python3
# To get a chat ID, visit https://medium.com/@ManHay_Hong/how-to-create-a-telegram-bot-and-send-messages-with-python-4cf314d9fa3e
import asyncio
import pprint
import requests

import dc_api

import logging

logging.basicConfig(
    level=logging.WARN, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


class _AsyncTimedIterator:

    __slots__ = ("_iterator", "_timeout", "_sentinel")

    def __init__(self, iterable, timeout, sentinel):
        self._iterator = iterable.__aiter__()
        self._timeout = timeout
        self._sentinel = sentinel

    async def __anext__(self):
        try:
            return await asyncio.wait_for(self._iterator.__anext__(), self._timeout)
        except asyncio.TimeoutError:
            return self._sentinel


class AsyncTimedIterable:

    __slots__ = ("_factory",)

    def __init__(self, iterable, timeout=None, sentinel=None):
        self._factory = lambda: _AsyncTimedIterator(iterable, timeout, sentinel)

    def __aiter__(self):
        return self._factory()


async def send_telegram_message(context, message):
    # bot_token = '12345:YOUR FULL BOT TOKEN'
    # bot_chat_id = 'YOUR CHAR ID' #
    url = (
        "https://api.telegram.org/bot"
        + bot_token
        + "/sendMessage?chat_id="
        + bot_chat_id
        + "&parse_mode=Markdown&text="
        + message
    )
    response = requests.get(url)
    pprint.pprint(response)


async def run_loop(context):
    CONST_TIMEOUT_IN_SEC = 8
    CONST_TIME_TO_SLEEP_IN_SEC = 8
    CONST_NUM_FIRST_FETCH = 16
    CONST_NUM_NORMAL_FETCH = 16
    api = dc_api.API()

    max_of_id = 0
    while True:
        print("[INFO] Trying to fetch board messages...")
        index_generator = None
        if max_of_id != 0:
            index_generator = api.board(
                context["board_id"],
                start_page=1,
                num=CONST_NUM_NORMAL_FETCH,
                document_id_lower_limit=max_of_id,
            )
        else:
            index_generator = api.board(
                context["board_id"], start_page=1, num=CONST_NUM_FIRST_FETCH
            )
        print("[INFO] Done!")
        message = ""
        cnt = 0
        timed_index_generator = AsyncTimedIterable(
            iterable=index_generator, timeout=CONST_TIMEOUT_IN_SEC
        )
        async for index in timed_index_generator:
            if index:
                print("[INFO] ... index.id " + index.id)
                if int(index.id) > max_of_id:
                    max_of_id = int(index.id)
                message += index.title + "\n"
                cnt += 1
        print(message)
        if cnt > 0:
            await send_telegram_message(context, message)
        print("[INFO] now |max_of_id| is " + str(max_of_id))
        print("[INFO] Sleeping...")
        await asyncio.sleep(CONST_TIME_TO_SLEEP_IN_SEC)
        print("[INFO] Done.")


async def main():
    context = {}
    context["board_id"] = "smask"
    await run_loop(context)


asyncio.run(main())
