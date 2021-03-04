import asyncio
from typing import Dict, List, Union
from ftx.ftx import FTX
from line import push_message
from setting.settting import FTX_API_KEY, FTX_API_SECRET, PYTHON_ENV, SUBACCOUNT, TRADABLE
import json


class Bot:
    DEFAULT_SIZE = 100.0
    SPECIFIC_NAME = ["SPACEX", "STARLINK", "STAR", "STRLK"]
    SPECIFIC_SIZE = 900.0
    prev_markets: List[Dict[str, Union[str, float]]] = []

    def __init__(self, api_key, api_secret):
        self.ftx = FTX(
            "",
            api_key=api_key,
            api_secret=api_secret,
            subaccount=SUBACCOUNT)

        print(f"ENV:{PYTHON_ENV}\nSUBACCOUNT:{SUBACCOUNT}")
        # タスクの設定およびイベントループの開始
        loop = asyncio.get_event_loop()
        tasks = [self.run()]
        loop.run_until_complete(asyncio.wait(tasks))

    # ---------------------------------------- #
    # bot main
    # ---------------------------------------- #
    async def run(self):
        while True:
            await self.main(5)
            await asyncio.sleep(0)

    async def main(self, interval):
        # main処理
        """
        """
        listed = []
        new_listed = []

        self.ftx.market()
        response = await self.ftx.send()
        # print(json.dumps(response[0]['result'], indent=2, sort_keys=False))
        listed = self.extract_name(markets=response[0]['result'], include=["spot"])
        print(json.dumps(listed, indent=2, sort_keys=False))

        if self.prev_markets == []:
            self.prev_markets = listed
            print("Snapshot markets...")
        else:
            # 新規上場を検知
            new_listed = self.extract_new_listed(self.prev_markets, listed)
            print(
                "New Listed...",
                json.dumps(
                    new_listed,
                    indent=2,
                    sort_keys=False))

            if TRADABLE:
                for new in new_listed:
                    size = self.DEFAULT_SIZE / float(new["bid"])
                    if new["baseCurrency"] in self.SPECIFIC_NAME:
                        size = self.SPECIFIC_SIZE
                    if PYTHON_ENV == 'production':
                        self.ftx.place_order(
                            type='market',
                            market=new["name"],
                            side='buy',
                            price='',
                            size=size,
                            postOnly=False)
                        response = await self.ftx.send()
                        print(response[0])
                        orderId = response[0]['result']['id']
                        push_message(f"Ordered :\norderId:{orderId}")
                    else:
                        # テスト
                        print(f"DEVELOPMENT:>>\nMARKET:{new['name']}\nSIZE:{size}")

            # SNSに通知する
        for new in new_listed:
            push_message(f"NEW LISTED: {json.dumps(new)}")

        await asyncio.sleep(interval)
        # Update...
        self.prev_markets = listed
        listed = []

        await asyncio.sleep(0)

    def extract_name(
            self,
            markets,
            include=["spot", "future"],
            exclude=["HEDGE", "BULL", "BEAR", "HALF", "BVOL"]):
        satsfied = []
        has_spot = "spot" in include
        has_future = "future" in include
        for market in markets:
            if market["enabled"]:
                if has_spot and market['type'] == "spot" and market["quoteCurrency"] == 'USD':
                    is_excluded = True
                    for token in exclude:
                        is_excluded = is_excluded and token not in market["baseCurrency"]
                    if is_excluded:
                        satsfied.append(market)
                if has_future and market["type"] == 'future':
                    satsfied.append(market)
        return satsfied

    def extract_new_listed(
            self,
            prev_markets: List[Dict[str, Union[str, float]]],
            current_markets: List[Dict[str, Union[str, float]]]) -> List[Dict[str, Union[str, float]]]:
        new_listed = []
        if len(current_markets) == 0:
            return new_listed
        prev_market_names = [prev_market["name"] for prev_market in prev_markets]
        for current_market in current_markets:
            name = current_market["name"]
            if name not in prev_market_names:
                new_listed.append(current_market)
        return new_listed


if __name__ == "__main__":

    Bot(api_key=FTX_API_KEY, api_secret=FTX_API_SECRET)
