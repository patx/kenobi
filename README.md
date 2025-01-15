
![kenobiDB](https://patx.github.io/kenobi/logo.png)


KenobiDB is a document-based data store abstraction built on Python’s `sqlite3`, offering a simple and efficient way to manage JSON-like data. Its API is highly similar to MongoDB’s, providing familiar operations for insertion, updates, and searches—without the need for a server connection. By removing the complexity of SQL, KenobiDB delivers a secure, high-performance environment with built-in thread safety, async execution, and basic indexing while leveraging the simplicity of a document-based database. Perfect for small applications and prototypes, KenobiDB combines SQLite’s lightweight, serverless setup with the flexibility of document-based storage. Check out the [website](http://patx.github.io/kenobi/) or view the project on [PyPI](https://pypi.org/project/kenobi/).

## Features

- Lightweight and serverless setup using SQLite.
- MongoDB-like API for familiar operations.
- Supports key-value pair searching instead of complex SQL queries.
- Thread safety with `RLock`.
- Asynchronous execution with `ThreadPoolExecutor`.
- Built-in basic indexing for efficient searches.
- Super easy integration.
- Solid performance

## Installation

You can install KenobiDB using pip:

```bash
pip install kenobi
```

Alternatively, for the latest version, copy and paste the `kenobi.py` file into your working directory.

## Quick Start

```python
from kenobi import KenobiDB

db = KenobiDB('example.db')

db.insert({'name': 'Obi-Wan', 'color': 'blue'})
# Output: True

db.search('color', 'blue')
# Output: [{'name': 'Obi-Wan', 'color': 'blue'}]
```

## Overview/Usage

### Initialization and Setup

Initialize the database with a specified file. If the file does not exist, it will be created. SQLite is used for storage, and the database ensures the necessary table and indices are created.

```python
db = KenobiDB('example.db')
```

### Basic Operations

#### Insert

Add a single document or multiple documents to the database.

```python
db.insert({'name': 'Obi-Wan', 'color': 'blue'})

db.insert_many([
    {'name': 'Anakin', 'color': 'red'},
    {'name': 'Yoda', 'color': 'green'}
])
```

#### Remove

Remove documents matching a specific key-value pair.

```python
db.remove('name', 'Obi-Wan')
```

#### Update

Update documents matching a specific key-value pair with new data.

```python
db.update('name', 'Anakin', {'color': 'dark'})
```

#### Purge

Remove all documents from the database.

```python
db.purge()
```

### Search Operations

#### All

Retrieve all documents with optional pagination.

```python
db.all(limit=10, offset=0)  # With pagination

db.all()  # No pagination
```

#### Search

Retrieve documents matching a specific key-value pair with optional pagination.

```python
db.search('color', 'blue')
```

#### Glob Search

Retrieve documents using regex.

```python
db.search_pattern('color', 'b*')
```

#### Find Any

Retrieve documents where a key matches any value in a list.

```python
db.find_any('color', ['blue', 'red'])
```

#### Find All

Retrieve documents where a key matches all values in a list.

```python
db.find_all('color', ['blue', 'red'])
```

### Concurrency and Asynchronous Execution

KenobiDB uses `RLock` for thread safety and `ThreadPoolExecutor` with a maximum of 5 workers for concurrent operations.

#### Asynchronous Execution

Use the `execute_async` method to run functions asynchronously.

```python
def insert_document(db, document):
    db.insert(document)

future = db.execute_async(insert_document, db, {'name': 'Luke', 'color': 'green'})
```

#### Close

Shut down the thread pool executor.

```python
db.close()
```

## Performance and Scalability

KenobiDB is optimized to handle large datasets efficiently, leveraging SQLite's lightweight architecture and advanced features like WAL mode and batch inserts. Here are some benchmarks showcasing KenobiDB's performance:

- **1,000,000 Documents**:

  - **Insertion**: Completed in approximately **10 seconds**.
  - **Retrieval**: Completed in approximately **3 seconds**.
  - **Total Time (Insert + Retrieve)**: \~13 seconds.

- **10,000,000 Documents**:

  - **Insertion**: Completed in approximately **120 seconds**.
  - **Retrieval**: Completed in approximately **10 seconds**.
  - **Total Time (Insert + Retrieve)**: \~130 seconds.

These benchmarks were achieved on a StarLabs StarLite Mk IV (Quad-Core Intel® Pentium® Silver N5030 CPU @ 1.10GHz w/ 8 GB memory and 240 GB storage. To see times on your machine you can run the unit tests.

### Key Factors Contributing to Performance:

- **Batch Inserts**: Using `executemany` minimizes transaction overhead.
- **Write-Ahead Logging (WAL) Mode**: Improves write concurrency and throughput.
- **Efficient JSON Handling**: Streamlined serialization and deserialization processes.
- While KenobiDB performs exceptionally well for small to medium datasets, it remains designed for lightweight use cases and may not be suitable for enterprise-scale applications requiring high levels of concurrency.
- While not as fast as pure SQLite you can easily store documents, you get thread saftey/async, and other features built in ready to go!

## Testing and Contributions

Contributions are welcome! To test the library:

1. Clone the repository.
2. Report issues as you encounter them.
3. Run the unittests.

Feel free to open issues or submit pull requests on the [GitHub repository](https://github.com/patx/kenobi).

## Limitations

KenobiDB is designed for small-scale applications and prototypes. While it provides excellent performance for most operations, it is not intended to replace full-fledged databases for high-scale or enterprise-level applications for that you should use MongoDB.
