# pybpsapi - Python bindings for the BPS Circular API

What is `pybpsapi`?

`pybpsapi` is a Python library that allows you to interact with the BPS Circular API. It is written in Python using the requests library.
This package also features a well maintained and tried and tested circular-checking system to check for new circulars.

## Installation

`pybpsapi` can be installed using pip:

```bash
pip install pybpsapi
```

## Contributing

Contributions are welcome! Please feel free to open an issue or a pull request on the [GitHub repository](https://bpsapi.rajtech.me/r/


## Documentation

**The full documentation for the package can be found [here](https://bpsapi.rajtech.me/docs/category/python-package).**

### The `API` class

The `API` class is the main class of the package. It is used to interact with the five endpoints of the BPS Circular API.

---

#### `API.latest(category: str | int)` 

This method returns the latest circulars from the BPS Circular API.

```python
# Import the module
import pybpsapi

# Create an instance of the API class
api = pybpsapi.API()

# Get the latest circular from the `general` category
latest1 = api.latest(category="general")

# or you could use the category ID
latest2 = api.latest(category=41)

# You can also get the cached version of the latest circular
latest3 = api.latest(category="general", cached=True)


print(latest1, latest2)
```

---

#### `API.list(category: str | int)`

This method returns a list of all the circulars in a category.

```python
# Import the module
import pybpsapi

# Create an instance of the API class
api = pybpsapi.API()

# Get the list of all the circulars in the `general` category
list1 = api.list(category="general")

# or you could use the category ID
list2 = api.list(category=41)

print(list1, list2)
```

---

#### `API.search(query: str | int)`

This method returns a list of the most similar circular that matches the search query.

```python
# Import the module
import pybpsapi

# Create an instance of the API class
api = pybpsapi.API()

# Get the list of all the circulars in the `general` category
search1 = api.search(query="mobile")

# or you could use the circular ID
search2 = api.search(query=1216)

print(search1, search2)
```

---

#### `API.getpng(url: str)`
This method returns the PNG image(es) of the circular.

```python
# Import the module
import pybpsapi

# Create an instance of the API class
api = pybpsapi.API()

# or you could use the circular URL
png1 = api.getpng(url="https://bpsdoha.com/circular/category/38-circular-ay-2022-23?download=1215")

print(png1)
```

### The `CircularChecker` class

The `CircularChecker` class is a bit more complicated than the `API` class. It is used to check for new circulars in a category.

#### Parameters

- `category` - The category to check for new circulars. Can be a category name (general|ptm|exam) or a category ID.
- `url` (optional) - The BPS API URL to use. Defaults to `https://bpsapi.rajtech.me/v1`.
- `cache_method` (optional) - The method to use to cache the latest circular. Can be `None` for memory, `pickle` to use a `.pickle` file, or `database` for a local SQLITE3 Database. Defaults to `memory`.
- `debug` (optional) - Whether to enable debug mode. This enables access to the `set_cache` and `refresh cache` methods. Defaults to `False`.

##### Keyword Arguments


The following keyword arguments must be passed when using the `database` cache method.
- `db_name` - The name of the database to use. 
- `db_path` - The path to the database. 
- `db_table` - The name of the table to use. 

The following keyword arguments must be passed when using the `pickle` cache method.
- `pickle_path` - The path to the pickle file.
- `pickle_name` - The name of the pickle file.


---


#### Initial `CircularChecker` setup

```python
# Import the module
import pybpsapi

# A minimal instance of the CircularChecker class. Stores the cache in memory.
checker = pybpsapi.CircularChecker(category="general")

# An instance of the CircularChecker class that stores the cache in a pickle file.
checker2 = pybpsapi.CircularChecker(category="general", cache_method="pickle", pickle_path=".", pickle_name="cache.pickle")

# An instance of the CircularChecker class that stores the cache in a SQLITE3 database. The database must be created before using this, but the table will be created automatically.
checker3 = pybpsapi.CircularChecker(category="general", cache_method="database", db_name="cache.db", db_path=".", db_table="cache")
```

---

#### `CircularChecker.check()`

This method checks for new circulars in the category. It returns a list of the new circular(s), if any.

```python
# Import the module
import pybpsapi

# Create an instance of the CircularChecker class
checker = pybpsapi.CircularChecker(category="general")

# Check for new circulars
new_circulars = checker.check()

print(new_circulars)
```

---


#### `CircularChecker.get_cache()`

This method returns the current cache of the CircularChecker instance.

```python
# Import the module
import pybpsapi

# Create an instance of the CircularChecker class
checker = pybpsapi.CircularChecker(category="general")

# Get the current cache
cache = checker.get_cache()

print(cache)
```

---

#### `CircularChecker.set_cache(data: dict, title: str = "circular_list")`

This method sets the cache of the CircularChecker instance. This method is only available when `debug` is set to `True`.

The `data` parameter is the actual data to set as the cache.   
The `title` parameter is the title of the circular list. This is only used when using the `database` cache method. Defaults to `circular_list`.


```python
# Import the module
import pybpsapi

# Create an instance of the CircularChecker class
checker = pybpsapi.CircularChecker(category="general", debug=True)

# Set the cache
checker.set_cache(data={...})
```

---

#### `CircularChecker.refresh_cache()`

This method refreshes the cache of the CircularChecker instance. This method is only available when `debug` is set to `True`.

```python
# Import the module
import pybpsapi

# Create an instance of the CircularChecker class
checker = pybpsapi.CircularChecker(category="general", debug=True)

# Refresh the cache
checker.refresh_cache()
```


### The `CircularCheckerGroup` class

The `CircularCheckerGroup` class is used to check for new circulars in multiple categories at once.

#### Parameters

- `*args` - Premade `CircularChecker` objects can be directly passed to the `CircularCheckerGroup` class.

#### Setup

```python
# Import the module
import pybpsapi

# Create an instance of the CircularChecker class
checker = pybpsapi.CircularChecker(category="general")
checker2 = pybpsapi.CircularChecker(category="ptm")

# Create an instance of the CircularCheckerGroup class
checker_group = pybpsapi.CircularCheckerGroup(checker, checker2)
```

or, you could use the `add` method to add `CircularChecker` objects to the `CircularCheckerGroup` object.

```python
# Import the module
import pybpsapi

# Create an instance of the CircularChecker class
checker = pybpsapi.CircularChecker(category="general")
checker2 = pybpsapi.CircularChecker(category="ptm")

# Create an instance of the CircularCheckerGroup class
checker_group = pybpsapi.CircularCheckerGroup()

# Add the CircularChecker object to the CircularCheckerGroup object
checker_group.add(checker)
checker_group.add(checker2)
```


### The `CircularCheckerGroup.check()`

This method checks for new circulars in all the categories in the `CircularCheckerGroup` object. It returns a list of the new circular(s), if any.

```python
# Import the module
import pybpsapi

# Create an instance of the CircularChecker class
checker = pybpsapi.CircularChecker(category="general")
checker2 = pybpsapi.CircularChecker(category="ptm")

# Create an instance of the CircularCheckerGroup class
checker_group = pybpsapi.CircularCheckerGroup(checker, checker2)

# Check for new circulars
new_circulars = checker_group.check()
```

The returned variable will be a `dict` with each key being the name or id of the category with the list inside it.