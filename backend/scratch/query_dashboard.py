import pprint
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)
response = client.get("/api/lab/validation/dashboard")
print("Status Code:", response.status_code)
if response.status_code == 200:
    pprint.pprint(response.json())
else:
    print("Error:", response.text)
