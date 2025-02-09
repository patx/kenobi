"""
.. moduleauthor:: Harrison Erd <harrisonerd@gmail.com>

Database fixture and temp folder preparation fixtures

.. py:data:: pytest_plugins
   :type: list[str]
   :value: []

   pytest plugins to activate

"""

import shutil
from collections.abc import Sequence
from pathlib import PurePath

import pytest

from kenobi import KenobiDB

pytest_plugins = []


@pytest.fixture()
def prepare_folders_files(request):
    """Prepare folders and files within folder."""

    set_folders = set()

    def _method(seq_rel_paths, tmp_path):
        """Creates folders and empty files

        :param seq_rel_paths: Relative file paths. Creates folders as well
        :type seq_rel_paths:

           collections.abc.Sequence[str | pathlib.Path] | collections.abc.MutableSet[str | pathlib.Path]

        :param tmp_path: Start absolute path
        :type tmp_path: pathlib.Path
        :returns: Set of absolute paths of created files
        :rtype: set[pathlib.Path]
        """
        set_abs_paths = set()
        is_seq = seq_rel_paths is not None and (
            (isinstance(seq_rel_paths, Sequence) and not isinstance(seq_rel_paths, str))
            or isinstance(seq_rel_paths, set)
        )
        if is_seq:
            for posix in seq_rel_paths:
                if isinstance(posix, str):
                    abs_path = tmp_path.joinpath(*posix.split("/"))
                elif issubclass(type(posix), PurePath):
                    if not posix.is_absolute():
                        abs_path = tmp_path / posix
                    else:  # pragma: no cover
                        # already absolute
                        abs_path = posix
                else:
                    abs_path = None

                if abs_path is not None:
                    set_abs_paths.add(abs_path)
                    set_folders.add(abs_path.parent)
                    abs_path.parent.mkdir(parents=True, exist_ok=True)
                    abs_path.touch()
        else:
            abs_path = None

        return set_abs_paths

    yield _method

    # cleanup
    if request.node.test_report.outcome == "passed":
        for abspath_folder in set_folders:
            shutil.rmtree(abspath_folder, ignore_errors=True)


@pytest.fixture()
def db_path(tmp_path):
    """
    Returns:
        pathlib.Path: path to database within pytest managed temporary folder
    """
    path_db = tmp_path.joinpath("test_kenobi.db")

    return path_db


@pytest.fixture()
def create_db(db_path, request):
    """Per test function create database in pytest managed temporary folder

    Usage

    .. code-block:: text

       import pytest
       def test_sometest(create_db):
           db = create_db()

    Returns:
        KenobiDB: database instance
    """
    db = KenobiDB(db_path)

    def cleanup():
        """Pretty way but works.

        Purposefully refrain from: purge database or delete database file.

        Let pytest manage removing the db file. So can later
        debug a test function in a working debug environment.
        """
        db.close()

    def _fcn():
        """Initializes database. After test function close database.

        - purposefully induce a failure with :code:`assert False`

        - go to the temp folder

        - activate the venv

        - open a REPR with :command:`python`

        """

        return db

    request.addfinalizer(cleanup)

    return _fcn
