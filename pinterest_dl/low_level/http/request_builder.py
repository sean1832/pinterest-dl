import json
import time
from urllib.parse import quote_plus, unquote_plus, urlencode


class RequestBuilder:
    def __init__(self) -> None:
        pass

    @staticmethod
    def build_post(options, source_url="/", context=None) -> str:
        return RequestBuilder.url_encode(
            {
                "source_url": source_url,
                "data": json.dumps({"options": options, "context": context}),
                "_": "%s" % int(time.time() * 1000),
            }
        )

    @staticmethod
    def build_get(endpoint: str, options: dict, source_url: str = "/", context: dict = {}) -> str:
        query = RequestBuilder.url_encode(
            {
                "source_url": source_url,
                "data": json.dumps({"options": options, "context": context}),
                "_": "%s" % int(time.time() * 1000),
            }
        )

        url = f"{endpoint}?{query}"
        return url

    @staticmethod
    def url_encode(query: str | dict) -> str:
        if isinstance(query, str):
            query = quote_plus(query)
        else:
            query = urlencode(query)
        query = query.replace("+", "%20")
        return query

    @staticmethod
    def url_decode(query: str) -> str:
        # Decode the URL-encoded string
        return unquote_plus(query)
