"""Export the committed source without carrying local Git history into a new repo."""
import subprocess
from pathlib import Path

root = Path(__file__).resolve().parent.parent
files = subprocess.check_output(['git', 'ls-tree', '-r', '--name-only', 'HEAD'], cwd=root, text=True).splitlines()
unsafe = [name for name in files if name == '.env' or name.endswith('.sqlite3') or '__pycache__/' in name]
if unsafe:
    raise SystemExit('Avval maxfiy/lokal fayllarni Git kuzatuvidan chiqarib commit qiling.')
output = root / 'release-source.zip'
subprocess.run(['git', 'archive', '--format=zip', f'--output={output}', 'HEAD'], cwd=root, check=True)
print(f'Tarix va maxfiy fayllarsiz kod: {output}')
