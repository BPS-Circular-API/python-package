import requests
import pickle


class API:
    """Methods which communicate with the API"""

    def __init__(self, url="https://bpsapi.rajtech.me/v1/"):
        self.url = url

        json = requests.get(self.url + "categories").json()
        if json['http_status'] == 200:
            self.categories = json['data']
        else:
            raise ConnectionError("Invalid API Response. API says there are no categories.")

    # /latest endpoint
    def latest(self, category: str or int) -> dict or None:
        """The `/latest` endpoint returns the latest circular from a particular category"""
        if type(category) == int:
            category = int(category)
            if not 1 < category < 100:
                raise ValueError("Invalid category Number")

        else:
            if category not in self.categories:
                raise ValueError("Invalid category Name")

        params = {'category': category}

        request = requests.get(self.url + "latest", params=params)
        json = request.json()
        try:
            json['http_status']
        except KeyError:
            raise ConnectionError("Invalid API Response")
        if json['http_status'] == 200:
            return json['data']

    # /list endpoint
    def list(self, category: str or int, amount: int = -1) -> list or None:
        """The `/list` endpoint returns a list of circulars from a particular category"""
        if type(category) == int:
            category = int(category)
            if not 1 < category < 100:
                raise ValueError("Invalid category Number")

        else:
            if category not in self.categories:
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

    def search(self, query: str or int, amount: int = 1) -> dict or None:
        """The `/search` endpoint lets you search for a circular by its name or ID"""
        if query.isdigit() and len(query) == 4:
            query = int(query)
        elif type(query) != str:
            raise ValueError("Invalid Query")

        params = {'title': query, 'amount': amount}

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
        """The `/getpng` endpoint lets you get the pngs from a circular"""
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
    def __init__(self, category, url: str = "https://bpsapi.rajtech.me/v1/", cache_method=None, debug: bool = False,
                 **kwargs):
        self.url = url
        self.category = category
        self._cache = []

        json = requests.get(self.url + "categories").json()
        if json['http_status'] == 200:
            self.categories = json['data']
        else:
            raise ConnectionError("Invalid API Response. API says there are no categories.")

        if debug:
            self.set_cache = self._set_cache
            self.refresh_cache = self._refresh_cache

        if type(category) == int:
            category = int(category)
            if not 1 < category < 100:
                raise ValueError("Invalid category Number")

        else:
            if category not in self.categories:
                raise ValueError("Invalid category Name")

        self._params = {'category': category}
        self.cache_method = cache_method

        if cache_method is not None:
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

                self._cur.execute(
                    f"CREATE TABLE IF NOT EXISTS {self.db_table} (title TEXT, category TEXT, data BLOB)")

                # check if the cache exists
                self._cur.execute(f"SELECT * FROM {self.db_table} WHERE title = ? AND category = ?",
                                  ("circular_list", self.category))
                if self._cur.fetchone() is None:
                    self._cur.execute(f"INSERT INTO {self.db_table} VALUES (?, ?, ?)",
                                      ("circular_list", self.category, pickle.dumps([])))
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
                        pickle.dump([], f)

            else:
                raise ValueError("Invalid Cache Method")

    def get_cache(self) -> list[list]:
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
        if self.cache_method == "database":
            self._cur.execute(f"DELETE FROM {self.db_table} WHERE category = ?", (self.category,))
            self._cur.execute(f"INSERT INTO {self.db_table} VALUES (?, ?, ?)",
                              (title, self.category, pickle.dumps(data)))
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

        self._cur.execute(f"SELECT * FROM {self.db_table} WHERE category = ?", (self.category,))
        res = self._cur.fetchone()
        if res is None:
            cache = []
        else:
            cache = pickle.loads(res[2])

        self._refresh_cache()
        final_dict = self.get_cache()

        if final_dict != old_cached:  # If the old and new dict are not the same
            new_circular_objects = [i for i in final_dict if i not in old_cached]

            for circular in new_circular_objects:
                # check if they are in the database
                if circular in cache:
                    continue

                return_dict.append(circular)

            # sort the return_dict by circular id in ascending order
            return_dict.sort(key=lambda x: x['circular_id'])
            return return_dict

        else:
            return []


class CircularCheckerGroup:
    def __init__(self, *args, **kwargs):
        self._checkers = []

        if kwargs.get("debug"):
            self.debug = True
        else:
            self.debug = False

        for arg in args:
            if type(arg) != CircularChecker:
                raise ValueError("Invalid CircularChecker Object")
            self._checkers.append(arg)

        if self.debug:
            self.checkers = self._checkers

    def add(self, checker: CircularChecker, *args: CircularChecker):
        self._checkers.append(checker)
        for arg in args:
            if type(arg) != CircularChecker:
                raise ValueError("Invalid CircularChecker Object")
            self._checkers.append(arg)

    def create(self, category, url: str = "https://bpsapi.rajtech.me/v1/", cache_method=None, debug: bool = False,
               **kwargs):
        checker = CircularChecker(category, url, cache_method, debug, **kwargs)
        self._checkers.append(checker)

    def check(self) -> dict[list[dict] or list[None]]:
        return_dict = {}
        for checker in self._checkers:
            return_dict[checker.category] = checker.check()
        return return_dict

    def refresh_cache(self):
        for checker in self._checkers:
            checker.refresh_cache()

    def get_cache(self) -> dict[list[list]]:
        return_dict = {}
        for checker in self._checkers:
            return_dict[checker.category] = checker.get_cache()
        return return_dict
