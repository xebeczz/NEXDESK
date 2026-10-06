import sys, subprocess, time, json, urllib.request, urllib.error

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

def stream_message(session_id, message, token):
    """Stream a message and capture all SSE events"""
    url = f'{BASE}/api/v1/chat/sessions/{session_id}/messages'
    body = json.dumps({'message': message}).encode()
    headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {token}'}
    r = urllib.request.Request(url, data=body, headers=headers, method='POST')
    
    events = []
    buffer = ""
    try:
        resp = urllib.request.urlopen(r, timeout=120)
        for line in resp:
            line = line.decode()
            if line.startswith('data:'):
                data = line[5:].strip()
                if data == '[DONE]':
                    break
                try:
                    ev = json.loads(data)
                    events.append(ev)
                except json.JSONDecodeError:
                    pass
    except urllib.error.HTTPError as e:
        print(f'HTTP Error: {e.code} - {e.read().decode()}')
    return events

# Login as user
s, r = req('POST', '/api/v1/auth/login', {'identifier': 'user@itdesk.io', 'password': 'User@12345'})
print(f'Login: {s}')
token = r.get('access_token', '')

# Create chat session
s, r = req('POST', '/api/v1/chat/sessions', {}, token=token)
print(f'Create session: {s}')
session_id = r.get('id', '')

# Test 1: "Hi" - capture full stream
print('\n=== TEST 1: "Hi" ===')
events = stream_message(session_id, 'Hi', token)
full_content = ''
analysis = None
for ev in events:
    if ev.get('type') == 'token':
        full_content += ev.get('content', '')
    elif ev.get('type') == 'analysis':
        analysis = ev.get('analysis', {})
        print(f'Analysis: {json.dumps(analysis, indent=2)}')
    elif ev.get('type') == 'draft':
        print(f'Draft created: {json.dumps(ev.get("draft", {}), indent=2)}')
print(f'Full response: {full_content[:500].encode("ascii", "ignore").decode()}...')

# Test 2: Wi-Fi issue
print('\n=== TEST 2: "My laptop Wi-Fi is not working." ===')
events = stream_message(session_id, "My laptop Wi-Fi is not working.", token)
full_content = ''
analysis = None
for ev in events:
    if ev.get('type') == 'token':
        full_content += ev.get('content', '')
    elif ev.get('type') == 'analysis':
        analysis = ev.get('analysis', {})
        print(f'Analysis: {json.dumps(analysis, indent=2)}')
    elif ev.get('type') == 'draft':
        print(f'Draft created: {json.dumps(ev.get("draft", {}), indent=2)}')
print(f'Full response: {full_content[:500].encode("ascii", "ignore").decode()}...')

# Test 3: Critical issue - production server down
print('\n=== TEST 3: "My production server is completely down and multiple departments cannot work." ===')
events = stream_message(session_id, "My production server is completely down and multiple departments cannot work.", token)
full_content = ''
analysis = None
for ev in events:
    if ev.get('type') == 'token':
        full_content += ev.get('content', '')
    elif ev.get('type') == 'analysis':
        analysis = ev.get('analysis', {})
        print(f'Analysis: {json.dumps(analysis, indent=2)}')
    elif ev.get('type') == 'draft':
        print(f'Draft created: {json.dumps(ev.get("draft", {}), indent=2)}')
print(f'Full response: {full_content[:500].encode("ascii", "ignore").decode()}...')

# Check drafts
print('\n=== CHECK DRAFTS ===')
s, r = req('GET', '/api/v1/chat/drafts', token=token)
print(f'Drafts: {json.dumps(r, indent=2)}')

# Check if ticket was created via draft confirmation
if r and len(r) > 0:
    draft_id = r[0].get('id')
    print(f'\n=== CONFIRM DRAFT ===')
    s, r = req('POST', f'/api/v1/chat/drafts/{draft_id}/confirm', {}, token=token)
    print(f'Confirm draft: {s}')
    print(f'Result: {json.dumps(r, indent=2)}')

proc.terminate()