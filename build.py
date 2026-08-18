import subprocess
import shutil
import os
import sys
import json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

print("Building with PyInstaller...")
result = subprocess.run(
    [os.path.join("venv", "Scripts", "pyinstaller.exe"), "-F", "-w", "app.py", "-i", "icon.ico"],
    cwd=BASE_DIR, shell=True
)

if result.returncode != 0:
    print("Build failed!")
    sys.exit(1)

print("Build complete. Cleaning up...")

# Remove build folder
build_dir = os.path.join(BASE_DIR, "build")
if os.path.exists(build_dir):
    shutil.rmtree(build_dir)

# Remove spec file
spec_file = os.path.join(BASE_DIR, "app.spec")
if os.path.exists(spec_file):
    os.remove(spec_file)

# Copy config.json to dist
config_src = os.path.join(BASE_DIR, "config.json")
config_dst = os.path.join(BASE_DIR, "dist", "config.json")
shutil.copy2(config_src, config_dst)

# Copy icon.ico to dist
icon_src = os.path.join(BASE_DIR, "icon.ico")
icon_dst = os.path.join(BASE_DIR, "dist", "icon.ico")
if os.path.exists(icon_src):
    shutil.copy2(icon_src, icon_dst)

# Rename app.exe to RadioZed.exe
app_exe = os.path.join(BASE_DIR, "dist", "app.exe")
radiozed_exe = os.path.join(BASE_DIR, "dist", "RadioZed.exe")
if os.path.exists(app_exe):
    if os.path.exists(radiozed_exe):
        os.remove(radiozed_exe)
    os.rename(app_exe, radiozed_exe)

# Rename dist to RadioZed v{version}
with open(config_src, 'r', encoding='utf-8') as f:
    config = json.load(f)
version = config.get('version', '0.0.0')
dist_dir = os.path.join(BASE_DIR, "dist")
new_dir = os.path.join(BASE_DIR, f"RadioZed v{version}")
if os.path.exists(new_dir):
    shutil.rmtree(new_dir)
os.rename(dist_dir, new_dir)

print(f"Done! Output in {new_dir}/")