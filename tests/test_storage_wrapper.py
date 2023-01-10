import pytest
from datetime import datetime
# @NOTE: Could remove some repeated boilerplate with a test fixture


def test_wrapper_import():
    """ Test that the wrappers class can be imported """
    import sys
    sys.path.append(".")
    from wrappers.storage_wrapper import StorageWrapper


def test_pymongo_client():
    """ Verify the pymongo wrapper can connect to the client """
    import sys
    sys.path.append(".")
    from wrappers.storage_wrapper import StorageWrapper
    # Connects to the default localhost server when called
    # with no params
    wrapper = StorageWrapper("prod")


def test_open_or_create():
    # Test that the open_or_create method creates a new collection if it does not exist
    import sys
    sys.path.append(".")
    from wrappers.storage_wrapper import StorageWrapper
    wrapper = StorageWrapper("prod")
    wrapper.delete_collection("test_collection")
    assert "test_collection" not in wrapper.db.list_collection_names()
    wrapper.open_or_create("test_collection")
    assert "test_collection" in wrapper.db.list_collection_names()
    wrapper.delete_collection("test_collection")

    # Test that the open_or_create method switches to an existing collection if it does exist
    wrapper.open_or_create("test_collection")
    assert wrapper.curr_collection.name == "test_collection"


def test_find():
    # Test finding a record that exists
    import sys
    sys.path.append(".")
    from wrappers.storage_wrapper import StorageWrapper
    wrapper = StorageWrapper("test_db")
    wrapper.delete_collection("test_collection")
    wrapper.open_or_create("test_collection")
    record = {"name": "test", "value": "test value"}
    wrapper.insert_or_update(
        record["name"], record["value"], datetime.today().date())
    result = wrapper.find("test")
    try:
        assert result[0] == record["value"]
    except Exception as e:
        wrapper.delete_collection("test_collection")
        raise e
    wrapper.delete_collection("test_collection")

    # Test finding a record that does not exist
    result = wrapper.find("non-existent")
    assert result == None


def test_keys():
    # Test getting keys for an empty collection
    import sys
    sys.path.append(".")
    from wrappers.storage_wrapper import StorageWrapper
    wrapper = StorageWrapper("test_db")
    wrapper.open_or_create("test_collection")
    result = wrapper.keys()
    assert result == list()

    # Test getting keys for a non-empty collection
    records = [
        {"name": "test1", "value": "test value 1"},
        {"name": "test2", "value": "test value 2"},
        {"name": "test3", "value": "test value 3"},
    ]

    for record in records:
        wrapper.insert_or_update(
            record["name"], record["value"], datetime.today().date())
    result = wrapper.keys()
    assert result == ["test1", "test2", "test3"]
    wrapper.delete_collection("test_collection")


def test_insert_or_update():
    # Test inserting a new record
    import sys
    sys.path.append(".")
    from wrappers.storage_wrapper import StorageWrapper
    wrapper = StorageWrapper("test_db")
    wrapper.open_or_create("test_collection")

    record = {"name": "test", "value": "test value"}
    wrapper.insert_or_update(
        record["name"], record["value"], datetime.today().date())
    result = wrapper.find("test")
    try:
        assert result[0] == record["value"]
    except Exception as e:
        wrapper.delete_collection("test_collection")
        raise e

    # Test updating an existing record
    record = {"name": "test", "value": "updated value"}
    wrapper.insert_or_update(
        record["name"], record["value"], datetime.today().date())
    result = wrapper.find("test")
    try:
        assert result[0] == record["value"]
    except Exception as e:
        wrapper.delete_collection("test_collection")
        raise e
    wrapper.delete_collection("test_collection")


def test_delete():
    # Test deleting a record that exists
    import sys
    sys.path.append(".")
    from wrappers.storage_wrapper import StorageWrapper
    wrapper = StorageWrapper("test_db")
    wrapper.open_or_create("test_collection")

    record = {"name": "test", "value": "test value"}
    wrapper.insert_or_update(
        record["name"], record["value"], datetime.today().date())
    wrapper.delete("test")
    result = wrapper.find("test")
    assert result == None

    # Test deleting a record that does not exist
    wrapper.delete("non-existent")
    result = wrapper.find("non-existent")
    assert result == None
    wrapper.delete_collection("test_collection")
