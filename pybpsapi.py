import warnings
import mysql.connector
import requests
import sqlite3
import os

_min_category_id = 23

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
    def latest(self, category: str | int) -> dict | None:
        """The `/latest` endpoint returns the latest circular from a particular category"""

        if type(category) is str:
            if category.isdigit():
                try:
                    category = int(category)
                except ValueError:
                    warnings.warn(f"Category id: {category} is digit, but cannot be converted to int. "
                                  f"It will be treated as a category name.")

        # A category id or category name can be passed in
        if type(category) is int:
            if not _min_category_id <= category:
                raise ValueError("Invalid category Number")
        else:
            # Check with the API's category list
            if category not in self.categories:
                raise ValueError("Invalid category Name")

        request = requests.get(f"{self.url}latest/{category}")
        json = request.json()

        if json.get("data") is None or json.get("http_status") is None:
            raise ConnectionError("Invalid API Response, it doesn't contain either 'data' or 'http_code'")

        return json['data']

    # /list endpoint
    def list_(self, category: str | int, amount: int = None) -> list | None:
        """The `/list` endpoint returns a list of circulars from a particular category"""
        if type(category) is int:
            if not _min_category_id <= category:
                raise ValueError("Invalid category Number")

        else:
            if category not in self.categories:
                raise ValueError("Invalid category Name")

        if type(amount) is int and amount < 1:
            amount = None

        request = requests.get(f"{self.url}list/{category}")
        json = request.json()

        if json.get("data") is None or json.get("http_status") is None:
            raise ConnectionError("Invalid API Response, it doesn't contain either 'data' or 'http_code'")

        return json['data'][:amount]

    # /search endpoint
    def search(self, query: str | int, amount: int = 1) -> dict | None:
        """The `/search` endpoint lets you search for a circular by its name or ID"""
        if query.isdigit() and len(query) == 4:
            query = int(query)
        elif type(query) is not str:
            raise ValueError("Invalid Query. It isn't string")

        params = {'query': query, 'amount': amount}

        request = requests.get(self.url + "search", params=params)
        json = request.json()

        if json.get("data") is None or json.get("http_status") is None:
            raise ConnectionError("Invalid API Response, it doesn't contain either 'data' or 'http_code'")

        return json['data']

    # /getpng endpoint
    def getpng(self, url: str) -> list | None:
        """The `/getpng` endpoint lets you get the pngs from a circular"""
        if type(url) != str:
            raise ValueError("Invalid URL. It isn't string.")

        params = {'url': url}

        request = requests.get(self.url + "getpng", params=params)
        json = request.json()

        if json.get("data") is None or json.get("http_status") is None:
            raise ConnectionError("Invalid API Response, it doesn't contain either 'data' or 'http_code'")

        return json['data']


