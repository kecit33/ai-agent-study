"""PythonAnywhere WSGI 入口模板（免费账户只能跑 WSGI，不能常驻监听端口）。

用法：
  1. 把本项目上传到 /home/<你的用户名>/ai-campus-companion
  2. 在 Bash 控制台执行：pip install --user -r requirements.txt
  3. Web → Add a new web app → Manual configuration (Python 3.10/3.11)
  4. 把本文件内容粘进 WSGI 配置文件，并把 PROJECT_DIR 改成你的真实路径
  5. Reload，访问 https://<你的用户名>.pythonanywhere.com

说明：PythonAnywhere 走 Flask 版（app.py）；Render / 本地走零依赖的 server.py。
os.chdir 是必需的——app.py 的静态目录使用相对路径 "static"。
"""
import os
import sys

PROJECT_DIR = "/home/YOUR_USERNAME/ai-campus-companion"  # ← 改成你的真实路径

if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)
os.chdir(PROJECT_DIR)

from app import app as application  # noqa: E402,F401
