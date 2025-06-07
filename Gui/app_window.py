# app_window.py

import logging
import os
import time
from urllib.parse import urlparse
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
    QMessageBox, QTextEdit, QSplitter, QTreeWidget, QTreeWidgetItem, QHeaderView,
    QStatusBar, QMenu, QFileDialog, QTreeWidgetItemIterator, QCheckBox, QApplication,
    QFrame, QStyle, QLabel, QProgressBar
)
from PyQt6.QtCore import QThread, QSettings, QDir, Qt, QPoint
from PyQt6.QtGui import QFont, QIcon, QAction,  QBrush, QColor

from worker import Worker  # 确保 worker.py 在同一目录下

logger = logging.getLogger(__name__)

class AppWindow(QMainWindow):
    """
    应用程序的主窗口类。
    [优化] 负责构建UI、处理用户交互、管理后台工作线程以及状态更新。
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("终极资源嗅探下载器 v2.5 (优化版)")
        self.setGeometry(100, 100, 1200, 800)

        # --- 初始化状态和设置 ---
        self.download_queue = []
        self.worker_thread = None
        self.worker = None
        self.is_busy = False
        self.settings = QSettings("MyCompany", "UltimateSnifferGUI")
        self.current_task_data = {}
        self.current_download_base_url = ""

        self.setup_ui()
        self.connect_signals()
        self.load_settings()
        self.set_controls_for_idle()

    def setup_ui(self):
        """UI构建部分保持不变，无需修改。"""
        # --- 创建控件 ---
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("在此处粘贴要嗅探的URL")
        self.url_input.setFont(QFont("Segoe UI", 10))
        
        self.sniff_button = QPushButton(" 嗅探资源")
        self.sniff_button.setObjectName("SniffButton")

        self.task_tree = QTreeWidget()
        self.task_tree.setHeaderLabels(["任务URL", "标题"])
        self.task_tree.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.task_tree.header().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.task_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)

        self.resource_tree = QTreeWidget()
        self.resource_tree.setHeaderLabels(["资源/格式", "类型/编码", "分辨率", "大小", "链接/备注"])
        self.resource_tree.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.resource_tree.header().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.resource_tree.header().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.resource_tree.setSelectionMode(QTreeWidget.SelectionMode.ExtendedSelection)

        self.path_input = QLineEdit()
        self.path_input.setReadOnly(True)
        self.browse_button = QPushButton(" 浏览...")

        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setFont(QFont("Courier New", 9))

        self.merge_audio_checkbox = QCheckBox("自动合并最佳音轨")
        self.merge_audio_checkbox.setChecked(True)
        self.merge_audio_checkbox.setToolTip("勾选后，仅需选择视频流，程序将为每个视频流自动匹配最佳音轨进行合并。\n对直接下载链接无效。")
        
        self.download_button = QPushButton(" 下载选中项")
        self.download_button.setObjectName("StartButton")
        
        self.stop_button = QPushButton(" 停止操作")
        self.stop_button.setObjectName("StopButton")

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("%p%")

        # --- 设置图标 ---
        style = self.style()
        self.sniff_button.setIcon(style.standardIcon(QStyle.StandardPixmap.SP_FileDialogContentsView))
        self.download_button.setIcon(style.standardIcon(QStyle.StandardPixmap.SP_ArrowDown))
        self.stop_button.setIcon(style.standardIcon(QStyle.StandardPixmap.SP_MediaStop))
        self.browse_button.setIcon(style.standardIcon(QStyle.StandardPixmap.SP_DirOpenIcon))

        # --- 使用 QFrame 进行视觉分组 ---
        url_frame = QFrame()
        url_frame.setObjectName("UrlFrame")
        url_layout = QHBoxLayout(url_frame)
        url_layout.setContentsMargins(15, 10, 15, 10)
        url_layout.addWidget(QLabel("URL:"))
        url_layout.addWidget(self.url_input, 1)
        url_layout.addWidget(self.sniff_button)

        download_frame = QFrame()
        download_frame.setObjectName("DownloadFrame")
        download_layout = QVBoxLayout(download_frame)
        download_layout.setContentsMargins(15, 10, 15, 10)
        
        path_layout = QHBoxLayout()
        path_layout.addWidget(QLabel("下载到:"))
        path_layout.addWidget(self.path_input, 1)
        path_layout.addWidget(self.browse_button)
        
        action_layout = QHBoxLayout()
        action_layout.addWidget(self.merge_audio_checkbox)
        action_layout.addStretch()
        action_layout.addWidget(self.download_button)
        action_layout.addWidget(self.stop_button)
        
        download_layout.addLayout(path_layout)
        download_layout.addLayout(action_layout)
        download_layout.addWidget(self.progress_bar)

        # --- 主要布局 ---
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 5, 0)
        left_layout.addWidget(url_frame)
        left_layout.addWidget(QLabel("任务列表:"))
        left_layout.addWidget(self.task_tree)

        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(5, 0, 0, 0)
        right_layout.addWidget(QLabel("资源详情:"))
        right_layout.addWidget(self.resource_tree)
        right_layout.addWidget(download_frame)
        
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        main_splitter.addWidget(left_panel)
        main_splitter.addWidget(right_panel)
        main_splitter.setSizes([450, 750])

        bottom_splitter = QSplitter(Qt.Orientation.Vertical)
        bottom_splitter.addWidget(main_splitter)
        bottom_splitter.addWidget(self.log_output)
        bottom_splitter.setSizes([600, 200])

        central_widget = QWidget()
        main_v_layout = QVBoxLayout(central_widget)
        main_v_layout.addWidget(bottom_splitter)
        self.setCentralWidget(central_widget)
        self.setStatusBar(QStatusBar(self))

    def connect_signals(self):
        """连接信号和槽，保持不变。"""
        self.sniff_button.clicked.connect(self.start_sniffing)
        self.url_input.returnPressed.connect(self.start_sniffing)
        self.task_tree.currentItemChanged.connect(self.display_resources)
        self.task_tree.customContextMenuRequested.connect(self.show_task_context_menu)
        self.browse_button.clicked.connect(self.browse_path)
        self.download_button.clicked.connect(self.prepare_downloads)
        self.stop_button.clicked.connect(self.stop_task)

    # --- [优化] 核心任务管理逻辑 ---

    def start_task(self, task_type, **kwargs):
        """[新增] 统一的线程启动器，管理线程生命周期。"""
        if self.is_busy:
            self.log_output.append("<font color='orange'>警告：已有任务在运行。</font>")
            return

        self.is_busy = True
        if task_type == 'sniff':
            self.set_controls_for_busy("正在嗅探...")
        else: # 'download'
            # 消息在 process_next_in_queue 中设置
            pass 

        self.worker_thread = QThread()
        self.worker = Worker(task_type, **kwargs)
        self.worker.moveToThread(self.worker_thread)

        # 连接信号
        self.worker.log.connect(self.log_output.append)
        if task_type == 'sniff':
            self.worker.sniff_finished.connect(self.on_sniff_finished)
        elif task_type == 'download':
            self.worker.download_progress.connect(self.update_progress)
            self.worker.download_finished.connect(self.on_single_download_finished)

        # [说明] 线程完成后自动清理
        self.worker_thread.finished.connect(self.worker.deleteLater)
        self.worker_thread.finished.connect(self.worker_thread.deleteLater)
        self.worker_thread.finished.connect(self.clear_worker_references)
        
        self.worker_thread.started.connect(self.worker.run)
        self.worker_thread.start()

    def start_sniffing(self):
        url = self.url_input.text().strip()
        if not url: return
        self.log_output.append(f"<b>开始嗅探: {url}</b>")
        self.url_input.clear()
        self.start_task("sniff", url=url)

    def on_sniff_finished(self, data, url):
        # 正常结束，手动退出线程事件循环
        if self.worker_thread:
            self.worker_thread.quit()
        
        # UI更新逻辑
        existing_items = self.task_tree.findItems(url, Qt.MatchFlag.MatchExactly, 0)
        task_item = existing_items[0] if existing_items else QTreeWidgetItem(self.task_tree)
        task_item.setText(0, url)
        self.current_task_data[url] = data
        if data.get("error"):
            task_item.setText(1, f"[嗅探失败] {data['error']}")
            task_item.setForeground(1, QBrush(QColor("#ffc107")))
        else:
            title = data.get('title', '无标题')
            task_item.setText(1, title)
            task_item.setForeground(1, QBrush(self.palette().text().color()))
        if not existing_items: self.task_tree.addTopLevelItem(task_item)
        self.task_tree.setCurrentItem(task_item)
        
        self.is_busy = False
        self.set_controls_for_idle()

    def prepare_downloads(self):
        if self.is_busy: return
        current_task_item = self.task_tree.currentItem()
        if not current_task_item:
            QMessageBox.warning(self, "提示", "请先在左侧选择一个任务。")
            return
            
        self.current_download_base_url = current_task_item.text(0)
        self.download_queue.clear()
        yt_dlp_formats_manual = []
        auto_merge = self.merge_audio_checkbox.isChecked()
        iterator = QTreeWidgetItemIterator(self.resource_tree)
        
        while iterator.value():
            item = iterator.value()
            if item.checkState(0) == Qt.CheckState.Checked:
                download_info = item.data(0, Qt.ItemDataRole.UserRole)
                if not download_info: continue
                
                if download_info["type"] == "direct":
                    self.download_queue.append(download_info)
                elif download_info["type"] == "yt-dlp":
                    format_id = download_info.get('format_id')
                    if not format_id: continue
                    if auto_merge and download_info.get("is_video_only"):
                        self.download_queue.append({"type": "yt-dlp", "format_id": f"{format_id}+bestaudio"})
                    else:
                        if auto_merge:
                            self.download_queue.append({"type": "yt-dlp", "format_id": format_id})
                        else:
                             yt_dlp_formats_manual.append(format_id)
            iterator += 1
        
        if not auto_merge and yt_dlp_formats_manual:
            self.download_queue.append({"type": "yt-dlp", "format_id": "+".join(yt_dlp_formats_manual)})
            
        if not self.download_queue:
            QMessageBox.warning(self, "提示", "请在资源列表中勾选要下载的项目。")
            return
            
        self.log_output.append(f"<b>准备下载 {len(self.download_queue)} 个项目...</b>")
        self.process_next_in_queue()

    def process_next_in_queue(self):
        if not self.download_queue:
            self.log_output.append("<font color='#98c379'><b>所有下载任务已处理完毕！</b></font>")
            self.is_busy = False
            self.set_controls_for_idle()
            QMessageBox.information(self, "完成", "所有下载任务已处理完毕！")
            return
        
        task = self.download_queue.pop(0)
        self.set_controls_for_busy(f"正在下载 (队列剩余 {len(self.download_queue)} 个)...")
        
        worker_kwargs = {}
        download_dir = self.path_input.text()
        if not os.path.exists(download_dir):
            try:
                os.makedirs(download_dir)
            except OSError as e:
                self.log_output.append(f"<font color='red'>错误：无法创建下载目录: {e}</font>")
                self.on_single_download_finished(False, "无法创建下载目录。")
                return

        if task["type"] == "direct":
            filename = os.path.basename(urlparse(task['url']).path) or f"download_{int(time.time())}"
            filepath = os.path.join(download_dir, filename)
            worker_kwargs.update({"resource_type": "direct", "direct_url": task['url'], "download_path": filepath})
            self.log_output.append(f"<b>开始直接下载: {task['url']}</b>")
        else: # yt-dlp
            worker_kwargs.update({"resource_type": "yt-dlp", "url": self.current_download_base_url, "formats": task['format_id'], "download_path": download_dir})
            self.log_output.append(f"<b>开始yt-dlp下载: ...，格式: {task['format_id']}</b>")
        
        self.start_task("download", **worker_kwargs)

    def on_single_download_finished(self, success, message):
        # [优化] 无论成功、失败还是被取消，这个槽都会被调用
        if self.worker_thread:
            self.worker_thread.quit()

        is_cancelled = "被用户取消" in message
        if not is_cancelled:
            if success:
                self.log_output.append(f"<font color='#98c379'>项目下载成功。</font>")
            else:
                self.log_output.append(f"<font color='#e06c75'>项目下载失败: {message}</font>")
            
            # 继续处理队列中的下一个任务
            self.process_next_in_queue()
        else:
            # 如果是用户取消，则清空队列并重置UI
            self.download_queue.clear()
            self.log_output.append("<font color='orange'><b>下载队列已清空，操作被用户取消。</b></font>")
            self.is_busy = False
            self.set_controls_for_idle()

    def stop_task(self):
        """[优化] 健壮的停止逻辑。"""
        if self.worker and self.is_busy:
            self.log_output.append("<b>[用户操作] 发送停止信号...</b>")
            self.stop_button.setEnabled(False)
            self.stop_button.setText("正在停止...")
            self.worker.stop()
    
    def clear_worker_references(self):
        """[新增] 清理对worker和thread的引用，防止悬空指针。"""
        self.worker = None
        self.worker_thread = None
        if not self.is_busy: # 确保只有在任务真正结束后才恢复按钮
            self.stop_button.setText("停止操作")

    def closeEvent(self, event):
        """[优化] 优雅关闭事件处理。"""
        self.save_settings()
        if self.is_busy and self.worker_thread and self.worker_thread.isRunning():
            reply = QMessageBox.question(self, "确认退出", "任务仍在进行中，确定要退出吗？\n程序将尝试安全地停止任务。",
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                         QMessageBox.StandardButton.No)
            
            if reply == QMessageBox.StandardButton.Yes:
                self.log_output.append("<b>[程序关闭] 正在停止后台任务...</b>")
                self.stop_task()
                # 等待线程结束，设置5秒超时
                if not self.worker_thread.wait(5000):
                    self.log_output.append("<font color='red'>警告：线程在5秒内未响应退出，程序将强制关闭。</font>")
                else:
                    self.log_output.append("后台任务已安全停止。")
                event.accept()
            else:
                event.ignore()
        else:
            super().closeEvent(event)

    # --- 以下为UI辅助函数，大部分保持不变 ---
    def display_resources(self, current_item, previous_item):
        self.resource_tree.clear()
        if not current_item: return
        url = current_item.text(0)
        data = self.current_task_data.get(url)
        if not data or data.get("error"): return
        
        engine = data.get("engine")
        if engine == "yt-dlp": self.display_yt_dlp_resources(data)
        elif engine in ["html", "github_api", "direct_link", "browser"]: self.display_html_resources(data)

    def display_yt_dlp_resources(self, data):
        style = self.style(); video_icon = style.standardIcon(QStyle.StandardPixmap.SP_MediaPlay); audio_icon = style.standardIcon(QStyle.StandardPixmap.SP_MediaVolume)
        video_root = QTreeWidgetItem(self.resource_tree, ["视频流"]); video_root.setIcon(0, video_icon)
        audio_root = QTreeWidgetItem(self.resource_tree, ["音频流"]); audio_root.setIcon(0, audio_icon)
        for f in data.get("formats", []):
            is_video = f.get('vcodec') != 'none'; is_audio = f.get('acodec') != 'none'; is_video_only = is_video and not is_audio
            filesize = f"{(f.get('filesize') or f.get('filesize_approx', 0)) / 1024 / 1024:.2f} MB" if (f.get('filesize') or f.get('filesize_approx')) else "N/A"
            item_text = [f.get('format_note', f.get('format_id', 'N/A')), f"{f.get('vcodec', 'none')} / {f.get('acodec', 'none')}", f.get('resolution', '纯音频'), filesize, f.get('ext', 'N/A')]
            parent = video_root if is_video else audio_root
            item = QTreeWidgetItem(parent, item_text)
            item.setData(0, Qt.ItemDataRole.UserRole, {"type": "yt-dlp", "format_id": f.get('format_id'), "is_video_only": is_video_only})
            item.setCheckState(0, Qt.CheckState.Unchecked)
        self.resource_tree.expandAll()

    def display_html_resources(self, data):
        category_roots = {}
        for link in data.get("links", []):
            category_name = link.get("category", "其他");
            if category_name not in category_roots: category_roots[category_name] = QTreeWidgetItem(self.resource_tree, [category_name])
            filesize_mb = f"{link.get('size') / 1024 / 1024:.2f} MB" if isinstance(link.get('size'), int) else "未知"
            item_text = [link.get("filename", "N/A"), link.get("mime", link.get("ext")), "", filesize_mb, link.get("url")]
            item = QTreeWidgetItem(category_roots[category_name], item_text)
            item.setCheckState(0, Qt.CheckState.Unchecked); item.setData(0, Qt.ItemDataRole.UserRole, {"type": "direct", "url": link.get("url")})
        self.resource_tree.expandAll()

    def update_progress(self, value):
        self.progress_bar.setValue(value)
        self.statusBar().showMessage(f"下载进度: {value}%")

    def show_task_context_menu(self, position: QPoint):
        item = self.task_tree.itemAt(position);
        if not item: return
        menu = QMenu(); style = self.style()
        remove_action = menu.addAction(style.standardIcon(QStyle.StandardPixmap.SP_DialogCancelButton), "移除此任务")
        copy_url_action = menu.addAction(style.standardIcon(QStyle.StandardPixmap.SP_FileLinkIcon), "复制URL")
        action = menu.exec(self.task_tree.mapToGlobal(position))
        if action == remove_action: self.remove_task(item)
        elif action == copy_url_action: QApplication.clipboard().setText(item.text(0)); self.statusBar().showMessage("URL已复制到剪贴板", 2000)

    def remove_task(self, item):
        url_to_remove = item.text(0)
        self.task_tree.takeTopLevelItem(self.task_tree.indexOfTopLevelItem(item))
        if url_to_remove in self.current_task_data:
            del self.current_task_data[url_to_remove]
        self.resource_tree.clear()

    def set_controls_for_idle(self):
        self.stop_button.setVisible(False)
        self.sniff_button.setVisible(True); self.download_button.setVisible(True); self.merge_audio_checkbox.setVisible(True)
        for w in [self.url_input, self.browse_button, self.task_tree, self.resource_tree, self.merge_audio_checkbox, self.sniff_button, self.download_button]: w.setEnabled(True)
        self.statusBar().showMessage("准备就绪"); self.progress_bar.setVisible(False)
        self.stop_button.setText("停止操作")

    def set_controls_for_busy(self, message):
        self.sniff_button.setVisible(False); self.download_button.setVisible(False); self.merge_audio_checkbox.setVisible(False)
        self.stop_button.setVisible(True); self.stop_button.setEnabled(True)
        for w in [self.url_input, self.browse_button, self.task_tree, self.resource_tree, self.sniff_button, self.download_button]: w.setEnabled(False)
        self.statusBar().showMessage(message); self.progress_bar.setVisible(True); self.progress_bar.setValue(0)

    def browse_path(self):
        path = QFileDialog.getExistingDirectory(self, "选择下载文件夹", self.path_input.text() or QDir.homePath())
        if path: self.path_input.setText(path)

    def load_settings(self):
        default_path = QDir.home().filePath("Downloads")
        self.path_input.setText(self.settings.value("downloadPath", default_path))
        self.merge_audio_checkbox.setChecked(self.settings.value("autoMergeAudio", True, type=bool))

    def save_settings(self):
        self.settings.setValue("downloadPath", self.path_input.text())
        self.settings.setValue("autoMergeAudio", self.merge_audio_checkbox.isChecked())