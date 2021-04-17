"""
    BotBaseを継承したアーキテクチャ
    tweetでロングするボット
    エントリーのみで決済しない
"""
import asyncio
from typing import List
import json
from ftx_bot_base import BotBase
from setting.settting import PYTHON_ENV, FTX_API_KEY, FTX_API_SECRET, SUBACCOUNT, config
from twitter.recent_research import recent_research, create_time_fields

MARKET = config['MARKET']
MARKET_TYPE = config["MARKET_TYPE"]
SEC_TO_EXPIRE = config.getfloat('SEC_TO_EXPIRE')
MAX_POSITION_SIZE = config.getfloat('MAX_POSITION_SIZE')


SIZE = config.getfloat('SIZE')
QUERY = config['QUERY']
KEY_WORDS: List[str] = json.loads(config['KEY_WORDS'])
COND = config['COND']  # `or` OR `and`
CYCLE = config.getboolean('CYCLE')


class Bot(BotBase):
    def __init__(self, market, market_type, api_key, api_secret, subaccount):
        super().__init__(market, market_type, api_key, api_secret, subaccount)
        self.MARKET = MARKET
        # タスクの設定およびイベントループの開始
        loop = asyncio.get_event_loop()
        tasks = [self.run_strategy()]
        if CYCLE:
            tasks = [self.run(10)] + tasks
        # tasks = [self.run(10), self.run_strategy()]
        loop.run_until_complete(asyncio.wait(tasks))

    async def run_strategy(self):
        while True:
            try:
                await self.strategy(4)
                await asyncio.sleep(10)
            except Exception as e:
                self.logger.error(f'Unhandled Error :strategy {str(e)}')
                self.push_message(f'Unhandled Error :strategy {str(e)}')

    async def strategy(self, interval):
        # pos, success = await self.get_position()
        # if not success:
        #     return await asyncio.sleep(5)
        # elif pos["size"] > float(MAX_POSITION_SIZE):
        #     msg = f'MAX_POSITION_SIZE current size:{pos["size"]}'
        #     self.logger.info(msg)
        #     self.push_message(msg)
        #     return await asyncio.sleep(15)
        day = 0 if PYTHON_ENV == 'production' else 1
        keywords = KEY_WORDS
        query = QUERY
        tweet_fields = "tweet.fields=author_id"
        start_time_fields = create_time_fields(sec=12, day=day)
        queries = [query, tweet_fields, start_time_fields]

        result = recent_research(keywords, queries, COND)

        if len(result) > 0:
            self.push_message(f"Detect events:\nkeywords:{keywords}\n{result}")
            if PYTHON_ENV == 'production':
                await self.place_order(
                    ord_type='market',
                    side='buy',
                    price='',
                    size=3800,
                    postOnly=False,
                    ioc=True,
                    sec_to_expire=SEC_TO_EXPIRE
                )
            else:
                await self.place_order(
                    ord_type='limit',
                    side='buy',
                    price=1111,
                    size=0.001,
                    postOnly=True,
                    sec_to_expire=SEC_TO_EXPIRE
                )
        await asyncio.sleep(interval)


if __name__ == "__main__":
    bot = Bot(MARKET, MARKET_TYPE, FTX_API_KEY, FTX_API_SECRET, SUBACCOUNT)
