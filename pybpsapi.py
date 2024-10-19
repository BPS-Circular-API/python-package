import mysql.connector
import requests


class API:
    """Methods which communicate with the API"""

    def __init__(self, url="https://bpsapi.rajtech.me/"):
        self.url = url
        self.list = self.list_

        json = requests.get(self.url + "categories").json()
        if json['http_status'] == 200:
            self.categories = json['data']
        else:
            raise ConnectionError("Invalid API Response. API says there are no categories.")

    # /latest endpoint
    def latest(self, category: str or int) -> dict | None:
        """The `/latest` endpoint returns the latest circular from a particular category"""
        if type(category) is int:
            category = int(category)

            if not 1 < category < 100:
                raise ValueError("Invalid category Number")

        else:
            if category not in self.categories:
                raise ValueError("Invalid category Name")

        request = requests.get(f"{self.url}latest/{category}")
        json = request.json()

        try:
            json['http_status']
        except KeyError:
            raise ConnectionError("Invalid API Response")
        if json['http_status'] == 200:
            return json['data']

    # /list endpoint
    def list_(self, category: str or int, amount: int = None) -> list | None:
        """The `/list` endpoint returns a list of circulars from a particular category"""
        if type(category) is int:
            if not 1 < category < 100:
                raise ValueError("Invalid category Number")

        else:
            if category not in self.categories:
                raise ValueError("Invalid category Name")

        if amount < 1:
            amount = None

        request = requests.get(f"{self.url}list/{category}")
        json = request.json()

        try:
            json['http_status']
        except KeyError:
            raise ConnectionError("Invalid API Response")
        if json['http_status'] == 200:
            return json['data'][:amount]

    def search(self, query: str or int, amount: int = 1) -> dict | None:
        """The `/search` endpoint lets you search for a circular by its name or ID"""
        if query.isdigit() and len(query) == 4:
            query = int(query)
        elif type(query) != str:
            raise ValueError("Invalid Query")

        params = {'query': query, 'amount': amount}

        request = requests.get(self.url + "search", params=params)
        json = request.json()

        try:
            json['http_status']

        except KeyError:
            raise ConnectionError("Invalid API Response")

        if json['http_status'] == 200:
            return json['data']

    # /getpng endpoint
    def getpng(self, url: str) -> list | None:
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
    def __init__(self, category, url: str = "https://bpsapi.rajtech.me/", cache_method='sqlite', debug: bool = False,
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

        self.cache_method = cache_method

        if cache_method is None:
            raise ValueError("Invalid Cache Method")

        if cache_method == "sqlite":
            try:
                self.db_name = kwargs['db_name']
                self.db_path = kwargs['db_path']
                self.db_table = kwargs['db_table']
            except KeyError:
                raise ValueError("Invalid Database Parameters. One of db_name, db_path, db_table not passed into kwargs")

            import sqlite3
            import os

            if not os.path.exists(self.db_path + f"/{self.db_name}.db"):
                os.mkdir(self.db_path)

            self._con = sqlite3.connect(self.db_path + f"/{self.db_name}.db")
            self._cur = self._con.cursor()

        elif cache_method == "mysql":
            try:
                self.db_name = kwargs['db_name']
                self.db_user = kwargs['db_user']
                self.db_host = kwargs['db_host']
                self.db_port = kwargs['db_port']
                self.db_password = kwargs['db_password']
                self.db_table = kwargs['db_table']

            except KeyError:
                raise ValueError("Invalid Database Parameters. One of db_name, db_user, db_host, db_port, db_password, db_table not passed into kwargs")

            self._con = mysql.connector.python(
                host=self.db_host, port=self.db_port, password=self.db_password,
                user=self.db_user, database=self.db_name,
            )

            self._cur = self._con.cursor()

        self._cur.execute(
            f"CREATE TABLE IF NOT EXISTS {self.db_table} (category TEXT, id INTEGER, title TEXT, link TEXT)"
        )
        self._con.commit()

    def get_cache(self) -> list[list]:
        self._cur.execute(f"SELECT * FROM {self.db_table} WHERE category = ?", (self.category,))
        res = self._cur.fetchall()

        return res

    def _set_cache(self, data):
        # data [ (id, title, link) ]
        self._cur.executemany(
            f"INSERT IGNORE INTO {self.db_table} (category, id, title, link) VALUES ({self.category}, ?, ?, ?)",
            data
        )
        self._con.commit()

    def _add_to_cache(self, id_, title, link):
        self._cur.execute(
            f"INSERT IGNORE INTO {self.db_table} (id, title, link) VALUES (?, ?, ?, ?)",
            (self.category, id_, title, link)
        )

    def _refresh_cache(self):
        request = requests.get(f"{self.url}list/{self.category}")
        json = request.json()

        try:
            json['http_status']
        except KeyError:
            raise ValueError("Invalid API Response")

        if json['http_status'] == 200:
            self._set_cache(json['data'])

    def check(self) -> list[dict] | list[None]:
        self._cur.execute(f"SELECT COUNT(*) FROM {self.db_table} WHERE category = ?", (self.category,))
        cached_circular_amount = self._cur.fetchone()[0]

        self._refresh_cache()
        new_circular_list = self.get_cache()
        # data[(id, title, link)]

        if len(new_circular_list) != cached_circular_amount:
            self._cur.execute(f"SELECT id FROM {self.db_table} WHERE category = ?", (self.category,))

            cached_circular_ids = self._cur.fetchall()
            cached_circular_ids = [i[0] for i in cached_circular_ids]

            new_circular_objects = [i for i in new_circular_list if i[0] not in cached_circular_ids]

            # (id, title, link) -> {'id': id, 'title': title, 'link': link}
            new_circular_objects = [
                {
                    'id': i[0],
                    'title': i[1],
                    'link': i[2]
                }
                for i in new_circular_objects
            ]

            # sort the new_circular_objects by circular id in ascending order
            new_circular_objects.sort(key=lambda x: x['id'])
            return new_circular_objects

        else:
            return []


class CircularCheckerGroup:
    def __init__(self, *args, **kwargs):
        self._checkers = []

        for arg in args:
            if type(arg) is not CircularChecker:
                raise ValueError("Invalid CircularChecker Object")
            self._checkers.append(arg)

        if bool(kwargs.get("debug")):
            self.checkers = self._checkers

    def add(self, checker: CircularChecker, *args: CircularChecker):
        self._checkers.append(checker)
        for arg in args:
            if type(arg) is not CircularChecker:
                raise ValueError("Invalid CircularChecker Object")
            self._checkers.append(arg)

    def create(self, category, url: str = "https://bpsapi.rajtech.me/", cache_method=None, **kwargs):
        checker = CircularChecker(category, url, cache_method, **kwargs)
        self._checkers.append(checker)

    def check(self) -> dict[list[dict], ...] | dict:
        return_dict = {}
        for checker in self._checkers:
            return_dict[checker.category] = checker.check()
        return return_dict

    def refresh_cache(self):
        for checker in self._checkers:
            checker.refresh_cache()

    def get_cache(self) -> dict[list[list]] | dict:
        return_dict = {}
        for checker in self._checkers:
            return_dict[checker.category] = checker.get_cache()
        return return_dict
