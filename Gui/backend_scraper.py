# backend_scraper.py

import logging
import os
import sys
import re
import subprocess
import time
from urllib.parse import urljoin, urlparse
import shutil
import requests
from bs4 import BeautifulSoup
import certifi
import undetected_chromedriver as uc

logger = logging.getLogger(__name__)

if os.name == "nt":
    CREATION_FLAGS = subprocess.CREATE_NO_WINDOW
else:
    CREATION_FLAGS = 0

RESOURCE_CATEGORIES = {
    "视频": (".mp4", ".mkv", ".avi", ".mov", ".flv", ".webm", ".ts", ".m3u8"),
    "音频": (".mp3", ".m4a", ".wav", ".aac", ".flac", ".ogg"),
    "图片": (".jpg", ".jpeg", ".png", ".gif", "bmp", ".webp", ".svg"),
    "压缩包": (".zip", ".rar", ".7z", ".tar", ".gz", ".iso"),
    "可执行/安装包": (".exe", ".msi", ".dmg", ".pkg", ".deb", ".rpm"),
    "文档": (".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".txt", ".md"),
}


def get_executable_path(filename):
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, filename)
    base_path = os.path.dirname(getattr(sys, "argv", [__file__])[0])
    local_path = os.path.join(base_path, filename)
    return local_path if os.path.exists(local_path) else filename


def create_requests_session(proxy_dict=None):
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
    )
    if proxy_dict:
        session.proxies = proxy_dict
    session.verify = certifi.where()
    return session


def extract_links_from_html(base_url, html_content):
    soup = BeautifulSoup(html_content, "html.parser")
    found_urls = set()
    for a_tag in soup.find_all("a", href=True):
        href = a_tag.get("href")
        if href and not href.startswith(("javascript:", "#", "data:")):
            found_urls.add(urljoin(base_url, href))
    for tag in soup.find_all(["img", "video", "audio", "source"], src=True):
        src = tag.get("src")
        if (
            src
            and isinstance(src, str)
            and not src.startswith(("javascript:", "#", "data:"))
        ):
            found_urls.add(urljoin(base_url, src))
    verified_links = []
    for link_url in found_urls:
        path = urlparse(link_url).path
        _, ext = os.path.splitext(path)
        if ext:
            for category, extensions in RESOURCE_CATEGORIES.items():
                if ext.lower() in extensions:
                    verified_links.append(
                        {
                            "url": link_url,
                            "filename": os.path.basename(path) or "unknown",
                            "category": category,
                            "ext": ext.lower(),
                        }
                    )
                    break
    return verified_links


# --- 嗅探引擎模块 ---


def sniff_engine_direct_link_checker(url, proxy_dict=None, context_worker=None):
    logger.info(f"引擎[Direct Checker]: 检查URL -> {url}")
    session = create_requests_session(proxy_dict)
    try:
        response = session.head(url, timeout=15, allow_redirects=True)
        if context_worker and not context_worker._is_running:
            return {"error": "操作被用户取消。"}
        response.raise_for_status()
        content_type = response.headers.get("content-type", "").lower()
        if "text/html" in content_type:
            return {
                "error": "内容是HTML页面，非直接文件。",
                "engine": "direct_link_checker",
            }
        filename = ""
        if "content-disposition" in response.headers:
            disp_match = re.search(
                r'filename="?([^"]+)"?', response.headers["content-disposition"]
            )
            if disp_match:
                filename = disp_match.group(1)
        if not filename:
            filename = os.path.basename(urlparse(response.url).path) or "unknown_file"
        _, ext = os.path.splitext(filename)
        category = next(
            (cat for cat, exts in RESOURCE_CATEGORIES.items() if ext.lower() in exts),
            "其他",
        )
        link_info = {
            "url": response.url,
            "filename": filename,
            "category": category,
            "ext": ext.lower(),
            "size": int(response.headers.get("content-length", 0)),
            "mime": content_type.split(";")[0],
        }
        return {
            "links": [link_info],
            "title": filename,
            "engine": "direct_link_checker",
        }
    except requests.RequestException as e:
        if context_worker and not context_worker._is_running:
            return {"error": "操作被用户取消。"}
        return {"error": f"网络请求失败: {e}", "engine": "direct_link_checker"}


