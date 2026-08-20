import subprocess
import shutil
import os
import sys
import json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def run_pyinstaller() -> None:
    result = subprocess.run(
        [os.path.join("venv", "Scripts", "pyinstaller.exe"), "-F", "-w", "app.py", "-i", "icon.ico"],
        cwd=BASE_DIR, shell=True
    )
    if result.returncode != 0:
        print("Build failed!")
        sys.exit(1)
    print("Build complete.")


def cleanup_build_artifacts() -> None:
    build_dir = os.path.join(BASE_DIR, "build")
    if os.path.exists(build_dir):
        shutil.rmtree(build_dir)
    spec_file = os.path.join(BASE_DIR, "app.spec")
    if os.path.exists(spec_file):
        os.remove(spec_file)
    print("Cleaned up build artifacts.")


def copy_config() -> None:
    src = os.path.join(BASE_DIR, "config.json")
    dst = os.path.join(BASE_DIR, "dist", "config.json")
    shutil.copy2(src, dst)


def copy_icon() -> None:
    src = os.path.join(BASE_DIR, "icon.ico")
    dst = os.path.join(BASE_DIR, "dist", "icon.ico")
    if os.path.exists(src):
        shutil.copy2(src, dst)


def copy_src() -> None:
    src = os.path.join(BASE_DIR, "src")
    dst = os.path.join(BASE_DIR, "dist", "src")
    if os.path.exists(src):
        if os.path.exists(dst):
            shutil.rmtree(dst)
        shutil.copytree(src, dst)


def rename_exe() -> None:
    app_exe = os.path.join(BASE_DIR, "dist", "app.exe")
    radiozed_exe = os.path.join(BASE_DIR, "dist", "RadioZed.exe")
    if os.path.exists(app_exe):
        if os.path.exists(radiozed_exe):
            os.remove(radiozed_exe)
        os.rename(app_exe, radiozed_exe)


def rename_dist() -> None:
    config_src = os.path.join(BASE_DIR, "config.json")
    with open(config_src, 'r', encoding='utf-8') as f:
        config = json.load(f)
    version = config.get('version', '0.0.0')
    dist_dir = os.path.join(BASE_DIR, "dist")
    new_dir = os.path.join(BASE_DIR, f"RadioZed v{version}")
    if os.path.exists(new_dir):
        shutil.rmtree(new_dir)
    os.rename(dist_dir, new_dir)
    print(f"Done! Output in {new_dir}/")


if __name__ == "__main__":
    run_pyinstaller()          # 1. PyInstaller打包
    cleanup_build_artifacts()  # 2. 清理build目录和spec文件
    copy_config()              # 3. 复制config.json
    copy_icon()                # 4. 复制icon.ico
    copy_src()                 # 5. 复制src文件夹
    rename_exe()               # 6. 重命名app.exe为RadioZed.exe
    rename_dist()              # 7. 重命名dist为RadioZed v{version}