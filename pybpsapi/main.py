import pickle
import warnings
try:
    import mysql.connector as mysql_connector
except Exception:
    mysql_connector = None
try:
    import requests
except Exception:
    requests = None
import sqlite3
import os

_min_category_id = 23

class API:
    """Methods which communicate with the API"""

    def __init__(self, url="https://bpsapi.rajtech.me/"):
        if requests is None:
            raise ImportError("requests is required to use API class")
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
        if type(query) is str:
            if query.isdigit() and len(query) == 4:
                query = int(query)
        elif type(query) is not int:
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
        if type(url) is not str:
            raise ValueError("Invalid URL. It isn't string.")

        params = {'url': url}

        request = requests.get(self.url + "getpng", params=params)
        json = request.json()

        if json.get("data") is None or json.get("http_status") is None:
            raise ConnectionError("Invalid API Response, it doesn't contain either 'data' or 'http_code'")

        return json['data']


class CircularChecker:
    def __init__(
            self, category: str | int = None,
            api_url: str = "https://bpsapi.rajtech.me/",
            fallback_api_url: str = None,
            cache_method: str = 'pickle', **kwargs
    ):
        self.api_url = api_url
        self.fallback_api_url = fallback_api_url
        self.category = category
        self.cache_method = cache_method
        # internal cache key used for storage (DB/pickle). Use a stable string instead of None
        self._category_key = str(self.category) if self.category is not None else '__ALL__'

        # Get category names from API
        del category # To avoid confusion with self.category
        categories = self._send_api_request("categories")

        # If this circular checker is supposed to be for a specific category of circulars only
        # Check if the category name or id is valid
        if self.category is not None:
            if type(self.category) is int:
                if not _min_category_id <= self.category:
                    raise ValueError("Invalid category Number")
            else:   # If category name is passed
                if self.category not in categories:
                    raise ValueError(f"Invalid category Name ({self.category})."
                                     f"Allowed are {categories}")

        # Check if all required variables for each cache method are passed in kwargs
        # And create a pickle file or database file on disk (sqlite) if it doesn't exist
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
            if not os.path.exists(self.db_path):
                os.makedirs(self.db_path, exist_ok=True)

        # For the mysql/mariadb cache method
        elif self.cache_method == "mysql":
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

        # For the pickle cache method
        elif self.cache_method == 'pickle':
            try:
                self.cache_file = kwargs['cache_file']
            except KeyError:
                raise ValueError("Invalid cache file path")

            if not os.path.exists(self.cache_file):
                with open(self.cache_file, 'wb') as f:
                    f.write(pickle.dumps({}))

        else:
            raise ValueError("Invalid cache method. Only mysql, sqlite, pickle allowed")

        # For sqlite and mysql, create a table if it doesn't exist in the database
        if self.cache_method in ('sqlite', 'mysql'):
            con, cur = self._get_db()

            cur.execute(
                f"""
            CREATE TABLE IF NOT EXISTS  {self.db_table}  (
                category	TEXT PRIMARY KEY NOT NULL UNIQUE,
                latest_circular_id	INTEGER
            )
            """
            )
            con.commit()
            con.close()

        if self.get_cache() is None:
            self.check()

    def _send_api_request(self, endpoint: str, fallback=False) -> dict:
        try:
            api_url = self.fallback_api_url if fallback else self.api_url
            if requests is None:
                raise ImportError("requests is required to send API requests")
            request = requests.get(api_url + endpoint, timeout=5)
            json = request.json()
        except requests.exceptions.ConnectionError:
            if fallback:
                raise ConnectionError("Both API URLs are down")
            if self.fallback_api_url:
                warnings.warn("API is down. Trying fallback API URL")
                return self._send_api_request(endpoint, True)
            else:
                raise ConnectionError("API is down")

        return json['data']

    def _get_db(self):
        if self.cache_method == 'mysql':
            if mysql_connector is None:
                raise ImportError("mysql.connector is required for mysql cache_method")
            con = mysql_connector.connect(
                host=self.db_host, port=int(self.db_port), password=self.db_password,
                user=self.db_user, database=self.db_name,
            )
            cur = con.cursor()

        elif self.cache_method == 'sqlite':
            con = sqlite3.connect(os.path.join(self.db_path, f"{self.db_name}.db"))
            cur = con.cursor()
        else:
            raise ValueError("Method not supported for this cache method")

        return con, cur


    # Method to retrieve cache from the database
    def get_cache(self) -> int | None:
        res = None
        if self.cache_method in ('sqlite', 'mysql'):
            con, cur = self._get_db()

            if self.cache_method == 'mysql':
                cur.execute(f"SELECT latest_circular_id FROM {self.db_table} WHERE category = %s", (self._category_key,))
            else:
                cur.execute(f"SELECT latest_circular_id FROM {self.db_table} WHERE category = ?", (self._category_key,))

            row = cur.fetchone()
            con.close()

            if row is not None:
                res = row[0]

        elif self.cache_method == 'pickle':
            try:
                with open(self.cache_file, 'rb') as f:
                    data = pickle.load(f)
            except (EOFError, FileNotFoundError):
                data = None

            if isinstance(data, dict):
                res = data.get(self._category_key)
            else:
                # backward compatibility: single int value
                res = data
        else:
            raise ValueError("Method not supported for this cache method")

        if res is not None:
            try:
                res = int(res)
            except (TypeError, ValueError):
                res = None

        return res

    def _set_cache(self, circular_id: int):

        if self.cache_method in ('sqlite', 'mysql'):
            con, cur = self._get_db()
            # cur.execute(f"DELETE FROM {self.db_table} WHERE category = ?", (self.cate))

            if self.cache_method == 'mysql':
                query = f"REPLACE INTO {self.db_table} (category, latest_circular_id) VALUES (%s, %s)"
                cur.execute(query, (self._category_key, circular_id,))
            else:
                query = f"REPLACE INTO {self.db_table} (category, latest_circular_id) VALUES (?, ?)"
                cur.execute(query, (self._category_key, circular_id,))

            con.commit()
            con.close()

        elif self.cache_method == 'pickle':
            # keep a dict of category_key -> circular_id
            data = {}
            try:
                if os.path.exists(self.cache_file):
                    with open(self.cache_file, 'rb') as f:
                        existing = pickle.load(f)
                        if isinstance(existing, dict):
                            data = existing
                        elif isinstance(existing, int):
                            data = {'__ALL__': existing}
            except Exception:
                data = {}

            data[self._category_key] = circular_id
            with open(self.cache_file, 'wb') as f:
                f.write(pickle.dumps(data))


    # Method to check for new circulars
    def check(self) -> list[dict] | list:

        if (cached_circular_id := self.get_cache()) is not None:
            res = self._send_api_request(f'new-circulars/{cached_circular_id}')
        else:
            res = self._send_api_request('new-circulars/')
        # it's sorted in descending order

        # If the API found new circulars
        if len(res) > 0:
            # If this circular-checker is meant for only one category,
            # filter first so we can set a per-category cache based on that category only
            if self.category is not None:
                def _matches_category(c):
                    cat = c.get('category')
                    if isinstance(self.category, int):
                        try:
                            return int(cat) == self.category
                        except Exception:
                            return False
                    else:
                        return str(cat) == str(self.category)

                filtered = [c for c in res if _matches_category(c)]

                if cached_circular_id is None:
                    # initial run: initialize cache for this category and don't return historical items
                    if filtered:
                        try:
                            self._set_cache(filtered[0]['id'])
                        except Exception:
                            pass
                        return []
                    else:
                        try:
                            self._set_cache(res[0]['id'])
                        except Exception:
                            pass
                        return []

                # subsequent runs: if there are matching items, update cache to newest matching id and return them
                if filtered:
                    try:
                        self._set_cache(filtered[0]['id'])
                    except Exception:
                        pass

                    for circular in filtered:
                        del circular['category']

                    filtered.reverse()
                    return filtered

                # no new items for this category
                return []

            # global checker (no specific category)
            try:
                self._set_cache(res[0]['id'])
            except Exception:
                pass

            if cached_circular_id is None:
                return []

            res.reverse()
        return res


    # Close connections when object is deleted
    # def __del__(self):
    #
    #     if hasattr(self, '_con'):
    #         self._con.close()


class CircularCheckerGroup:
    def __init__(self, *circular_checkers: CircularChecker):
        self._checkers = []

        # Add each checker to self._checkers
        for checker in circular_checkers:
            if type(checker) is not CircularChecker:
                raise ValueError("Invalid CircularChecker Object")
            self._checkers.append(checker)


    # Method to add a circular checker to this group
    def add(self, checker: CircularChecker, *circular_checkers: CircularChecker):
        self._checkers.append(checker)

        for checker in circular_checkers:
            if type(checker) is not CircularChecker:
                raise ValueError("Invalid CircularChecker Object")
            self._checkers.append(checker)

    # Method to create a circular checker and add it to the group
    def create(self, category, url: str = "https://bpsapi.rajtech.me/", cache_method=None, **kwargs):
        checker = CircularChecker(category, api_url=url, cache_method=cache_method, **kwargs)
        self._checkers.append(checker)

    # Method to check for new circulars in each one of the checkers
    def check(self) -> dict[list[dict], ...] | dict:
        return_dict = {}
        for checker in self._checkers:
            return_dict[checker.category] = checker.check()
        return return_dict

    #
    # def __del__(self):
    #     for checker in self._checkers:
    #         del checker
