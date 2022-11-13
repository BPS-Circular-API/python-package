import requests


class API:
    """Methods which communicate with the API"""

    def __init__(self, url="https://bpsapi.rajtech.me/v1/"):
        self.url = url

    # /latest endpoint
    def latest(self, category: str or int, cached: bool = False) -> dict or None:
        """The /latest endpoint returns the latest circular from a particular category"""
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
            raise ConnectionError("Invalid API Response")
        if json['http_status'] == 200:
            return json['data']

    # /list endpoint
    def list(self, category: str or int, amount: int = -1) -> list or None:
        """The /list endpoint returns a list of circulars from a particular category"""
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
            raise ConnectionError("Invalid API Response")
        if json['http_status'] == 200:
            return json['data'] if amount == -1 else json['data'][:amount]

    def search(self, query: str or int) -> dict or None:
        """The /search endpoint lets you search for a circular by its name or ID"""
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
            raise ConnectionError("Invalid API Response")

        if json['http_status'] == 200:
            return json['data']

    # /getpng endpoint
    def getpng(self, url: str) -> list or None:
        """The /getpng endpoint lets you get the pngs from a circular"""
        if type(url) != str:
            raise ValueError("Invalid URL")

        params = {'url': url}

        request = requests.get(self.url + "getpng", params=params)
        json = request.json()

        try:
            json['http_status']

        except KeyError:
            raise ConnectionError("Invalid API Response")

        if json['http_status'] == 200:
            return json['data']


class CircularChecker:
    def __init__(self, category, url: str = "https://bpsapi.rajtech.me/v1/", cache_method=None, debug: bool = False, **kwargs):
        self.url = url
        self.category = category
        self._cache = []

        if debug:
            self.set_cache = self._set_cache
            self.refresh_cache = self._refresh_cache

        if type(category) == int:
            category = int(category)
            if not 1 < category < 100:
                raise ValueError("Invalid category Number")

        else:
            if category not in ["ptm", "general", "exam"]:
                raise ValueError("Invalid category Name")

        self._params = {'category': category}
        self.cache_method = cache_method

        if cache_method is not None:
            import pickle
            if cache_method == "database":
                try:
                    self.db_name = kwargs['db_name']
                    self.db_path = kwargs['db_path']
                    self.db_table = kwargs['db_table']
                except KeyError:
                    raise ValueError("Invalid Database Parameters")

                import sqlite3
                import os

                if not os.path.exists(self.db_path + f"/{self.db_name}.db"):
                    os.mkdir(self.db_path)

                self._con = sqlite3.connect(self.db_path + f"/{self.db_name}.db")
                self._cur = self._con.cursor()

                self._cur.execute(f"CREATE TABLE IF NOT EXISTS {self.db_table} (title TEXT, category TEXT, data BLOB)")
                self._cur.execute(f"INSERT INTO {self.db_table} VALUES (?, ?, ?)", ("circular_list", self.category, pickle.dumps([])))
                self._con.commit()

            elif cache_method == "pickle":
                try:
                    self.pickle_path = kwargs['pickle_path']
                    self.pickle_name = kwargs['pickle_name']
                except KeyError:
                    raise ValueError("Invalid Pickle Path")

                if self.pickle_name.endswith(".pickle"):
                    self.pickle_name = self.pickle_name[:-7]

                import os
                if not os.path.exists(self.pickle_path):
                    os.mkdir(self.pickle_path)
                # create a pickle file if it doesn't exist
                if not os.path.exists(self.pickle_path + f"/{self.pickle_name}.pickle"):
                    with open(self.pickle_path + f"/{self.pickle_name}.pickle", "wb") as f:
                        import pickle
                        pickle.dump([], f)

            else:
                raise ValueError("Invalid Cache Method")

        else:
            pass

    def get_cache(self) -> list[list]:
        import pickle
        if self.cache_method == "database":
            self._cur.execute(f"SELECT * FROM {self.db_table} WHERE category = ?", (self.category,))
            res = self._cur.fetchone()
            if res is None:
                return []
            else:
                return pickle.loads(res[2])

        elif self.cache_method == "pickle":

            with open(self.pickle_path + f"/{self.pickle_name}.pickle", "rb") as f:
                return pickle.load(f)

        else:
            return self._cache

    def _set_cache(self, data, title: str = "circular_list"):
        import pickle
        if self.cache_method == "database":
            self._cur.execute(f"DELETE FROM {self.db_table} WHERE category = ?", (self.category,))
            self._cur.execute(f"INSERT INTO {self.db_table} VALUES (?, ?, ?)", (title, self.category, pickle.dumps(data)))
            self._con.commit()

        elif self.cache_method == "pickle":
            with open(self.pickle_path + f"/{self.pickle_name}.pickle", "wb") as f:
                pickle.dump(data, f)

        else:
            self._cache = data

    def _refresh_cache(self):
        request = requests.get(self.url + "list", params=self._params)
        json = request.json()
        try:
            json['http_status']
        except KeyError:
            raise ValueError("Invalid API Response")
        if json['http_status'] == 200:
            self._set_cache(json['data'])

    def check(self) -> list[dict] or list[None]:
        return_dict = []
        old_cached = self.get_cache()

        if not old_cached:
            self._refresh_cache()
            return []

        self._refresh_cache()
        final_dict = self.get_cache()

        if final_dict != old_cached:  # If the old and new dict are not the same

            new_circular_objects = [i for i in final_dict if i not in old_cached]

            print(f"{len(new_circular_objects)} new circular(s) found")

            for circular in new_circular_objects:
                return_dict.append(circular)

            return return_dict

        else:
            return []





