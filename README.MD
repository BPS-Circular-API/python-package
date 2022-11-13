# pybpsapi - Python bindings for the BPS Circular API

What is `pybpsapi`?

`pybpsapi` is a Python library that allows you to interact with the BPS Circular API. It is written in Python using the requests library.
This package also features a well maintained and tried and tested circular-checking system to check for new circulars.

## Installation

`pybpsapi` can be installed using pip:

```bash
pip install pybpsapi
```

## Documentation

**The full documentation for the package can be found [here](https://bpsapi.rajtech.me/docs/category/python-package).**

### The `API` class

The `API` class is the main class of the package. It is used to interact with the five endpoints of the BPS Circular API.

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

[//]: # (### The `CircularChecker` class)