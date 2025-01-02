# kenobiDB
kenobiDB is a small document based database (abstraction) supporting very simple usage including insertion, update, removal and search. It uses SQLite, is thread safe, process safe, and atomic. kenobiDB also supports basic asynchronous operation. Check out the [website](http://patx.github.io/kenobi/) or view the project on [PyPI](https://pypi.org/project/kenobi/).

## Use it
* You can install kenobiDB using the pip command  `pip install kenobi`.
* For the latest version just copy and paste the `kenobi.py` file into your working directory.

## kenobiDB is fun!
```
>>> from kenobi import KenobiDB

>>> db = KenobiDB('example.db')

>>> db.insert({'name': 'Obi-Wan', 'color': 'blue'})
    True

>>> db.search('color', 'blue')
    [{'name': 'Obi-Wan', 'color': 'blue'}]
```

# Overview/Usage

## Initialization and Setup:
* The database is initialized with a specified file. If the file does not exist, it is created. SQLite is used for storage, and the database ensures the necessary table and indices are created.
```
db = KenobiDB('example.db')
```

## Concurrency:
* The class uses `RLock` for thread safety.
* A `ThreadPoolExecutor` with a maximum of 5 workers is used to handle concurrent operations.
* The `execute_async` method allows for asynchronous execution of functions using the thread pool.
```
future = db.execute_async(insert_document, db, document)
```

## Basic Operations:
* Insert: Add a single document or multiple documents to the database.
```
db.insert({'name': 'Obi-Wan', 'color': 'blue'})
db.insert_many([{'name': 'Anakin', 'color': 'red'}, {'name': 'Yoda', 'color': 'green'}])
```

* Remove: Remove documents matching a specific key-value pair.
```
db.remove('name', 'Obi-Wan')
```

* Update: Update documents matching a specific key-value pair with new data.
```
db.update('name', 'Anakin', {'color': 'dark'})
```

* Purge: Remove all documents from the database.
```
db.purge()
```

## Search Operations:
* All: Retrieve all documents with optional pagination.
```
db.all(limit=10, offset=0)
db.all() # No pagination
```

* Search: Retrieve documents matching a specific key-value pair with optional pagination.
```
db.search('color', 'blue')
```

* Find Any: Retrieve documents where a key matches any value in a list.
```
db.find_any('color', ['blue', 'red'])
```

* Find All: Retrieve documents where a key matches all values in a list.
```
db.find_all('color', ['blue', 'red'])
```

## Asynchronous Execution:
* The `execute_async` method allows for asynchronous execution of functions using the thread pool.
```
def insert_document(db, document):
    db.insert(document)
future = db.execute_async(insert_document, db, {'name': 'Luke', 'color': 'green'})
```

## Thread Pool Management:
   * The `close` method shuts down the thread pool executor.
```
db.close()
```


