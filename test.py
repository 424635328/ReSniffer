import pathlib
import os

# 定义项目结构
# 目录以斜杠 / 结尾，文件则没有。
file_structure = [
    "ReSniffer_Web/",
    "ReSniffer_Web/frontend/",
    "ReSniffer_Web/frontend/public/",
    "ReSniffer_Web/frontend/src/",
    "ReSniffer_Web/frontend/src/components/",
    "ReSniffer_Web/frontend/src/App.vue",
    "ReSniffer_Web/frontend/src/main.js",
    "ReSniffer_Web/frontend/index.html",
    "ReSniffer_Web/frontend/package.json",
    "ReSniffer_Web/frontend/vite.config.js",
    "ReSniffer_Web/backend/",
    "ReSniffer_Web/backend/app/",
    "ReSniffer_Web/backend/app/api/",
    "ReSniffer_Web/backend/app/api/endpoints/",
    "ReSniffer_Web/backend/app/api/endpoints/sniff.py",
    "ReSniffer_Web/backend/app/core/",
    "ReSniffer_Web/backend/app/core/config.py",
    "ReSniffer_Web/backend/app/services/",
    "ReSniffer_Web/backend/app/services/scraper.py",
    "ReSniffer_Web/backend/app/services/profiler.py",
    "ReSniffer_Web/backend/app/main.py",
    "ReSniffer_Web/backend/requirements.txt",
    "ReSniffer_Web/backend/Dockerfile",
]

def create_project_structure():
    """根据定义的列表创建项目结构"""
    for path_str in file_structure:
        # 将字符串路径转换为pathlib.Path对象
        path = pathlib.Path(path_str)

        if path_str.endswith('/'):
            # 如果路径以斜杠结尾，则为目录
            print(f"创建目录: {path}")
            # 创建目录，parents=True会自动创建父目录，exist_ok=True表示如果目录已存在不报错
            path.mkdir(parents=True, exist_ok=True)
        else:
            # 否则为文件
            # 首先确保父目录存在
            path.parent.mkdir(parents=True, exist_ok=True)
            print(f"创建文件: {path}")
            # 创建空文件
            path.touch()

if __name__ == "__main__":
    print("开始创建项目结构...")
    create_project_structure()
    print("\n项目结构创建完成！")