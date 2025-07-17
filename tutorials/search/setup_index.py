import json
from pdp_sdk import store_es

index = 'test_search'

# Load JSON data from file
with open('./dataset.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Store each doc into the index
for doc in data:
    store_es(doc, index)

print(f"Succesfully added docs to the index {index}")
