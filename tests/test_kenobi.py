"""
.. moduleauthor:: Harrison Erd <harrisonerd@gmail.com>

Not slow

.. code-block:: shell

   python -m coverage run --source='kenobi.kenobi' -m pytest \
   --showlocals -m "not slow" tests/test_kenobi.py && coverage report \
   --data-file=.coverage --include="**/kenobi.py"

All tests

.. code-block:: shell

   python -m coverage run --source='kenobi.kenobi' -m pytest \
   --showlocals tests/test_kenobi.py && coverage report \
   --data-file=.coverage --include="**/kenobi.py"

"""

import time
from contextlib import nullcontext as does_not_raise
from functools import partial

import pytest

testdata_insert_single_document = (
    (
        "insert",
        {"key": "value"},
        does_not_raise(),
        1,
        {"key": "value"},
    ),
    (
        "insert_many",
        [{"key": "value1"}, {"key": "value2"}],
        does_not_raise(),
        2,
        [{"key": "value1"}, {"key": "value2"}],
    ),
    (
        "insert",
        0.1234,
        pytest.raises(TypeError),
        0,
        {},
    ),
    (
        "insert",
        None,
        pytest.raises(TypeError),
        0,
        {},
    ),
    (
        "insert_many",
        [0.1234, 0.1234],
        pytest.raises(TypeError),
        0,
        [],
    ),
)

ids_insert_single_document = (
    "Single document",
    "Multiple documents",
    "document invalid unsupported type",
    "document invalid None",
    "Multiple documents unsupported types",
)


@pytest.mark.parametrize(
    "meth, document, expectation, result_count_expected, document_expected",
    testdata_insert_single_document,
    ids=ids_insert_single_document,
)
def test_insert_single_document(
    meth,
    document,
    expectation,
    result_count_expected,
    document_expected,
    create_db,
):
    """Test inserting a single document."""
    # pytest -vv --showlocals --log-level INFO -k "test_insert_single_document" tests
    # pytest -vv --showlocals --log-level INFO tests/test_kenobi.py::test_insert_single_document\[Single\ document\]
    # prepare
    db = create_db()
    if hasattr(db, meth):
        fcn = getattr(db, meth)
        # insert document(s)
        with expectation:
            fcn(document)

    # act
    results = db.all()
    # verify
    result_count_actual = len(results)
    assert result_count_actual == result_count_expected
    if isinstance(expectation, does_not_raise):
        # If fail :code:`len(results) == 0`. results[0] --> IndexError
        # document_actual = results[0]
        if isinstance(document, dict):
            assert document_expected in results
        elif isinstance(document, list):
            for d_document in document:
                assert d_document in results
        else:
            pass


testdata_remove_document = (
    (
        {"key": "value"},
        "key",
        "value",
        does_not_raise(),
        0,
    ),
    (
        {"key": "value"},
        None,
        "value",
        pytest.raises(ValueError),
        1,
    ),
    (
        {"key": "value"},
        0.12345,
        "value",
        pytest.raises(ValueError),
        1,
    ),
    (
        {"key": "value"},
        "key",
        None,
        pytest.raises(ValueError),
        1,
    ),
)
ids_remove_document = (
    "remove one document",
    "key None",
    "key unsupported type",
    "value None",
)


@pytest.mark.parametrize(
    "document, query_key, query_val, expectation, results_count_expected",
    testdata_remove_document,
    ids=ids_remove_document,
)
def test_remove_document(
    document, query_key, query_val, expectation, results_count_expected, create_db
):
    """Test removing a document by key:value."""
    # pytest -vv --showlocals --log-level INFO -k "test_remove_document" tests
    # prepare
    db = create_db()
    db.insert(document)
    # act
    with expectation:
        db.remove(query_key, query_val)
    # verify
    results = db.all()
    results_count_actual = len(results)
    assert results_count_actual == results_count_expected


testdata_update_document = (
    (
        {"id": 1, "key": "value"},
        {"key": "new_value"},
        "id",
        1,
        "key",
        "new_value",
        does_not_raise(),
        1,
        True,
    ),
    (
        {"id": 1, "key": "value"},
        {"key": "new_value"},
        None,
        1,
        "key",
        "value",
        pytest.raises(ValueError),
        1,
        False,
    ),
    (
        {"id": 1, "key": "value"},
        {"key": "new_value"},
        "id",
        None,
        "key",
        "value",
        pytest.raises(ValueError),
        1,
        False,
    ),
    (
        {"id": 1, "key": "value"},
        {"key": "new_value"},
        "id",
        2,
        "key",
        "value",
        does_not_raise(),
        1,
        False,
    ),
)
ids_update_document = (
    "Update a document",
    "id_field None ValueError",
    "id_val None ValueError",
    "could not update nonexistent document",
)


