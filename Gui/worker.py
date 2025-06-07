# worker.py

import logging
import re
import subprocess
import os
from urllib.parse import urlparse
from PyQt6.QtCore import QObject, pyqtSignal

import backend_scraper
from strategy_profiler import select_best_strategy, AVAILABLE_STRATEGIES, update_experience_data

logger = logging.getLogger(__name__)

if os.name == 'nt':
    CREATION_FLAGS = subprocess.CREATE_NO_WINDOW
else:
    CREATION_FLAGS = 0

class Worker(QObject):
    sniff_finished = pyqtSignal(dict, str)
    download_finished = pyqtSignal(bool, str)
    download_progress = pyqtSignal(int)
    log = pyqtSignal(str)

    def __init__(self, task_type, **kwargs):
        super().__init__()
        self.task_type = task_type
        self.kwargs = kwargs
        self.process = None
        self._is_running = True

    def run(self):
        if not self._is_running: return

        if self.task_type == "sniff":
            self._run_intelligent_sniff()
        elif self.task_type == "download":
            self._run_download()

    def _run_intelligent_sniff(self):
        original_url = self.kwargs.get("url")
        self.log.emit(f"后台：启动贝叶斯策略嗅探 -> {original_url}")
        strategy_queue = select_best_strategy(original_url)

        if not strategy_queue:
            self.log.emit("<font color='red'>错误：没有找到适用于此URL的嗅探策略。</font>")
            if self._is_running:
                self.sniff_finished.emit({"error": "没有适用的嗅探策略。"}, original_url)
            return

        final_result = None
        for strategy_name in strategy_queue:
            if not self._is_running:
                self.log.emit("嗅探操作被用户取消。")
                # 不再发送信号，因为主窗口已经处理了停止状态
                break

            self.log.emit(f"<b>策略执行: 尝试使用 '{strategy_name}' 引擎...</b>")
            
            backend_function_name = AVAILABLE_STRATEGIES.get(strategy_name)
            if not backend_function_name:
                self.log.emit(f"<font color='red'>配置错误：策略 '{strategy_name}' 没有对应的后端函数。</font>")
                continue
            
            if strategy_name == "direct_link":
                path = urlparse(original_url).path; filename = os.path.basename(path); _, ext = os.path.splitext(path)
                final_result = {"links": [{"url": original_url, "filename": filename, "category": "直接链接", "ext": ext}], "title": filename, "engine": "direct_link"}
                self.log.emit(f"<font color='green'>策略 '{strategy_name}' 成功。</font>")
                break
            
            try:
                backend_function = getattr(backend_scraper, backend_function_name)
                # [说明] 这里的 backend_function 调用是阻塞点
                result = backend_function(original_url)
            except AttributeError:
                msg = f"代码错误：后端模块中未找到函数 '{backend_function_name}'。"
                self.log.emit(f"<font color='red'>{msg}</font>"); final_result = {"error": msg}; break
            except Exception as e:
                result = {"error": f"执行后端函数时发生意外错误: {e}"}

            if result and not result.get("error"):
                self.log.emit(f"<font color='green'>策略 '{strategy_name}' 成功找到资源！</font>")
                final_result = result
                try:
                    domain = urlparse(original_url).netloc
                    update_experience_data(domain, strategy_name)
                except Exception as e:
                    logger.warning(f"更新经验数据失败: {e}")
                break
            else:
                error_msg = result.get("error", "未知错误")
                self.log.emit(f"策略 '{strategy_name}' 失败: {error_msg}")

        if self._is_running:
            if not final_result:
                final_result = {"error": "所有推荐的嗅探策略均已尝试，未能找到任何资源。"}
            self.sniff_finished.emit(final_result, original_url)
        else:
            # 如果是因为取消而退出循环，也需要通知UI任务结束
             self.sniff_finished.emit({"error": "操作被用户取消。"}, original_url)

    def _run_download(self):
        resource_type = self.kwargs.get("resource_type")
        if resource_type == "yt-dlp":
            self._run_yt_dlp_download()
        else: # "direct"
            self._run_direct_download()
            
    def _run_yt_dlp_download(self):
        url, formats, download_path = self.kwargs.get("url"), self.kwargs.get("formats"), self.kwargs.get("download_path")
        command = backend_scraper.build_download_command(url, formats, download_path)
        
        try:
            self.process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8', errors='ignore', creationflags=CREATION_FLAGS)
        except Exception as e:
            if not self._is_running: return
            logger.error(f"启动 yt-dlp 下载进程时出错: {e}")
            self.download_finished.emit(False, f"启动下载失败: {e}")
            return

        try:
            progress_pattern = re.compile(r"download-stream:(\s*\d+\.?\d*%)")
            for line in self.process.stdout:
                line_strip = line.strip()
                if line_strip: self.log.emit(f"[yt-dlp] {line_strip}")
                if match := progress_pattern.search(line):
                    percentage = int(float(match.group(1).strip().replace('%', '')))
                    self.download_progress.emit(percentage)
            
            return_code = self.process.wait()
            if not self._is_running: self.download_finished.emit(False, "操作被用户取消。")
            elif return_code == 0: self.download_progress.emit(100); self.download_finished.emit(True, "下载成功完成。")
            else: self.download_finished.emit(False, f"下载失败，进程返回码: {return_code}")
        except Exception as e:
            if not self._is_running: self.download_finished.emit(False, "操作被用户取消。")
            else:
                logger.error(f"监控下载进程时发生未知错误: {e}")
                self.download_finished.emit(False, f"监控下载时发生错误: {e}")
        finally:
            self.process = None

    def _run_direct_download(self):
        if not self._is_running: return
        direct_url = self.kwargs.get("direct_url")
        download_path = self.kwargs.get("download_path")
        stop_callback = lambda: not self._is_running

        success, msg = backend_scraper.download_direct_link(direct_url, download_path, progress_callback=self.download_progress.emit, stop_callback=stop_callback)
        
        if self._is_running: self.download_finished.emit(success, msg)
        else: self.download_finished.emit(False, "操作被用户取消。")
            
    def stop(self):
        self.log.emit("后台：收到停止请求，正在执行...")
        self._is_running = False
        if self.process and self.process.poll() is None:
            try:
                self.log.emit(f"正在终止子进程 (PID: {self.process.pid})...")
                self.process.terminate()
            except Exception as e:
                logger.error(f"终止进程时发生未知错误: {e}")
                self.log.emit(f"<font color='red'>终止进程时出错: {e}</font>")
        else:
            self.log.emit("没有活动的子进程需要停止。")