import pymongo

# Connect to the MongoDB instance
client = pymongo.MongoClient("mongodb://localhost:27017/")

print(f"Client status {client}")

# Check if a database with the name "prod" exists
if "prod" not in client.list_database_names():
    print(f"database prod does not exist")


# Get a reference to the "prod" database
db = client["prod"]

# Create a collection if it does not exist
if "languages" not in db.list_collection_names():
    print(f"collection languages does not exist")
    db.create_collection("languages", capped=True, size=50_000_000, max = 1000)

# Get a reference to the "languages" collection
languages_collection = db["languages"]

# Query for a document
customer = languages_collection.find_one({"name": "Jane Doe"})
print(customer)

# Insert a new document
new_customer = {
    "name": "Jane Doe",
    "age": 25,
    "email": "jane@example.com"
}
languages_collection.insert_one(new_customer)

# Update an existing document
languages_collection.update_one(
    {"name": "John Smith"},
    {"$set": {"age": 35}}
)