class CircularChecker:
    def __init__(self, category: str | int, url: str = "https://bpsapi.rajtech.me/", cache_method: str = 'sqlite', **kwargs):
        self.url = url
        self.category = category
        self.cache_method = cache_method
        self._cache = []

        # Get category names from API
        json = requests.get(self.url + "categories").json()

        if json['http_status'] == 200:
            categories = json['data']
        else:
            raise ConnectionError("Invalid API Response. API says there are no categories.")

        if kwargs.get("debug"):
            self.set_cache = self._set_cache
            self.refresh_cache = self._refresh_cache

        # If category id is passed
        if type(self.category) is int:
            if not _min_category_id <= self.category:
                raise ValueError("Invalid category Number")
        else:   # If category name is passed
            if self.category not in categories:
                raise ValueError("Invalid category Name")

        # For the sqlite cache method
        if self.cache_method == "sqlite":
            try:
                self.db_name = kwargs['db_name']
                self.db_path = kwargs['db_path']
                self.db_table = kwargs['db_table']
            except KeyError:
                raise ValueError(
                    "Invalid Database Parameters. One of db_name, db_path, db_table not passed into kwargs")

            # Create local db if it does not exist
            if not os.path.exists(self.db_path + f"/{self.db_name}.db"):
                os.mkdir(self.db_path)

            self._con = sqlite3.connect(self.db_path + f"/{self.db_name}.db")
            self._cur = self._con.cursor()

        # For the mysql/mariadb cache method
        elif cache_method == "mysql":
            try:
                self.db_name = kwargs['db_name']
                self.db_user = kwargs['db_user']
                self.db_host = kwargs['db_host']
                self.db_port = kwargs['db_port']
                self.db_password = kwargs['db_password']
                self.db_table = kwargs['db_table']

            except KeyError:
                raise ValueError(
                    "Invalid Database Parameters. One of db_name, db_user, db_host, db_port, db_password, db_table not passed into kwargs")

            self._con = mysql.connector.connect(
                host=self.db_host, port=self.db_port, password=self.db_password,
                user=self.db_user, database=self.db_name,
            )
            self._cur = self._con.cursor(prepared=True)

        else:
            raise ValueError("Invalid cache method. Only mysql and sqlite allowed")

        # Create a table to cache circulars if it's not there
        self._cur.execute(
            f"""
        CREATE TABLE IF NOT EXISTS  {self.db_table}  (
            category	TEXT,
            id	INTEGER UNIQUE,
            title	TEXT,
            link	TEXT
        )
        """
        )
        self._con.commit()


    # Method to retrieve cache from the database
    def get_cache(self) -> list[list] | list:
        self._cur.execute(f"SELECT id, title, link FROM {self.db_table} WHERE category = ?", (self.category,))
        res = self._cur.fetchall()

        return res

    # Method to add multiple items to cache
    def _set_cache(self, data):
        # data [ (id, title, link) ]
        query = f"INSERT OR IGNORE INTO {self.db_table} (category, id, title, link) VALUES (?, ?, ?, ?)"

        if self.cache_method == 'mysql':
            query = query.replace("OR ", "")

        self._cur.executemany(query, tuple((self.category, *d) for d in data))
        self._con.commit()

    # Method to add a single item to cache
    def _add_to_cache(self, id_: int, title: str, link: str):
        query = f"INSERT OR IGNORE INTO {self.db_table} (id, title, link) VALUES (?, ?, ?, ?)"

        if self.cache_method == 'mysql':
            query = query.replace("OR ", "")

        self._cur.execute(query, (self.category, id_, title, link))

    # Method to retrieve circulars from the API and insert into cache
    def _refresh_cache(self):
        request = requests.get(f"{self.url}list/{self.category}")
        json: dict = request.json()

        if json.get("data") is None or json.get("http_status") is None:
            raise ConnectionError("Invalid API Response, it doesn't contain either 'data' or 'http_code'")

        self._cur.execute(f"SELECT id FROM {self.db_table} WHERE category = ?", (self.category,))

        # ((1234,), (4567,), ...) -> ('1234', '4567')
        cached_ids: list = self._cur.fetchall()
        cached_ids: tuple[str, ...] = tuple([str(i[0]) for i in cached_ids])

        if json['http_status'] == 200:
            self._set_cache(
                [
                    (i['id'], i['title'], i['link'])
                    for i in json['data']
                    if i['id'] not in cached_ids    # Add only new circulars to the database
                ]
            )

    # Method to check for new circular(s)
    def check(self) -> list[dict] | list:
        # First get cached circulars and store them in a variable 'cached_circular_ids'
        # Then refresh cache and get the new list of circulars, and then compare and find new ones.
        self._cur.execute(f"SELECT id FROM {self.db_table} WHERE category = ?", (self.category,))

        cached_circular_ids = self._cur.fetchall()
        cached_circular_ids = [i[0] for i in cached_circular_ids]   # [(id, title, link)]

        self._refresh_cache()
        new_circular_list = self.get_cache() #

        # If there are new circulars
        if len(new_circular_list) > len(cached_circular_ids):
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

        return []

    # Close connections when object is deleted
    def __del__(self):
        if hasattr(self, '_con'):
            self._con.close()


class CircularCheckerGroup:
    def __init__(self, *circular_checkers: CircularChecker, **kwargs):
        self._checkers = []

        # Add each checker to self._checkers
        for checker in circular_checkers:
            if type(checker) is not CircularChecker:
                raise ValueError("Invalid CircularChecker Object")
            self._checkers.append(checker)

        if bool(kwargs.get("debug")):
            self.checkers = self._checkers

    # Method to add a circular checker to this group
    def add(self, checker: CircularChecker, *circular_checkers: CircularChecker):
        self._checkers.append(checker)

        for checker in circular_checkers:
            if type(checker) is not CircularChecker:
                raise ValueError("Invalid CircularChecker Object")
            self._checkers.append(checker)

    # Method to create a circular checker and add it to the group
    def create(self, category, url: str = "https://bpsapi.rajtech.me/", cache_method=None, **kwargs):
        checker = CircularChecker(category, url, cache_method, **kwargs)
        self._checkers.append(checker)

    # Method to check for new circulars in each one of the checkers
    def check(self) -> dict[list[dict], ...] | dict:
        return_dict = {}
        for checker in self._checkers:
            return_dict[checker.category] = checker.check()
        return return_dict

    # Method to refresh (sync) cache from API
    def refresh_cache(self):
        for checker in self._checkers:
            checker.refresh_cache()

    # Method to get the cache of all checkers
    def get_cache(self) -> dict[list[list]] | dict:
        return_dict = {}
        for checker in self._checkers:
            return_dict[checker.category] = checker.get_cache()
        return return_dict

    def __del__(self):
        for checker in self._checkers:
            del checker