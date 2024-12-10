import pickle
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
    def __init__(self, category: str | int = None, url: str = "https://bpsapi.rajtech.me/", cache_method: str = 'sqlite', **kwargs):
        self.url = url
        self.category = category
        self.cache_method = cache_method
        self.latest_circular_id = self.get_cache()

        # Get category names from API
        json = requests.get(self.url + "categories").json()

        if json['http_status'] == 200:
            categories = json['data']
        else:
            raise ConnectionError("Invalid API Response. API says there are no categories.")

        # If category id is passed
        if category is not None:
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

        elif cache_method == 'pickle':
            try:
                self.cache_file = kwargs['cache_file']
            except KeyError:
                raise ValueError("Invalid cache file path")

        else:
            raise ValueError("Invalid cache method. Only mysql and sqlite allowed")

        # Create a table to cache circulars if it's not there
        if self.cache_method in ('sqlite', 'mysql'):
            con, cur = self._get_db()

            cur.execute(
                f"""
            CREATE TABLE IF NOT EXISTS  {self.db_table}  (
                category	TEXT,
                id	INTEGER UNIQUE,
                title	TEXT,
                link	TEXT
            )
            """
            )
            con.commit()
            con.close()

        # If cache method is pickle, create a file if it doesn't exist
        elif self.cache_method == 'pickle':
            if not os.path.exists(self.cache_file):
                with open(self.cache_file, 'wb') as f:
                    f.write(b'')

    def _get_db(self):
        if self.cache_method == 'mysql':
            con = mysql.connector.connect(
                host=self.db_host, port=self.db_port, password=self.db_password,
                user=self.db_user, database=self.db_name,
            )
            cur = con.cursor(prepared=True)

        elif self.cache_method == 'sqlite':
            con = sqlite3.connect(self.db_path + f"/{self.db_name}.db")
            cur = con.cursor()
        else:
            raise ValueError("Method not supported for this cache method")

        return con, cur


    # Method to retrieve cache from the database
    def get_cache(self) -> int | None:
        if self.cache_method in ('sqlite', 'mysql'):
            con, cur = self._get_db()

            cur.execute(f"SELECT latest_circular_id FROM {self.db_table} WHERE category = ?", (self.category,))
            res = cur.fetchone()

        elif self.cache_method == 'pickle':
            with open(self.cache_file, 'rb') as f:
                res = pickle.load(f)

        return res

    # Method to add multiple items to cache
    def _set_cache(self, circular_id: int):

        if self.cache_method in ('sqlite', 'mysql'):
            con, cur = self._get_db()
            query = f"INSERT OR IGNORE INTO {self.db_table} (category, latest_circular_id) VALUES (?, ?)"

            if self.cache_method == 'mysql':
                query = query.replace("OR ", "")

            cur.execute(query, (self.category, circular_id,))
            con.commit()

        elif self.cache_method == 'pickle':
            with open(self.cache_file, 'wb') as f:
                pickle.dumps(circular_id, f)


    # Method to check for new circular(s)
    def check(self) -> list[dict] | list:
        res = requests.get(self.url + f"new-circulars/{self.latest_circular_id}").json()['data']
        # it's sorted in descending order

        if len(res) > 0:
            self._set_cache(res[0]['id'])

            if self.category:
                res = [circular for circular in res if circular['category'] == self.category]

        return res


    # Close connections when object is deleted
    def __del__(self):
        pass

