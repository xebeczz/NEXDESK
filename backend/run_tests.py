import subprocess
import sys

# Run all backend tests
result = subprocess.run([
    sys.executable, '-m', 'pytest', '--tb=short', 'tests/'
], cwd=r'C:\Users\poove\Documents\New folder\backend', capture_output=True, text=True, timeout=120)

print('STDOUT:')
print(result.stdout)
print('STDERR:')
print(result.stderr)
print('Return code:', result.returncode)