def sniff_engine_github_api(url, proxy_dict=None, context_worker=None):
    logger.info(f"引擎[GitHub API]: 开始深度解析GitHub URL -> {url}")
    repo_match = re.search(r"github\.com/([^/]+)/([^/]+)", url)
    if not repo_match:
        return {"error": "URL中未找到 'owner/repo' 格式。", "engine": "github_api"}
    owner, repo = repo_match.group(1), repo_match.group(2).replace(".git", "").strip(
        "/"
    )
    api_url = f"https://api.github.com/repos/{owner}/{repo}/releases/latest"
    if tag_match := re.search(r"/releases/tag/([^/?#]+)", url):
        api_url = f"https://api.github.com/repos/{owner}/{repo}/releases/tags/{tag_match.group(1)}"
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "Ultimate-Sniffer-App/1.0",
    }
    if token := os.environ.get("GITHUB_TOKEN"):
        headers["Authorization"] = f"token {token}"
    session = create_requests_session(proxy_dict)
    session.headers.update(headers)
    try:
        response = session.get(api_url, timeout=30)
        if context_worker and not context_worker._is_running:
            return {"error": "操作被用户取消。"}
        response.raise_for_status()
        data = response.json()
        if isinstance(data, list) and not data:
            return {"error": "该仓库没有任何发布版本。", "engine": "github_api"}
        if isinstance(data, list):
            data = data[0]
        links = [
            {
                "url": asset.get("browser_download_url"),
                "filename": asset.get("name"),
                "category": next(
                    (
                        cat
                        for cat, exts in RESOURCE_CATEGORIES.items()
                        if os.path.splitext(asset.get("name"))[1].lower() in exts
                    ),
                    "其他",
                ),
                "size": asset.get("size"),
                "mime": asset.get("content_type"),
                "ext": os.path.splitext(asset.get("name"))[1].lower(),
            }
            for asset in data.get("assets", [])
            if asset.get("browser_download_url") and asset.get("name")
        ]
        if not links:
            return {
                "error": "此发布版本下未找到任何资源文件(assets)。",
                "engine": "github_api",
            }
        return {
            "links": links,
            "title": data.get("name", f"{owner}/{repo} - {data.get('tag_name')}"),
            "engine": "github_api",
        }
    except requests.RequestException as e:
        if context_worker and not context_worker._is_running:
            return {"error": "操作被用户取消。"}
        msg = f"GitHub API 请求失败: {e}"
        if (
            hasattr(e, "response")
            and e.response is not None
            and e.response.status_code == 403
        ):
            msg += " 也可能是速率限制已超额，请设置 GITHUB_TOKEN 环境变量。"
        return {"error": msg, "engine": "github_api"}


def sniff_engine_html_parser(url, proxy_dict=None, context_worker=None):
    logger.info(f"引擎[HTML]: 开始嗅探 {url}")
    session = create_requests_session(proxy_dict)
    try:
        with session.get(url, timeout=20, stream=True) as response:
            if context_worker and not context_worker._is_running:
                return {"error": "操作被用户取消。"}
            response.raise_for_status()
            content_type = response.headers.get("content-type", "").lower()
            if "text/html" not in content_type:
                return {"error": f"内容非HTML({content_type})", "engine": "html"}
            html_content = response.text
            if context_worker and not context_worker._is_running:
                return {"error": "操作被用户取消。"}
            soup = BeautifulSoup(html_content, "html.parser")
            title = soup.title.string.strip() if soup.title else "Untitled"
            links = extract_links_from_html(url, html_content)
            if not links:
                return {"error": "HTML引擎未发现可识别的链接。", "engine": "html"}
            return {"links": links, "title": title, "engine": "html"}
    except requests.RequestException as e:
        if context_worker and not context_worker._is_running:
            return {"error": "操作被用户取消。"}
        return {"error": f"网络请求失败: {e}", "engine": "html"}


