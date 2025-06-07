# strategy_profiler.py (终极智能增强版 v2)

import logging
from urllib.parse import urlparse
import os
import re
import json

logger = logging.getLogger(__name__)

# --- [优化] 策略元数据：统一管理策略信息 ---
# 成本：1=极低, 2=低, 3=中, 5=高, 10=极高(浏览器)
STRATEGY_METADATA = {
    # 验证一个链接是否是直接文件
    "direct_link_checker": {"backend": "sniff_engine_direct_link_checker", "cost": 2},
    # 专用API，高效准确
    "github_api":     {"backend": "sniff_engine_github_api", "cost": 2},
    # 通用视频网站解析器，功能强大但成本中等
    "yt_dlp":         {"backend": "sniff_engine_yt_dlp", "cost": 5},
    # 基础HTML解析，成本低但功能有限
    "html_parser":    {"backend": "sniff_engine_html_parser", "cost": 3},
    # JS渲染，成本极高，作为最后手段
    "browser":        {"backend": "sniff_engine_browser", "cost": 10},
}
AVAILABLE_STRATEGIES = {name: data["backend"] for name, data in STRATEGY_METADATA.items()}

# --- [优化] 动态经验数据管理 ---
EXPERIENCE_FILE = "strategy_experience.json"
experience_data = {}

def load_experience_data():
    """从文件加载经验数据。"""
    global experience_data
    if os.path.exists(EXPERIENCE_FILE):
        try:
            with open(EXPERIENCE_FILE, 'r') as f:
                experience_data = json.load(f)
                logger.info("经验数据加载成功。")
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"加载经验数据失败: {e}。将使用空数据。")
            experience_data = {}
    else:
        logger.info("经验数据文件不存在，将创建新的。")
        experience_data = {}

def save_experience_data():
    """将经验数据保存到文件。"""
    try:
        with open(EXPERIENCE_FILE, 'w') as f:
            json.dump(experience_data, f, indent=2)
    except IOError as e:
        logger.error(f"保存经验数据失败: {e}")

def update_experience_data(domain, successful_strategy):
    """
    [优化] 更新并持久化经验数据。
    每次成功，对应策略的权重增加。
    """
    domain = re.sub(r'^www\.', '', domain) # 移除 'www.'
    if domain not in experience_data:
        experience_data[domain] = {}
    
    # 将成功的策略权重+1，其他策略保持不变
    current_weight = experience_data[domain].get(successful_strategy, 0)
    experience_data[domain][successful_strategy] = current_weight + 1
    
    logger.info(f"经验数据已更新: {{'{domain}': {experience_data[domain]}}}")
    save_experience_data()

# --- [优化] 主决策函数：规则优先，评分兜底 ---

def select_best_strategy(url: str) -> list[str]:
    """
    [重构] 对URL应用一系列规则和评分，生成最佳策略队列。
    """
    logger.info(f"为URL '{url}' 进行智能策略评估...")
    try:
        url_info = urlparse(url)
        domain = re.sub(r'^www\.', '', url_info.netloc)
        path = url_info.path
    except Exception as e:
        logger.error(f"URL解析失败: {e}"); return []

    # --- 第一部分：强规则匹配 (Rule-Based Matching) ---
    # 如果满足强规则，直接返回预设的策略队列，保证核心场景的准确性。

    # 规则 1: GitHub Release 页面
    if 'github.com' in domain and '/releases' in path:
        logger.info("决策[强规则]: 检测到 GitHub Release 页面。")
        return ["github_api", "browser", "html_parser"]
        
    # 规则 2: 已知文件扩展名
    known_exts = ('.mp4', '.mkv', '.zip', '.rar', '.exe', '.msi', '.pdf', '.mp3', '.iso', '.dmg', '.pkg')
    if path.lower().endswith(known_exts):
        logger.info("决策[强规则]: URL 以已知文件扩展名结尾。")
        return ["direct_link_checker", "yt_dlp"]

    # 规则 3: 已知视频网站的特定页面格式
    if 'youtube.com' in domain and ('/watch' in path or '/shorts/' in path):
        logger.info("决策[强规则]: 检测到 YouTube 视频页面。")
        return ["yt_dlp"]
    if 'bilibili.com' in domain and '/video/' in path:
        logger.info("决策[强规则]: 检测到 Bilibili 视频页面。")
        return ["yt_dlp"]

    # --- 第二部分：评分系统 (Scoring System) ---
    # 如果没有匹配到强规则，则进入评分系统，对所有策略进行评估。
    logger.info("决策[评分系统]: 未匹配到强规则，进入通用评分模式。")
    scores = {}

    # 1. 基础置信度分数 (0-100)
    # 每个策略对自己处理这个URL的信心打分
    scores['yt_dlp'] = 70 if any(site in domain for site in ['vimeo.com', 'douyin.com', 'ixigua.com']) else 40
    scores['browser'] = 50 if not os.path.splitext(path)[1] else 20 # 对动态页面更有信心
    scores['html_parser'] = 30 # 作为基础的解析器，信心不高
    scores['direct_link_checker'] = 25 # 任何页面都可能是伪装的直接链接，给个低保分
    scores['github_api'] = 10 # 除非是GitHub域名，否则信心很低

    # 2. 调整分数：应用经验数据和成本惩罚
    final_scores = {}
    for strategy, base_score in scores.items():
        # 应用经验加成
        experience_weight = 0
        if domain in experience_data and strategy in experience_data[domain]:
            # 将总使用次数作为权重，但设置上限防止无限增长
            experience_weight = min(experience_data[domain][strategy], 10) * 5 # 每次成功 +5 分，最多 +50
        
        # 应用成本惩罚
        cost = STRATEGY_METADATA[strategy]["cost"]
        # 成本越高，基础分的"衰减"越严重
        cost_penalty = (11 - cost) / 10 # 成本1->衰减1.0, 成本10->衰减0.1

        final_score = base_score * cost_penalty + experience_weight
        final_scores[strategy] = final_score
        
    # 按最终分数降序排序
    sorted_strategies = sorted(final_scores.items(), key=lambda item: item[1], reverse=True)
    
    # 格式化日志输出
    log_output = [(s, f"{v:.2f}") for s, v in sorted_strategies]
    logger.info(f"策略评估结果 (策略, 最终得分): {log_output}")
    
    # 返回分数大于阈值的策略队列
    return [strategy for strategy, score in sorted_strategies if score > 20]

# --- 程序启动时加载一次经验数据 ---
load_experience_data()