@pytest.mark.parametrize(
    (
        "document, updated_fields, id_field, id_val, val_key, "
        "val_expected, expectation, results_count_expected, is_success_expected"
    ),
    testdata_update_document,
    ids=ids_update_document,
)
def test_update_document(
    document,
    updated_fields,
    id_field,
    id_val,
    val_key,
    val_expected,
    expectation,
    results_count_expected,
    is_success_expected,
    create_db,
):
    """Test updating a document by key:value."""
    # pytest -vv --showlocals --log-level INFO -k "test_update_document" tests
    # prepare
    db = create_db()
    db.insert(document)
    # act
    with expectation:
        is_success_actual = db.update(id_field, id_val, updated_fields)
    if isinstance(expectation, does_not_raise):
        assert is_success_actual is is_success_expected
    # verify
    results = db.all()
    results_count_actual = len(results)
    assert results_count_actual == results_count_expected
    val_actual = results[0][val_key]

    assert val_actual == val_expected


def test_purge_database(create_db):
    """Test purging all documents from the database."""
    # pytest -vv --showlocals --log-level INFO -k "test_purge_database" tests
    documents = [{"key": "value1"}, {"key": "value2"}]
    results_count_expected = 0
    # prepare
    db = create_db()
    db.insert_many(documents)
    # act
    db.purge()
    # verify
    results = db.all()
    results_count_actual = len(results)
    assert results_count_actual == results_count_expected


testdata_search_by_key_value = (
    (
        [{"key": "value1"}, {"key": "value2"}],
        "key",
        "value1",
        does_not_raise(),
        1,
    ),
    (
        [{"key": "value1"}, {"key": "value2"}],
        None,
        "value1",
        pytest.raises(ValueError),
        1,
    ),
    (
        [{"key": "value1"}, {"key": "value2"}],
        0.2345,
        "value1",
        pytest.raises(ValueError),
        1,
    ),
)
ids_search_by_key_value = (
    "successful query",
    "query_key None",
    "query_key unsupported type",
)


@pytest.mark.parametrize(
    "documents, query_key, query_val, expectation, results_count_expected",
    testdata_search_by_key_value,
    ids=ids_search_by_key_value,
)
def test_search_by_key_value(
    documents,
    query_key,
    query_val,
    expectation,
    results_count_expected,
    create_db,
):
    """Test searching documents by key:value."""
    # pytest -vv --showlocals --log-level INFO -k "test_search_by_key_value" tests

    # prepare
    db = create_db()
    db.insert_many(documents)
    # act
    with expectation:
        results = db.search(query_key, query_val)
    # verify
    if isinstance(expectation, does_not_raise):
        results_count_actual = len(results)
        assert results_count_actual == results_count_expected
        actual_doc_0 = results[0]
        expected_doc_0 = documents[0]
        assert actual_doc_0 == expected_doc_0


testdata_find_any = (
    (
        [{"key": "value1"}, {"key": "value2"}, {"key": "value3"}],
        "key",
        ["value1", "value3"],
        does_not_raise(),
        2,
        (0, 2),
    ),
    (
        [{"key": "value1"}, {"key": "value2"}, {"key": "value3"}],
        None,
        ["value1", "value3"],
        does_not_raise(),
        0,
        (),
    ),
    (
        [{"key": "value1"}, {"key": "value2"}, {"key": "value3"}],
        0.1234,
        ["value1", "value3"],
        does_not_raise(),
        0,
        (),
    ),
    (
        [{"key": "value1"}, {"key": "value2"}, {"key": "value3"}],
        "key",
        [None, None],
        does_not_raise(),
        0,
        (),
    ),
    (
        [{"key": "value1"}, {"key": "value2"}, {"key": "value3"}],
        "key",
        [0.1234, 0.1234],
        does_not_raise(),
        0,
        (),
    ),
    pytest.param(
        [{"key": "value1"}, {"key": "value2"}, {"key": "value3"}],
        "key",
        {0.1234, 0.1234},
        pytest.raises(TypeError),
        0,
        (),
        marks=pytest.mark.xfail,
    ),
    pytest.param(
        [{"key": "value1"}, {"key": "value2"}, {"key": "value3"}],
        "key",
        (0.1234, 0.1234),
        pytest.raises(TypeError),
        0,
        (),
        marks=pytest.mark.xfail,
    ),
)
ids_find_any = (
    "successful query",
    "key None",
    "key unsupported type",
    "query vals list None None",
    "query vals list both unsupported type",
    "query vals set both unsupported type BUG",
    "query vals tuple both unsupported type BUG",
)


