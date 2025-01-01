kenobiDB
========
kenobiDB is a small document based database supporting very simple usage
including insertion, update, removal and search. It useses YAML, is thread safe, process safe, and atomic. Check out
the `website <http://patx.github.io/kenobi/>`_ or view the project on
`PyPI <https://pypi.org/project/kenobi/>`_.

Use it
------
- You can install kenobiDB using the pip command ``pip install kenobi``.
- View API documentation `here <https://patx.github.io/kenobi/api.html>`_.
- You can see a `walk through <https://patx.github.io/kenobi/walk.html>`_ of all of kenobiDB's features.

See it in action
----------------
.. code-block:: python

    >>> from kenobi import KenobiDB

    >>> db = KenobiDB('example.yaml')

    >>> db.insert({'name': 'Obi-Wan', 'color': 'blue'})
    True

    >>> db.search('color', 'blue')
    [{'name': 'Obi-Wan', 'color': 'blue'}]
