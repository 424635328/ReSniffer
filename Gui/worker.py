# worker.py

import logging
import re
import os
import json
from urllib.parse import urlparse
from PyQt6.QtCore import QObject, pyqtSignal, QProcess
import undetected_chromedriver as uc

import backend_scraper
from strategy_profiler import (
    select_best_strategy,
    AVAILABLE_STRATEGIES,
    update_experience_data,
)

logger = logging.getLogger(__name__)


class Worker(QObject):
    """
    后台工作线程 (v3.1 - 最终异步版)
    所有外部进程调用均使用 QProcess，保证完全可中断。
    """

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
        self.stoppable_resource = None
        self.process_output_buffer = ""
        self.original_url = ""
        self.strategy_queue = []

    def register_stoppable_resource(self, resource):
        self.stoppable_resource = resource

    def unregister_stoppable_resource(self):
        self.stoppable_resource = None

    def run(self):
        if not self._is_running:
            return
        if self.task_type == "sniff":
            self._run_intelligent_sniff()
        elif self.task_type == "download":
            self._run_download()

    def _run_intelligent_sniff(self):
        self.original_url = self.kwargs.get("url")
        self.log.emit(f"后台：启动智能策略嗅探 -> {self.original_url}")

        self.strategy_queue = select_best_strategy(self.original_url)
        if not self.strategy_queue:
            if self._is_running:
                self.sniff_finished.emit(
                    {"error": "没有适用的嗅探策略。"}, self.original_url
                )
            return

        self._process_next_strategy()

    def _process_next_strategy(self):
        if not self._is_running:
            self.sniff_finished.emit({"error": "操作被用户取消。"}, self.original_url)
            return

        if not self.strategy_queue:
            self.sniff_finished.emit(
                {"error": "所有推荐的嗅探策略均已尝试。"}, self.original_url
            )
            return

        strategy_name = self.strategy_queue.pop(0)
        self.log.emit(f"<b>策略执行: 尝试使用 '{strategy_name}' 引擎...</b>")

        if strategy_name == "yt_dlp":
            self._run_yt_dlp_sniff_qprocess(self.original_url)
        else:
            backend_function_name = AVAILABLE_STRATEGIES.get(strategy_name)
            if not backend_function_name:
                self.log.emit(
                    f"<font color='red'>配置错误：策略 '{strategy_name}' 没有对应的后端函数。</font>"
                )
                self._process_next_strategy()
                return
            try:
                backend_function = getattr(backend_scraper, backend_function_name)
                result = backend_function(self.original_url, context_worker=self)
                self._handle_sniff_result(result, strategy_name)
            except Exception as e:
                self._handle_sniff_result(
                    {"error": f"执行后端函数时发生意外错误: {e}"}, strategy_name
                )

    def _handle_sniff_result(self, result, strategy_name):
        if result and not result.get("error"):
            self.log.emit(
                f"<font color='green'>策略 '{strategy_name}' 成功找到资源！</font>"
            )
            try:
                update_experience_data(
                    urlparse(self.original_url).netloc, strategy_name
                )
            except Exception as e:
                logger.warning(f"更新经验数据失败: {e}")
            self.sniff_finished.emit(result, self.original_url)
        else:
            error_msg = result.get("error", "未知错误") if result else "未知错误"
            self.log.emit(f"策略 '{strategy_name}' 失败: {error_msg}")
            self._process_next_strategy()

    def _run_yt_dlp_sniff_qprocess(self, url):
        yt_dlp_exe = backend_scraper.get_executable_path("yt-dlp.exe")
        if not os.path.exists(yt_dlp_exe):
            self._handle_sniff_result({"error": "yt-dlp.exe 未找到"}, "yt_dlp")
            return

        command = [yt_dlp_exe, "--dump-json", "--no-warnings", url]
        self.process = QProcess()
        self.process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        self.process_output_buffer = ""

        def handle_output():
            self.process_output_buffer += (
                self.process.readAllStandardOutput()
                .data()
                .decode("utf-8", errors="ignore")
            )

        def handle_finish(exit_code, exit_status):
            handle_output()
            result = {}
            if not self._is_running:
                result = {"error": "操作被用户取消。"}
            elif exit_code == 0:
                try:
                    json_line = self.process_output_buffer.strip().split("\n")[0]
                    data = json.loads(json_line)
                    data["engine"] = "yt-dlp"
                    result = data
                except Exception as e:
                    result = {"error": f"解析yt-dlp输出失败: {e}"}
            else:
                result = {"error": f"yt-dlp 执行失败 (代码: {exit_code})"}
            self.process = None
            self._handle_sniff_result(result, "yt_dlp")

        self.process.readyReadStandardOutput.connect(handle_output)
        self.process.finished.connect(handle_finish)
        self.process.start(command[0], command[1:])

    def _run_download(self):
        resource_type = self.kwargs.get("resource_type")
        if resource_type == "yt-dlp":
            self._run_yt_dlp_download_qprocess()
        else:
            self._run_direct_download()

    def _run_yt_dlp_download_qprocess(self):
        if not self._is_running:
            self.download_finished.emit(False, "任务在启动前被取消。")
            return
        url, formats, download_path = (
            self.kwargs.get("url"),
            self.kwargs.get("formats"),
            self.kwargs.get("download_path"),
        )
        command_list = backend_scraper.build_download_command(
            url, formats, download_path
        )
        self.process = QProcess()
        self.process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        self.process.readyReadStandardOutput.connect(self._on_yt_dlp_output)
        self.process.finished.connect(self._on_yt_dlp_finished)
        self.process.start(command_list[0], command_list[1:])

    def _on_yt_dlp_output(self):
        if not self.process:
            return
        output = (
            self.process.readAllStandardOutput().data().decode("utf-8", errors="ignore")
        )
        progress_pattern = re.compile(r"download-stream:(\s*\d+\.?\d*%)")
        for line in output.splitlines():
            if line.strip():
                self.log.emit(f"[yt-dlp] {line.strip()}")
            if match := progress_pattern.search(line):
                try:
                    self.download_progress.emit(
                        int(float(match.group(1).strip().replace("%", "")))
                    )
                except (ValueError, IndexError):
                    pass

    def _on_yt_dlp_finished(self, exit_code, exit_status):
        self._on_yt_dlp_output()
        if not self._is_running:
            self.download_finished.emit(False, "操作被用户取消。")
        elif exit_code == 0:
            self.download_progress.emit(100)
            self.download_finished.emit(True, "下载成功完成。")
        else:
            status_msg = (
                "崩溃" if exit_status == QProcess.ExitStatus.CrashExit else "正常退出"
            )
            self.download_finished.emit(
                False, f"下载失败 (代码: {exit_code}, 状态: {status_msg})"
            )
        self.process = None

    def _run_direct_download(self):
        if not self._is_running:
            self.download_finished.emit(False, "任务在启动前被取消。")
            return
        direct_url = self.kwargs.get("direct_url")
        download_path = self.kwargs.get("download_path")
        stop_callback = lambda: not self._is_running
        success, msg = backend_scraper.download_direct_link(
            direct_url,
            download_path,
            progress_callback=self.download_progress.emit,
            stop_callback=stop_callback,
        )
        if self._is_running:
            self.download_finished.emit(success, msg)
        else:
            self.download_finished.emit(False, "操作被用户取消。")

    def stop(self):
        self.log.emit("后台：收到停止请求，正在执行...")
        self._is_running = False
        if (
            isinstance(self.process, QProcess)
            and self.process.state() != QProcess.ProcessState.NotRunning
        ):
            try:
                self.log.emit(f"正在终止 QProcess (PID: {self.process.processId()})...")
                self.process.kill()
            except Exception as e:
                logger.error(f"终止 QProcess 时发生未知错误: {e}")
        elif self.stoppable_resource:
            try:
                if isinstance(self.stoppable_resource, uc.Chrome):
                    self.log.emit("正在关闭浏览器驱动...")
                    self.stoppable_resource.quit()
            except Exception as e:
                logger.error(f"停止嗅探资源时出错: {e}")
            finally:
                self.unregister_stoppable_resource()
        else:
            self.log.emit("没有活动的嗅探资源或下载子进程需要停止。")
