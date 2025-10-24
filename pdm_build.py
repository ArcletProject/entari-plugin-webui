#!/usr/bin/env python3
import shutil, subprocess, sys
from pathlib import Path

# 所有路径都用相对当前文件所在目录解析
BASE_DIR        = Path(__file__).parent
FRONTEND_DIST   = BASE_DIR / "frontend" / "dist"
FRONTEND_PKG    = BASE_DIR / "entari_plugin_webui" / "frontend"

def copy_frontend():
    if not FRONTEND_DIST.exists():
        print(f"[ERROR] {FRONTEND_DIST} 不存在，请先在前端目录执行 npm run build")
        sys.exit(1)

    if FRONTEND_PKG.exists():
        shutil.rmtree(FRONTEND_PKG)
    shutil.copytree(FRONTEND_DIST, FRONTEND_PKG)
    print(f"[INFO] 前端产物已复制到 {FRONTEND_PKG}")

def build():
    copy_frontend()
    subprocess.run(["pdm", "build"], check=True)

if __name__ == "__main__":
    build()