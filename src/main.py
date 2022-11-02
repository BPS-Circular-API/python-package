import requests


class Circular:
    def __init__(self, url="https://bpsapi.rajtech.me/v1/"):
        self.url = url

    # /latest endpoint
    def latest(self, category: str or int, cached: bool = False) -> dict or None:
        if type(category) == int:
            category = int(category)
            if not 1 < category < 100:
                raise ValueError("Invalid category Number")

        else:
            if category not in ["ptm", "general", "exam"]:
                raise ValueError("Invalid category Name")

        params = {'category': category}
        endpoint = "latest" if not cached else "cached-latest"

        request = requests.get(self.url + endpoint, params=params)
        json = request.json()
        try:
            json['http_status']
        except KeyError:
            raise ValueError("Invalid API Response")
        if json['http_status'] == 200:
            return json['data']

    # /list endpoint
    def list(self, category: str or int, amount: int = -1) -> list or None:
        if type(category) == int:
            category = int(category)
            if not 1 < category < 100:
                raise ValueError("Invalid category Number")

        else:
            if category not in ["ptm", "general", "exam"]:
                raise ValueError("Invalid category Name")

        if amount < -1:
            amount = -1

        params = {'category': category}

        request = requests.get(self.url + "list", params=params)
        json = request.json()
        try:
            json['http_status']
        except KeyError:
            raise ValueError("Invalid API Response")
        if json['http_status'] == 200:
            return json['data'] if amount == -1 else json['data'][:amount]

    def search(self, query: str or int) -> dict or None:
        if type(query) == int:
            query = int(query)
        elif type(query) != str:
            raise ValueError("Invalid Query")

        params = {'title': query}

        request = requests.get(self.url + "search", params=params)
        json = request.json()

        try:
            json['http_status']

        except KeyError:
            raise ValueError("Invalid API Response")

        if json['http_status'] == 200:
            return json['data']

    # /getpng endpoint
    def getpng(self, url: str) -> list or None:
        if type(url) != str:
            raise ValueError("Invalid URL")

        params = {'url': url}

        request = requests.get(self.url + "getpng", params=params)
        json = request.json()

        try:
            json['http_status']

        except KeyError:
            raise ValueError("Invalid API Response")

        if json['http_status'] == 200:
            return json['data']