@pytest.mark.parametrize(
    (
        "documents, query_key, query_vals, expectation, "
        "results_count_expected, t_documents_idxs"
    ),
    testdata_find_any,
    ids=ids_find_any,
)
def test_find_any(
    documents,
    query_key,
    query_vals,
    expectation,
    results_count_expected,
    t_documents_idxs,
    create_db,
):
    """Test finding documents where a key matches any value in a list."""
    # pytest -vv --showlocals --log-level INFO -k "test_find_any" tests
    # prepare
    db = create_db()
    db.insert_many(documents)

    # act
    with expectation:
        results = db.find_any(query_key, query_vals)
    # verify
    if isinstance(expectation, does_not_raise):
        results_count_actual = len(results)
        assert results_count_actual == results_count_expected
        for doc_idx in t_documents_idxs:
            assert documents[doc_idx] in results


testdata_find_all = (
    (
        [
            {"key": ["value1", "value2"]},
            {"key": ["value1"]},
            {"key": ["value2", "value3"]},
        ],
        "key",
        ["value1", "value2"],
        does_not_raise(),
        1,
        (0,),
    ),
    pytest.param(
        [
            {"key": ["value1", "value2"]},
            {"key": ["value1"]},
            {"key": ["value2", "value3"]},
        ],
        "key",
        {"value1", "value2"},
        pytest.raises(TypeError),
        1,
        (),
        marks=pytest.mark.xfail,
    ),
    pytest.param(
        [
            {"key": ["value1", "value2"]},
            {"key": ["value1"]},
            {"key": ["value2", "value3"]},
        ],
        "key",
        ("value1", "value2"),
        pytest.raises(TypeError),
        1,
        (),
        marks=pytest.mark.xfail,
    ),
)
ids_find_all = (
    "successful query",
    "query vals set both unsupported type BUG",
    "query vals tuple both unsupported type BUG",
)


@pytest.mark.parametrize(
    (
        "documents, query_key, query_vals, expectation, "
        "results_count_expected, t_documents_idxs"
    ),
    testdata_find_all,
    ids=ids_find_all,
)
def test_find_all(
    documents,
    query_key,
    query_vals,
    expectation,
    results_count_expected,
    t_documents_idxs,
    create_db,
):
    """Test finding documents where a key matches all values in a list."""
    # pytest -vv --showlocals --log-level INFO -k "test_find_all" tests
    # prepare
    db = create_db()
    db.insert_many(documents)
    # act
    with expectation:
        results = db.find_all(query_key, query_vals)
    # verify
    if isinstance(expectation, does_not_raise):
        results_count_actual = len(results)
        assert results_count_actual == results_count_expected
        for doc_idx in t_documents_idxs:
            assert results[0] == documents[doc_idx]


def test_pagination_all(create_db):
    """Test paginated retrieval of all documents."""
    # pytest -vv --showlocals --log-level INFO -k "test_pagination_all" tests
    documents = [{"key": f"value{i}"} for i in range(10)]
    results_count_expected = 5

    # prepare
    db = create_db()
    db.insert_many(documents)
    # act
    results = db.all(limit=5, offset=0)
    # verify
    results_count_actual = len(results)
    assert results_count_actual == results_count_expected
    assert results == documents[:5]


def test_pagination_search(create_db):
    """Test paginated search by key:value."""
    # pytest -vv --showlocals --log-level INFO -k "test_pagination_search" tests
    documents = [{"key": f"value{i}"} for i in range(10)]
    results_count_expected = 1

    # prepare
    db = create_db()
    db.insert_many(documents)
    # act
    results = db.search("key", "value1", limit=1, offset=0)
    # verify
    results_count_actual = len(results)
    assert results_count_actual == results_count_expected
    assert results[0] == {"key": "value1"}


