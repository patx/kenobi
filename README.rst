kenobiDB is simple document based database
``````````````````````````````````````````

::

    >>> from kenobi import KenobiDB

    >>> db = KenobiDB('database.json', auto_save=False)

    >>> db.insert({'name': 'user1', 'groups': ['user']})
    >>> db.insert({'name': 'user2', 'groups': ['admin', 'user']})
    >>> db.insert({'name': 'user3', 'groups': ['sudo', 'user']})

    >>> db.search('name1', 'user1')
    [{'name': 'user1', 'groups': ['user']}]

    >>> db.find_any('groups', ['admin', 'sudo'])
    [{'name': 'user2', 'groups': ['admin', 'user']},
     {'name': 'user3', 'groups': ['sudo', 'user']}]

    >>> db.find_all('groups', ['admin', 'user'])
    [{'name': 'user2', 'groups': ['admin', 'user']}]

    >>>> db.save_db()
    True
