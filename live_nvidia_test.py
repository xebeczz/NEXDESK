import sys, subprocess, time, json, urllib.request

sys.path.insert(0, 'backend')

proc = subprocess.Popen(
    [sys.executable, '-m', 'uvicorn', 'app.main:app', '--host', '0.0.0.0', '--port', '8000'],
    stdout=subprocess.PIPE, stderr=subprocess.STDOUT
)
time.sleep(5)

BASE = 'http://localhost:8000'

def req(method, path, data=None, token=None, params=None):
    from urllib.parse import urlencode
    url = BASE + path
    if params:
        url += '?' + urlencode(params)
    body = json.dumps(data).encode() if data else None
    headers = {'Content-Type': 'application/json'}
    if token:
        headers['Authorization'] = f'Bearer {token}'
    r = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        resp = urllib.request.urlopen(r, timeout=60)
        content = resp.read().decode()
        try:
            return resp.status, json.loads(content)
        except json.JSONDecodeError:
            return resp.status, content
    except urllib.error.HTTPError as e:
        content = e.read().decode()
        try:
            return e.code, json.loads(content)
        except json.JSONDecodeError:
            return e.code, content

# Login as user
s, r = req('POST', '/api/v1/auth/login', {'identifier': 'user@itdesk.io', 'password': 'User@12345'})
print(f'Login: {s}')
token = r.get('access_token', '')

# Create chat session
s, r = req('POST', '/api/v1/chat/sessions', {}, token=token)
print(f'Create session: {s}')
session_id = r.get('id', '')

# Test 1: "Hi"
print('\n=== TEST 1: "Hi" ===')
s, r = req('POST', f'/api/v1/chat/sessions/{session_id}/messages', {'message': 'Hi'}, token=token)
print(f'Status: {s}')
print(f'Response: {json.dumps(r, indent=2)[:500]}')

# Test 2: "My laptop Wi-Fi is not working."
print('\n=== TEST 2: "My laptop Wi-Fi is not working." ===')
s, r = req('POST', f'/api/v1/chat/sessions/{session_id}/messages', {'message': 'My laptop Wi-Fi is not working.'}, token=token)
print(f'Status: {s}')
print(f'Response: {json.dumps(r, indent=2)[:500]}')

# Test 3: Critical issue
print('\n=== TEST 3: "My production server is completely down and multiple departments cannot work." ===')
s, r = req('POST', f'/api/v1/chat/sessions/{session_id}/messages', {'message': 'My production server is completely down and multiple departments cannot work.'}, token=token)
print(f'Status: {s}')
print(f'Response: {json.dumps(r, indent=2)[:500]}')

# Check for draft
print('\n=== CHECK DRAFTS ===')
s, r = req('GET', '/api/v1/chat/drafts', token=token)
print(f'Drafts: {s}')
print(f'Drafts: {json.dumps(r, indent=2)}')

proc.terminate()