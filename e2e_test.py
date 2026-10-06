"""End-to-end testing script for ITDesk acceptance."""
import subprocess, time, sys, urllib.request, json, os
from urllib.parse import urlencode

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

results = []

def run(name, condition, detail):
    status = 'PASS' if condition else 'FAIL'
    results.append((name, condition, detail))
    if not condition:
        print(f'  [{status}] {name} -> {detail}')
    else:
        print(f'  [{status}] {name}')

# Start the backend server
proc = subprocess.Popen(
    [sys.executable, '-m', 'uvicorn', 'app.main:app', '--host', '0.0.0.0', '--port', '8000'],
    stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
    cwd=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend')
)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend'))
time.sleep(4)

# Check health
try:
    r = urllib.request.urlopen(f'{BASE}/health', timeout=5)
    health_ok = r.status == 200
except Exception:
    health_ok = False
run('Backend health', health_ok, f'status={r.status if health_ok else "failed"}')

# Check NVIDIA API key
from app.core.config import settings
nvidia_enabled = bool(settings.NVIDIA_API_KEY)
run('NVIDIA API key present', nvidia_enabled, 'NVIDIA_API_KEY is empty (offline mode)')

# 1. Login as User
s, r = req('POST', '/api/v1/auth/login', {'identifier': 'user@itdesk.io', 'password': 'User@12345'})
run('Login as User', s == 200, f'status={s}')
user_token = r.get('access_token', '') if s == 200 else ''

# 2. Login as Admin
s, r = req('POST', '/api/v1/auth/login', {'identifier': 'admin@itdesk.io', 'password': 'Admin@12345'})
run('Login as Admin', s == 200, f'status={s}')
admin_token = r.get('access_token', '') if s == 200 else ''

# 3. User /me
s, r = req('GET', '/api/v1/auth/me', token=user_token)
run('User role correct', s == 200 and r.get('role') == 'user', f'role={r.get("role") if s == 200 else "N/A"}')

# 4. Admin /me
s, r = req('GET', '/api/v1/auth/me', token=admin_token)
run('Admin role correct', s == 200 and r.get('role') == 'admin', f'role={r.get("role") if s == 200 else "N/A"}')

# 5. User dashboard stats
s, r = req('GET', '/api/v1/dashboard/stats', token=user_token)
run('User dashboard stats', s == 200, f'status={s}, keys={list(r.keys()) if s == 200 else r}')

# 6. Admin dashboard stats
s, r = req('GET', '/api/v1/dashboard/stats', token=admin_token)
run('Admin dashboard stats', s == 200, f'status={s}, keys={list(r.keys()) if s == 200 else r}')

# 7. Analytics endpoints (admin)
s, r = req('GET', '/api/v1/analytics/monthly-trends', {}, admin_token, {'months': 12})
run('Monthly trends analytics', s == 200, f'status={s}')

s, r = req('GET', '/api/v1/analytics/tickets-over-time', {}, admin_token, {'days': 30})
run('Tickets over time analytics', s == 200, f'status={s}')

s, r = req('GET', '/api/v1/analytics/priority-distribution', {}, admin_token)
run('Priority distribution analytics', s == 200, f'status={s}')

s, r = req('GET', '/api/v1/analytics/status-distribution', {}, admin_token)
run('Status distribution analytics', s == 200, f'status={s}')

s, r = req('GET', '/api/v1/analytics/department-distribution', {}, admin_token)
run('Department distribution analytics', s == 200, f'status={s}')

s, r = req('GET', '/api/v1/analytics/sla', {}, admin_token)
run('SLA analytics', s == 200, f'status={s}')

# 8. AI chat - create session
s, r = req('POST', '/api/v1/chat/sessions', {}, token=user_token)
run('AI: Create chat session', s in (200, 201), f'status={s}')
session_id = r.get('id', '') if s in (200, 201) else ''

# 9. AI - greeting
s, r = req('POST', f'/api/v1/chat/sessions/{session_id}/messages', {'message': 'Hi'}, token=user_token)
run('AI: Greeting message', s == 200, f'status={s}')

# 10. AI - thanks
s, r = req('POST', f'/api/v1/chat/sessions/{session_id}/messages', {'message': 'Thank you'}, token=user_token)
run('AI: Thanks message', s == 200, f'status={s}')

# 11. AI - password issue
s, r = req('POST', f'/api/v1/chat/sessions/{session_id}/messages', {'message': "My password isn't working."}, token=user_token)
run('AI: Password issue', s == 200, f'status={s}')

# 12. AI - critical incident
s, r = req('POST', f'/api/v1/chat/sessions/{session_id}/messages', {'message': 'My production server is completely down and multiple departments cannot work.'}, token=user_token)
run('AI: Critical incident', s == 200, f'status={s}')

# 13. Chat persistence - list messages
s, r = req('GET', f'/api/v1/chat/sessions/{session_id}/messages', token=user_token)
run('Chat persistence (messages visible)', s == 200 and len(r) > 0, f'status={s}, count={len(r) if s == 200 else 0}')

# 14. Chat persistence - list sessions
s, r = req('GET', '/api/v1/chat/sessions', token=user_token)
run('Chat sessions visible', s == 200 and len(r) > 0, f'status={s}, count={len(r) if s == 200 else 0}')

