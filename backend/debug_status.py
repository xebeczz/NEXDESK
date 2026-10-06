import sys
sys.path.insert(0, '.')
import json, urllib.request, time, subprocess

proc = subprocess.Popen([sys.executable, '-m', 'uvicorn', 'app.main:app', '--host', '0.0.0.0', '--port', '8001'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
time.sleep(3)

BASE = 'http://localhost:8001'

def req(method, path, data=None, token=None):
    url = BASE + path
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

# Get tickets
s, r = req('GET', '/api/v1/tickets', token=token)
print(f'List tickets: {s}')
tickets = r.get('items', [])
if tickets:
    t = tickets[0]
    print(f'First ticket: {t.get("ticket_no")}, status={t.get("status")}')
    tid = t.get('id')
    
    # Try to change status
    for status in ['in_progress', 'pending', 'resolved', 'closed']:
        s, r = req('POST', f'/api/v1/tickets/{tid}/status', {'status': status, 'resolution_notes': f'Test {status}'}, token=token)
        print(f'  Change to {status}: {s} - {r}')

proc.terminate()