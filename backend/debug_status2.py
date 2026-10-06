import sys
sys.path.insert(0, 'backend')
import json, urllib.request, time, subprocess
from urllib.parse import urlencode

proc = subprocess.Popen(
    [sys.executable, '-m', 'uvicorn', 'app.main:app', '--host', '0.0.0.0', '--port', '8000'],
    stdout=subprocess.PIPE, stderr=subprocess.STDOUT
)
time.sleep(3)

BASE = 'http://localhost:8000'

def req(method, path, data=None, token=None, params=None):
    url = BASE + path
    if params:
        url += '?' + urlencode(params)
    body = json.dumps(data).encode() if data else None
    headers = {'Content-Type': 'application/json'}
    if token:
        headers['Authorization'] = f'Bearer {token}'
    r = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        resp = urllib.request.urlopen(r, timeout=15)
        return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode())

# Login as admin
s, r = req('POST', '/api/v1/auth/login', {'identifier': 'admin@itdesk.io', 'password': 'Admin@12345'})
print(f'Admin login: {s}')
token = r.get('access_token', '')

# Create a new ticket as admin
s, r = req('POST', '/api/v1/tickets', {
    'title': 'Test status flow',
    'description': 'Testing status flow',
    'category': 'Hardware',
    'priority': 'medium'
}, token=token)
print(f'Create ticket: {s}')
ticket_id = r.get('id', '')
ticket_no = r.get('ticket_no', '')

# Test status flow
statuses = ['in_progress', 'pending', 'resolved', 'closed']
for new_status in statuses:
    s, r = req('POST', f'/api/v1/tickets/{ticket_id}/status', {'status': new_status, 'resolution_notes': f'Test {new_status}'}, token=token)
    print(f'  Change to {new_status}: {s}')
    if s != 200:
        print(f'    Error: {r}')

proc.terminate()