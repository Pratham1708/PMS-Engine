"""
Check what the Archive/Compare/Changes API endpoints actually return vs what frontend expects.
"""
from fastapi.testclient import TestClient
from main import app
import json

client = TestClient(app)

# 1. /snapshot/dates — Archive tab
print("=== 1. GET /snapshot/dates (Archive tab) ===")
r = client.get('/api/snapshot/dates')
print(f"Status: {r.status_code}")
data = r.json()
print(f"Response type: {type(data)}, keys: {list(data.keys()) if isinstance(data, dict) else 'LIST len=' + str(len(data))}")
if isinstance(data, dict):
    dates = data.get('dates', [])
    if dates:
        print(f"First date item keys: {list(dates[0].keys())}")
        print(f"First date item: {json.dumps(dates[0], default=str)}")

# 2. /snapshot/latest/changes — What's Changed tab
print("\n=== 2. GET /snapshot/latest/changes (What's Changed) ===")
r2 = client.get('/api/snapshot/latest/changes')
print(f"Status: {r2.status_code}")
data2 = r2.json()
print(f"Response type: {type(data2)}, len={len(data2) if isinstance(data2, list) else 'N/A'}")
if isinstance(data2, list) and len(data2) > 0:
    print(f"First change keys: {list(data2[0].keys())}")
    print(f"First change: {json.dumps(data2[0], default=str)}")
elif isinstance(data2, dict):
    print(f"Response: {json.dumps(data2, default=str)[:300]}")

# 3. /snapshot/compare — Compare tab
print("\n=== 3. GET /snapshot/compare?date1=&date2= (Compare) ===")
r3 = client.get('/api/snapshot/dates')
dates_data = r3.json()
dates_list = dates_data.get('dates', []) if isinstance(dates_data, dict) else []
print(f"Available dates: {[d['snapshot_date'] for d in dates_list[:5]]}")

if len(dates_list) >= 2:
    d1 = dates_list[1]['snapshot_date']
    d2 = dates_list[0]['snapshot_date']
    print(f"\nComparing {d1} vs {d2}")
    r_cmp = client.get(f'/api/snapshot/compare?date1={d1}&date2={d2}')
    print(f"Status: {r_cmp.status_code}")
    if r_cmp.status_code == 200:
        cmp = r_cmp.json()
        print(f"Response keys: {list(cmp.keys())}")
        meta = cmp.get('comparison_metadata', {})
        print(f"Metadata: {meta}")
        deltas = cmp.get('stock_deltas', [])
        print(f"stock_deltas count: {len(deltas)}")
        if deltas:
            print(f"First delta keys: {list(deltas[0].keys())}")
    else:
        print(f"Error: {r_cmp.text[:300]}")

# 4. Check what {date}/changes returns
print("\n=== 4. GET /snapshot/{date}/changes ===")
if dates_list:
    date = dates_list[0]['snapshot_date']
    r4 = client.get(f'/api/snapshot/{date}/changes')
    print(f"Status: {r4.status_code}, type={type(r4.json())}, len={len(r4.json()) if isinstance(r4.json(), list) else 'N/A'}")
    if isinstance(r4.json(), list) and r4.json():
        print(f"First change: {json.dumps(r4.json()[0], default=str)}")
    else:
        print(f"Response: {r4.text[:200]}")