def sniff_engine_browser(url, proxy_dict=None, context_worker=None):
    logger.info(f"引擎[浏览器]: 启动无头浏览器嗅探 {url}")
    options = uc.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    if proxy_dict and (proxy_url := proxy_dict.get("https://")):
        options.add_argument(f"--proxy-server={proxy_url}")
    driver = None
    try:
        driver = uc.Chrome(options=options)
        if context_worker:
            context_worker.register_stoppable_resource(driver)
        driver.get(url)
        for _ in range(7):
            if context_worker and not context_worker._is_running:
                raise InterruptedError("Browser task was cancelled during wait.")
            time.sleep(1)
        page_source, page_title = driver.page_source, driver.title
        links = extract_links_from_html(url, page_source)
        if not links:
            return {
                "error": "浏览器成功渲染页面，但未发现可识别的链接。",
                "engine": "browser",
            }
        return {"links": links, "title": page_title, "engine": "browser"}
    except Exception as e:
        if context_worker and not context_worker._is_running:
            return {"error": "操作被用户取消。"}
        if isinstance(e, InterruptedError):
            return {"error": "操作被用户取消。"}
        return {"error": f"浏览器引擎启动或执行失败: {e}", "engine": "browser"}
    finally:
        if context_worker:
            context_worker.unregister_stoppable_resource()
        if driver:
            driver.quit()


# --- 下载相关函数 ---


def build_download_command(url, format_codes, download_dir, proxy_dict=None):
    yt_dlp_exe = get_executable_path("yt-dlp.exe")
    output_template = os.path.join(download_dir, "%(title)s.f%(format_id)s.%(ext)s")
    if "+" in format_codes:
        output_template = os.path.join(download_dir, "%(title)s.%(ext)s")
    command = [
        yt_dlp_exe,
        "-f",
        format_codes,
        "--output",
        output_template,
        "--merge-output-format",
        "mp4",
        "--no-overwrites",
        "--no-mtime",
        "--no-warnings",
        "--progress",
        "--progress-template",
        "download-stream:%(progress._percent_str)s",
    ]
    ffmpeg_on_path = shutil.which("ffmpeg")
    if ffmpeg_on_path:
        logger.info(f"ffmpeg 在系统 PATH 中找到: {ffmpeg_on_path}")
    else:
        local_ffmpeg_path = get_executable_path("ffmpeg.exe")
        if os.path.exists(local_ffmpeg_path) and "ffmpeg.exe" in local_ffmpeg_path:
            logger.info(f"在本地目录找到 ffmpeg: {local_ffmpeg_path}")
            command.extend(["--ffmpeg-location", local_ffmpeg_path])
        else:
            logger.warning(
                "警告：在系统 PATH 或本地目录中均未找到 ffmpeg.exe。需要合并时操作会失败。"
            )
    if proxy_dict and (proxy_url := proxy_dict.get("https://")):
        command.extend(["--proxy", proxy_url])
    command.append(url)
    logger.info(f"生成的 yt-dlp 命令: {' '.join(command)}")
    return command


def download_direct_link(
    url, download_path, progress_callback=None, stop_callback=None, proxy_dict=None
):
    logger.info(f"直接下载链接: {url}")
    filepath = download_path
    try:
        session = create_requests_session(proxy_dict)
        with session.get(url, stream=True, timeout=(10, 300)) as r:
            r.raise_for_status()
            total_size = int(r.headers.get("content-length", 0))
            downloaded_size = 0
            with open(filepath, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if stop_callback and stop_callback():
                        f.close()
                        if os.path.exists(filepath):
                            os.remove(filepath)
                        return False, "下载被用户取消"
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        if total_size > 0 and progress_callback:
                            progress_callback(int((downloaded_size / total_size) * 100))
        if progress_callback:
            progress_callback(100)
        return True, "下载成功完成。"
    except requests.RequestException as e:
        if stop_callback and stop_callback():
            if os.path.exists(filepath):
                try:
                    os.remove(filepath)
                except OSError:
                    pass
            return False, "下载被用户取消"
        return False, f"网络请求失败: {e}"
    except Exception as e:
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
            except OSError:
                pass
        return False, f"下载过程中发生未知错误: {e}"
