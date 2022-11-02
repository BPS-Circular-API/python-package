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


