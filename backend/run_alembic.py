import subprocess
import sys

result = subprocess.run([
    sys.executable, '-m', 'alembic', 'upgrade', 'head'
], cwd=r'C:\Users\poove\Documents\New folder\backend', capture_output=True, text=True)

print('STDOUT:')
print(result.stdout)
print('STDERR:')
print(result.stderr)
print('Return code:', result.returncode)