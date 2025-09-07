import os
import shutil
import subprocess
import sys
from pathlib import Path

# --- 以下路径可按实际项目调整 ---
FRONTEND_ROOT      = Path("frontend")
BACKEND_ROOT       = Path("entari_plugin_webui")
PACKAGE_NAME       = "entari_plugin_webui"
FRONTEND_BUILD_DIR = FRONTEND_ROOT / "dist"
FRONTEND_PKG_DIR   = BACKEND_ROOT / PACKAGE_NAME / "frontend"
# ---------------------------------

def clean_copy_frontend():
    """把前端构建产物塞进 Python 包"""
    if not FRONTEND_BUILD_DIR.exists():
        print(f"[ERROR] {FRONTEND_BUILD_DIR} 不存在，请先构建前端！")
        sys.exit(1)

    if FRONTEND_PKG_DIR.exists():
        shutil.rmtree(FRONTEND_PKG_DIR)
    FRONTEND_PKG_DIR.mkdir(parents=True)

    for item in FRONTEND_BUILD_DIR.iterdir():
        dst = FRONTEND_PKG_DIR / item.name
        if item.is_dir():
            shutil.copytree(item, dst)
        else:
            shutil.copy2(item, dst)
    print(f"[INFO] 前端产物已复制到 {FRONTEND_PKG_DIR}")

def build_python_package():
    """调用 pdm build"""
    print("[INFO] 开始 pdm build …")
    subprocess.run(["pdm", "build"], cwd=BACKEND_ROOT, check=True)

def main():
    clean_copy_frontend()
    build_python_package()

if __name__ == "__main__":
    main()