from typing import Dict, List, Any
import requests
import os
import json
from os.path import join
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

load_dotenv(verbose=True)
ENV_FILE = '.env.production' if os.environ.get(
    "PYTHON_ENV") == 'production' else '.env.development'
dotenv_path = join(os.getcwd(), ENV_FILE)
load_dotenv(dotenv_path)


def auth():
    return os.environ.get("TWITTER_BEARER_TOKEN")

# Rate limits https://developer.twitter.com/en/docs/rate-limits
# 450 requests per 15 - minute window(app auth)
# 180 requests per 15 - minute window(user auth)


def create_time_fields(sec=10, day=0):
    since_date = ""
    td = ""
    utc_date = datetime.now(timezone.utc)
    td = timedelta(days=day, seconds=sec)
    since_date = utc_date - td
    start_time_fields = "start_time=" + since_date.strftime("%Y-%m-%dT%H:%M:%SZ")
    return start_time_fields


def create_url(queries=[]):
    # GET /2/tweets/search/recent
    query_strings = ''
    if queries is not []:
        query_strings = ("?" + "".join([q + "&" for q in queries]))[:-1]
    url = "https://api.twitter.com/2/tweets/search/recent{}".format(
        query_strings)
    return url


def create_headers(bearer_token):
    headers = {"Authorization": "Bearer {}".format(bearer_token)}
    return headers


def connect_to_endpoint(url, headers):
    response = requests.request("GET", url, headers=headers)
    print(response.status_code)
    if response.status_code != 200:
        raise Exception(response.status_code, response.text)
    return response.json()


def isunion(a, b):
    return a or b


def isintersect(a, b):
    return a and b


def check_txt(keywords, txt, cond='or'):
    func = isunion if cond == 'or' else isintersect
    is_included = False
    for word in keywords:
        is_included = func((word in txt), is_included)
    return is_included


def mining_txt(keywords, datas: Dict[str, Any], cond='or'):
    matched_data = []
    if datas["meta"]["result_count"] == 0:
        return []
    for data in datas["data"]:
        if check_txt(keywords, data["text"], cond):
            matched_data.append(data)
    return matched_data


def recent_research(keywords, queries, cond='or'):
    """ tweeter recent research

    """
    bearer_token = auth()
    url = create_url(queries)
    headers = create_headers(bearer_token)
    res = connect_to_endpoint(url, headers)
    # d = json.dumps(res, indent=2, sort_keys=True)
    # print("Feched Tweets: ", d)

    matched = mining_txt(keywords, res, cond)
    print("Matched Tweets:", json.dumps(matched, indent=2))
    return matched


if __name__ == "__main__":
    query = "query=from:elonmusk -is:retweet"
    tweet_fields = "tweet.fields=author_id"
    utc_date = datetime.now(timezone.utc)
    utc_date = utc_date.replace(second=(utc_date.second - 10) % 60)
    utc_date = utc_date.replace(day=(utc_date.day - 3) % 60)
    start_time_fields = "start_time=" + utc_date.strftime("%Y-%m-%dT%H:%M:%SZ")

    keywords = ['doge', 'Doge', 'DOGE']
    queries = [query, tweet_fields, start_time_fields]
    recent_research(keywords, queries)
