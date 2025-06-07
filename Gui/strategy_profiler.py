# strategy_profiler.py

import logging
from urllib.parse import urlparse
import re
import os
import json

logger = logging.getLogger(__name__)

# [最终版] yt-dlp 不再有后端映射，完全由 worker 特殊处理
STRATEGY_METADATA = {
    "direct_link_checker": {"backend": "sniff_engine_direct_link_checker", "cost": 2},
    "github_api": {"backend": "sniff_engine_github_api", "cost": 2},
    "yt_dlp": {"backend": None, "cost": 5},
    "html_parser": {"backend": "sniff_engine_html_parser", "cost": 3},
    "browser": {"backend": "sniff_engine_browser", "cost": 10},
}
AVAILABLE_STRATEGIES = {
    name: data["backend"]
    for name, data in STRATEGY_METADATA.items()
    if data["backend"] is not None
}

EXPERIENCE_FILE = "strategy_experience.json"
experience_data = {}


def load_experience_data():
    global experience_data
    if os.path.exists(EXPERIENCE_FILE):
        try:
            with open(EXPERIENCE_FILE, "r") as f:
                experience_data = json.load(f)
                logger.info("经验数据加载成功。")
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"加载经验数据失败: {e}。")
            experience_data = {}
    else:
        experience_data = {}


def save_experience_data():
    try:
        with open(EXPERIENCE_FILE, "w") as f:
            json.dump(experience_data, f, indent=2)
    except IOError as e:
        logger.error(f"保存经验数据失败: {e}")


def update_experience_data(domain, successful_strategy):
    domain = re.sub(r"^www\.", "", domain)
    if domain not in experience_data:
        experience_data[domain] = {}
    current_weight = experience_data[domain].get(successful_strategy, 0)
    experience_data[domain][successful_strategy] = current_weight + 1
    logger.info(f"经验数据已更新: {{'{domain}': {experience_data[domain]}}}")
    save_experience_data()


def select_best_strategy(url: str) -> list[str]:
    logger.info(f"为URL '{url}' 进行智能策略评估...")
    try:
        url_info = urlparse(url)
        domain = re.sub(r"^www\.", "", url_info.netloc)
        path = url_info.path
    except Exception as e:
        logger.error(f"URL解析失败: {e}")
        return []

    # 强规则匹配
    if "github.com" in domain and "/releases" in path:
        return ["github_api", "browser", "html_parser"]
    known_exts = (
        ".mp4",
        ".mkv",
        ".zip",
        ".rar",
        ".exe",
        ".msi",
        ".pdf",
        ".mp3",
        ".iso",
        ".dmg",
        ".pkg",
    )
    if path.lower().endswith(known_exts):
        return ["direct_link_checker", "yt_dlp"]
    if "youtube.com" in domain and ("/watch" in path or "/shorts/" in path):
        return ["yt_dlp"]
    if "bilibili.com" in domain and "/video/" in path:
        return ["yt_dlp"]

    # 评分系统
    scores = {
        "yt_dlp": (
            70
            if any(site in domain for site in ["vimeo.com", "douyin.com", "ixigua.com"])
            else 40
        ),
        "browser": 50 if not os.path.splitext(path)[1] else 20,
        "html_parser": 30,
        "direct_link_checker": 25,
        "github_api": 10,
    }
    final_scores = {}
    for strategy, base_score in scores.items():
        experience_weight = 0
        if domain in experience_data and strategy in experience_data[domain]:
            experience_weight = min(experience_data[domain][strategy], 10) * 5
        cost = STRATEGY_METADATA[strategy]["cost"]
        cost_penalty = (11 - cost) / 10
        final_scores[strategy] = base_score * cost_penalty + experience_weight

    sorted_strategies = sorted(
        final_scores.items(), key=lambda item: item[1], reverse=True
    )
    logger.info(
        f"策略评估结果 (策略, 最终得分): {[(s, f'{v:.2f}') for s, v in sorted_strategies]}"
    )
    return [strategy for strategy, score in sorted_strategies if score > 20]


load_experience_data()
