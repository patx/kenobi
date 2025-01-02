# kenobiDB
KenobiDB is a document-based data store abstraction built over SQLite, offering a simple and efficient way to store and retrieve JSON-like data.
By abstracting away the complexity of SQL, it provides a flexible and secure environment for handling data with high performance. With built-in
thread safety, async execution, and basic indexing, KenobiDB ensures reliable and fast data management while maintaining the simplicity of a document store.
Ideal for small applications and prototypes, it combines the power of SQLite with the ease and flexibility of document-based storage. Check out
the [website](http://patx.github.io/kenobi/) or view the project on [PyPI](https://pypi.org/project/kenobi/).

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
db.all(limit=10, offset=0) # With pagination

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

## Concurrency and Asynchronous Execution:
* The class uses `RLock` for thread safety.
* A `ThreadPoolExecutor` with a maximum of 5 workers is used to handle concurrent operations.
* The `execute_async` method allows for asynchronous execution of functions using the thread pool.
```
def insert_document(db, document):
    db.insert(document)
future = db.execute_async(insert_document, db, {'name': 'Luke', 'color': 'green'})
```

   * The `close` method shuts down the thread pool executor.
```
db.close()
```

