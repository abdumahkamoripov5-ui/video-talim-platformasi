"""Run migrations only when explicitly enabled for a production deployment."""
import os
import subprocess
import sys
import shutil
from pathlib import Path

root = Path(__file__).resolve().parent.parent
if os.environ.get('RUN_MIGRATIONS', '').lower() == 'true':
    if os.environ.get('VERCEL_ENV') != 'production':
        raise SystemExit('RUN_MIGRATIONS is only allowed for production deployments')
    subprocess.run([sys.executable, 'manage.py', 'migrate', '--noinput'], cwd=root, check=True)

# Build React before Vercel runs Django collectstatic.
subprocess.run(['npm', 'ci', '--prefix', 'frontend'], cwd=root, check=True)
subprocess.run(['npm', 'run', 'build', '--prefix', 'frontend', '--', '--base=/static/'], cwd=root, check=True)
shutil.copyfile(root / 'frontend/dist/index.html', root / 'templates/spa.html')
