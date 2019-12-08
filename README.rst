kenobiDB is simple document based database
``````````````````````````````````````````

::

    >>> from kenobi import KenobiDB
    
    >>> db = KenobiDB('example.yaml', auto_save=False)
    
    >>> db.insert({'name': 'user1', 'groups': ['user']})
    True
    
    >>> db.insert_many([{'name': 'user2', 'groups': ['admin', 'user']},
    {'name': 'user3', 'groups': ['sudo', 'user']}])
    True
    
    >>> db.all()
    [{'name': 'user1', 'groups': ['user']},
     {'name': 'user2', 'groups': ['admin', 'user']},
     {'name': 'user3', 'groups': ['sudo', 'user']}]
    
    >>> db.search('name', 'user1')
    [{'name': 'user1', 'groups': ['user']}]
    
    >>> db.find_any('groups', ['admin', 'sudo'])
    [{'name': 'user2', 'groups': ['admin', 'user']},
     {'name': 'user3', 'groups': ['sudo', 'user']}]
    
    >>> db.find_all('groups', ['admin', 'user'])
    [{'name': 'user2', 'groups': ['admin', 'user']}]
    
    >>> db.update('name', 'user1', {'groups': ['user', sudo', 'admin']})
    True
    
    >>> db.all()
    [{'name': 'user1', 'groups': ['user', 'sudo', 'admin']},
     {'name': 'user2', 'groups': ['admin', 'user']},
     {'name': 'user3', 'groups': ['sudo', 'user']}]
    
    >>> db.save_db()
    True
    
    >>> db.remove('name', 'user1')
    [{'name': 'user1', 'groups': ['user', 'sudo', 'admin']}]
    
    >>> db.all()
    [{'name': 'user2', 'groups': ['admin', 'user']},
     {'name': 'user3', 'groups': ['sudo', 'user']}]
    
    >>> db.purge()
    True
    
    >>> db.all()
    []