def db_task(fcn, doc):
    """Function usable by thread pool executor"""
    fcn(doc)


testdata_concurrent_inserts = (
    (
        [{"key": f"value{i}"} for i in range(50)],
        does_not_raise(),
        50,
    ),
)
ids_concurrent_inserts = ("successful concurrent inserts",)


@pytest.mark.parametrize(
    "documents, expectation, results_count_expected",
    testdata_concurrent_inserts,
    ids=ids_concurrent_inserts,
)
def test_concurrent_inserts(documents, expectation, results_count_expected, create_db):
    """Test concurrent inserts to ensure thread safety."""
    # pytest -vv --showlocals --log-level INFO -k "test_concurrent_inserts" tests
    # prepare
    db = create_db()
    #    pytest doesn't support inner functions
    insert_task = partial(db_task, db.insert)

    # act
    with expectation:
        with db.executor as executor:
            executor.map(insert_task, documents)
    # verify
    results = db.all()
    results_count_actual = len(results)
    assert results_count_actual == results_count_expected


def test_performance_bulk_insert(create_db):
    """Test the performance of bulk inserting a large number of documents."""
    # pytest -vv --showlocals --log-level INFO -k "test_performance_bulk_insert" tests
    documents = [{"key": f"value{i}"} for i in range(1000)]
    duration_max_expected = 5
    # prepare
    db = create_db()
    start_time = time.time()
    # act
    db.insert_many(documents)
    end_time = time.time()
    duration_actual = end_time - start_time
    # verify
    assert duration_actual < duration_max_expected, "Bulk insert took too long"


def test_safe_query_handling(create_db):
    """Test safe handling of potentially harmful input to prevent SQL injection."""
    # pytest -vv --showlocals --log-level INFO -k "test_safe_query_handling" tests
    document = {"key": "value"}
    results_count_expected = 0
    # prepare
    db = create_db()
    db.insert(document)
    # act
    results = db.search("key", "value OR 1=1")
    # verify
    results_count_actual = len(results)
    assert (
        results_count_actual == results_count_expected
    ), "Unsafe query execution detected"


@pytest.mark.slow
def test_large_dataset(create_db):
    """Stress test: Insert and retrieve a large number of documents."""
    # pytest -vv --showlocals --log-level INFO -k "test_large_dataset" tests
    num_docs = 1_000_000
    documents = [{"key": f"value{i}"} for i in range(num_docs)]
    duration_1M_inserts_max = 300

    # prepare
    db = create_db()

    # Measure insertion performance
    start_time = time.time()
    db.insert_many(documents)
    end_time = time.time()
    duration_1M_inserts_actual = end_time - start_time

    # Ensure insertion is reasonably fast
    assert (
        duration_1M_inserts_actual < duration_1M_inserts_max
    ), "Inserting 1,000,000 documents took too long"
    msg_info = f"Inserted {num_docs} documents in {duration_1M_inserts_actual} seconds"
    print(msg_info)

    # Measure retrieval performance
    start_time = time.time()
    all_docs = db.all(limit=num_docs)
    end_time = time.time()
    retrieval_duration_actual = end_time - start_time
    docs_count_actual = len(all_docs)

    # Ensure retrieval is correct and performant
    assert docs_count_actual == num_docs, "Not all documents were retrieved"
    assert (
        retrieval_duration_actual < duration_1M_inserts_max
    ), "Retrieving 1,000,000 documents took too long"
    msg_info = f"Retrieved {docs_count_actual} documents in {retrieval_duration_actual} seconds"
    print(msg_info)


testdata_malformed_json_in_update = (
    (
        {"id": 1, "key": "value"},
        pytest.raises(TypeError),
    ),
)
ids_malformed_json_in_update = ("Insert a malformed document",)


@pytest.mark.parametrize(
    "malformed_document, expectation",
    testdata_malformed_json_in_update,
    ids=ids_malformed_json_in_update,
)
def test_malformed_json_in_update(malformed_document, expectation, create_db):
    """Test handling malformed JSON in update."""
    # pytest -vv --showlocals --log-level INFO -k "test_malformed_json_in_update" tests
    # prepare
    db = create_db()
    db.insert(malformed_document)

    # Attempt to update with malformed JSON structure
    with expectation:
        db.update("id", 1, "not a dict")
