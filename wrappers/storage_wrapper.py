import pymongo
from datetime import datetime, date
from collections import namedtuple
import json
DbEntry = namedtuple("DbEntry", field_names=["text", "date"])

######### DATABASE RECORD ####################
# {"name": programming language name, "value", json.dumps(DbEntry)}
# DbEntry is an named tupled containing the text and the date it was added


def serialize_date(obj):
    """JSON serializer for datetime objects not serializable by default json code"""

    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError("Type %s not serializable" % type(obj))


class StorageWrapper:
    """ Wrapper class to isolate pymongo dependency """
    db = None
    client = None
    curr_collection = None

    def __init__(self, db_name):
        try:
            # Connect to the mongo server
            self.client = pymongo.MongoClient("mongodb://localhost:27017/")
            # Get reference to db_name database, whether exists or not
            self.db = self.client[db_name]
            _ = self.db.list_collection_names()
        except Exception as e:
            print(e)

    def open_or_create(self, collection_name):
        """ Create a collection (in SQL, a table) """
        # Create a collection if it does not exist
        if collection_name not in self.db.list_collection_names():
            print(f"collection {collection_name} does not exist")
            self.db.create_collection(
                collection_name, capped=True, size=50_000_000, max=1000)
        self.curr_collection = self.db[collection_name]

    def find(self, name_of_entry):
        """ Search for a record given a record name, returning tuple of (text, date).
        Returns None if does not find it. """
        object_as_dict = self.curr_collection.find_one({"name": name_of_entry})
        if object_as_dict is None:
            return None
        object_value_tuple = json.loads(object_as_dict["value"])
        stored_json = object_value_tuple[0]
        stored_date = datetime.fromisoformat(object_value_tuple[1])
        return stored_json, stored_date

    def keys(self):
        """ Return a list of the key names """
        return list(self.curr_collection.distinct("name"))

    def insert_or_update(self, name: str, text: str, date_str: str):
        # Check if document with same "name" field is already in the collection

        # Prep entry for insert or update
        db_entry = DbEntry(text=text,
                           date=serialize_date(date_str))
        record = {"name": name, "value": json.dumps(db_entry)}
        count = self.curr_collection.count_documents({"name": record["name"]})

        if count == 1:
            # Record already exists with that name, so we update existing
            self.curr_collection.update_one(filter={"name": record["name"]}, update={
                                            "$set": {"value": record["value"]}})
        elif count > 1:
            # Two or more records exists with that name, which breaks an invariant
            # we have guarded here. That should never happen in normal
            # operation
            raise ValueError(
                "Count of documents with a given name should not ever be greater than 1")
        elif count == 0:
            # No records exist with that, so we insert it for the first time
            self.curr_collection.insert_one(record)

    def delete(self, name_of_entry):
        self.curr_collection.delete_one({"name": name_of_entry})

    def delete_collection(self, collection_name):
        self.db.drop_collection(collection_name)
