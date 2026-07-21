from fastapi.testclient import TestClient
from main import app
client = TestClient(app)

print('=== Testing all three actions ===')
r = client.get('/api/snapshot/diagnostics/list')
snaps = r.json()
print(f'Snapshots: {len(snaps)}')

sid = snaps[0]['snapshot_id']
date = snaps[0]['snapshot_date']
print(f'Using: {sid[:8]}... date={date}')

# 1. Inspect validation (clicking a row)
print('\n1. inspectValidation (GET /snapshot/{date}/validation)')
r_val = client.get(f'/api/snapshot/{date}/validation')
print(f'   Status: {r_val.status_code}')
data = r_val.json()
is_list = isinstance(data, list)
length = len(data) if is_list else 'N/A'
print(f'   Response is list: {is_list}, length: {length}')
if is_list and len(data) > 0:
    print(f'   First check keys: {list(data[0].keys())}')

# 2. Validate button
print('\n2. handleValidate (POST /snapshot/{id}/validate)')
r_v = client.post(f'/api/snapshot/{sid}/validate')
print(f'   Status: {r_v.status_code}')
vdata = r_v.json()
print(f'   Response keys: {list(vdata.keys())}')
print(f'   status={vdata.get("status")} score={vdata.get("score")}')
checks = vdata.get('checks', [])
keys = list(checks[0].keys()) if checks else 'empty'
print(f'   checks count: {len(checks)}, sample keys: {keys}')

# 3. Delete (import only test)
print('\n3. DELETE route registered correctly')
for route in app.routes:
    if hasattr(route, 'path') and 'snapshot' in route.path and 'DELETE' in getattr(route, 'methods', set()):
        print(f'   DELETE {route.path}')