# 15. Create ticket as User
s, r = req('POST', '/api/v1/tickets', {
    'title': 'Test ticket from e2e',
    'description': 'Testing E2E flow',
    'category': 'Hardware',
    'priority': 'medium'
}, token=user_token)
run('Create ticket as User', s == 201, f'status={s}, ticket_no={r.get("ticket_no", "") if s == 201 else r}')
ticket_no = r.get('ticket_no', '') if s == 201 else ''
ticket_id = r.get('id', '') if s == 201 else ''

# 16. Verify ticket_no format
import re
format_ok = bool(re.match(r'^TCK-\d{8}-\d{4}$', ticket_no)) if ticket_no else False
run('Ticket number format (TCK-YYYYMMDD-XXXX)', format_ok, f'ticket_no={ticket_no}')

# 17. List user tickets
s, r = req('GET', '/api/v1/tickets', token=user_token)
run('List user tickets', s == 200, f'status={s}')

# 18. Admin sees all tickets
s, r = req('GET', '/api/v1/tickets', token=admin_token)
all_tickets = r.get('items', []) if s == 200 else []
ticket_found = any(t.get('ticket_no') == ticket_no for t in all_tickets)
run('Admin sees user ticket', ticket_found, f'found={ticket_found}')

# 19. User blocked from admin route
s, r = req('GET', '/api/v1/admin/users', token=user_token)
run('User blocked from admin route', s == 403, f'status={s}')

# 20. Admin can access admin routes
s, r = req('GET', '/api/v1/admin/users', token=admin_token)
run('Admin accesses admin route', s == 200, f'status={s}')

# 21. Admin system health
s, r = req('GET', '/api/v1/admin/system-health', token=admin_token)
run('Admin system health', s == 200, f'status={s}')

# 22. Admin audit logs
s, r = req('GET', '/api/v1/admin/audit-logs', token=admin_token)
run('Admin audit logs', s == 200, f'status={s}')

# 23. Settings endpoint
s, r = req('GET', '/api/v1/settings', token=user_token)
run('Settings endpoint', s == 200, f'status={s}')

# 24. Security settings
s, r = req('GET', '/api/v1/settings/security', token=user_token)
run('Security settings endpoint', s == 200, f'status={s}')

# 25. Notifications
s, r = req('GET', '/api/v1/notifications', token=user_token)
run('Notifications endpoint', s == 200, f'status={s}')

# 26. Ticket status change test (admin)
statuses = ['in_progress', 'pending', 'resolved', 'closed']
prev_status = 'open'
all_changed = True
change_details = []
for new_status in statuses:
    s, r = req('POST', f'/api/v1/tickets/{ticket_id}/status', {'status': new_status, 'resolution_notes': f'Changed to {new_status}'}, token=admin_token)
    ok = s == 200
    change_details.append(f'{prev_status}->{new_status}:{"OK" if ok else "FAIL"}')
    if not ok:
        all_changed = False
    prev_status = new_status
run('Ticket status flow (open->in_progress->pending->resolved->closed)', all_changed, '; '.join(change_details))

# 27. Reopen ticket
s, r = req('POST', f'/api/v1/tickets/{ticket_id}/close', {'resolution_notes': 'Closed for testing'}, token=admin_token)
run('Admin close ticket', s == 200, f'status={s}')

# 28. Verify ticket in database directly
from app.db.session import get_db
from app.models.ticket import Ticket
db = next(get_db())
db_ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
db.close()
run('Ticket exists in database', db_ticket is not None, f'id={ticket_id}, ticket_no={db_ticket.ticket_no if db_ticket else "N/A"}')

# 29. AI drafts endpoint
s, r = req('GET', '/api/v1/chat/drafts', token=user_token)
run('AI drafts endpoint', s == 200, f'status={s}')

# 30. Reports endpoint (admin)
import io
s, r = req('GET', '/api/v1/reports/summary', token=admin_token)
run('Reports - summary', s == 200, f'status={s}')

s, r = req('GET', '/api/v1/reports/analytics', token=admin_token)
run('Reports - analytics', s == 200, f'status={s}')

# 31. Verify no 'staff' role in UserRole enum
from app.models.enums import UserRole
roles = [r.value for r in UserRole]
run('Only User/Admin roles exist', roles == ['admin', 'user'], f'roles={roles}')

# 32. Verify no aimotron model
run('Model is not aimotron', settings.NVIDIA_MODEL != 'nvidia/aimotron-550b', f'model={settings.NVIDIA_MODEL}')
run('Model is nemotron-3-ultra-550b-a55b', settings.NVIDIA_MODEL == 'nvidia/nemotron-3-ultra-550b-a55b', f'model={settings.NVIDIA_MODEL}')
run('Base URL is correct', settings.NVIDIA_BASE_URL == 'https://integrate.api.nvidia.com/v1', f'base_url={settings.NVIDIA_BASE_URL}')

# Terminate server
proc.terminate()
proc.wait()

print('\n' + '='*60)
passed = sum(1 for _, ok, _ in results if ok)
total = len(results)
print(f'E2E RESULTS: {passed}/{total} passed')
print('='*60)
if passed == total:
    print('ALL TESTS PASSED')
else:
    print(f'{total - passed} tests FAILED')
    for name, ok, detail in results:
        if not ok:
            print(f'  FAIL: {name} -> {detail}')
