import json
import time
from urllib.parse import quote_plus, unquote_plus, urlencode


class RequestBuilder:
    def __init__(self) -> None:
        pass

    def build_post(self, options, source_url="/", context=None) -> str:
        return self.url_encode(
            {
                "source_url": source_url,
                "data": json.dumps({"options": options, "context": context}),
                "_": "%s" % int(time.time() * 1000),
            }
        )

    def build_get(
        self, endpoint: str, options: dict, source_url: str = "/", context: dict = {}
    ) -> str:
        query = self.url_encode(
            {
                "source_url": source_url,
                "data": json.dumps({"options": options, "context": context}),
                "_": "%s" % int(time.time() * 1000),
            }
        )

        url = f"{endpoint}?{query}"
        return url

    def url_encode(self, query: str | dict) -> str:
        if isinstance(query, str):
            query = quote_plus(query)
        else:
            query = urlencode(query)
        query = query.replace("+", "%20")
        return query

    def url_decode(self, query: str) -> str:
        # Decode the URL-encoded string
        return unquote_plus(query)
