

██████╗ ███████╗███████╗███╗   ██╗██╗███████╗███████╗███████╗██████╗
██╔══██╗██╔════╝██╔════╝████╗  ██║██║██╔════╝██╔════╝██╔════╝██╔══██╗
██████╔╝█████╗  ███████╗██╔██╗ ██║██║█████╗  █████╗  ███████╗██████╔╝
██╔══██╗██╔══╝  ╚════██║██║╚██╗██║██║██╔══╝  ██╔══╝  ╚════██║██╔══██╗
██║  ██║███████╗███████║██║ ╚████║██║███████╗███████╗███████║██║  ██║
╚═╝  ╚═╝╚══════╝╚══════╝╚═╝  ╚═══╝╚═╝╚══════╝╚══════╝╚══════╝╚═╝  ╚═╝

  <p><strong>一个拥有“决策大脑”的次世代智能资源嗅探器</strong></p>
  
  <p>
    <a href="https://github.com/424635328/ReSniffer/releases/latest">
      <img src="https://img.shields.io/github/v/release/424635328/ReSniffer?style=for-the-badge&logo=github&color=8e44ad" alt="Latest Release">
    </a>
    <a href="https://github.com/424635328/ReSniffer/stargazers">
      <img src="https://img.shields.io/github/stars/424635328/ReSniffer?style=for-the-badge&logo=github&color=f1c40f" alt="Stargazers">
    </a>
    <a href="https://github.com/424635328/ReSniffer/blob/main/LICENSE">
      <img src="https://img.shields.io/github/license/424635328/ReSniffer?style=for-the-badge&color=2ecc71" alt="License">
    </a>
  </p>
  
  <p>
    <img src="https://img.shields.io/badge/Python-3.9+-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python Version">
    <img src="https://img.shields.io/badge/PyQt-6-2b7e2b?style=flat-square&logo=qt&logoColor=white" alt="PyQt6">
    <img src="https://img.shields.io/badge/Engine-yt--dlp-FF0000?style=flat-square" alt="yt-dlp">
    <img src="https://img.shields.io/badge/Engine-Selenium-43B02A?style=flat-square&logo=selenium" alt="Selenium">
  </p>
</div>

**ReSniffer** 重新定义了网页资源获取。它不仅是一个工具，更是一位数字世界的考古学家。它能穿透层层迷雾，从最简单直接的链接到由JavaScript动态构建的复杂Web应用，智能地勘探并挖掘出深埋其中的宝贵数字资源。

无论是主流媒体的加密视频流，还是开发者发布的最新软件版本，ReSniffer都将通过其独特的、基于多层决策的嗅探模型，将它们清晰地呈现在你面前。

---

## 目录

* [✨ **核心特性**](#-核心特性)
* [🧠 **技术架构：CSI智能嗅探模型**](#-技术架构csi智能嗅探模型)
* [📂 **项目结构**](#-项目结构)
* [🚀 **快速开始**](#-快速开始)
* [📦 **打包为独立应用**](#-打包为独立应用)
* [💡 **使用技巧与FAQ**](#-使用技巧与faq)
* [🤝 **贡献指南**](#-贡献指南)
* [📄 **许可证**](#-许可证)

---

## ✨ 核心特性

* **🤖 智能多策略嗅探**:
  * **贝叶斯决策核心**: 独创的策略分析器，能根据URL特征（域名、路径、参数）为每个嗅探引擎动态评分，并按最优顺序执行，实现真正的“因地制宜”。
  * **专用API优先**: 自动识别GitHub Release等特定站点，直接调用其官方API，实现最快、最精准的资源获取。
  * **媒体流深度解析**: 集成强大的 `yt-dlp` 引擎，穿透主流视频网站的防护，解析音视频流。
  * **无头浏览器穿透 (终极武器)**: 当所有常规方法失效时，自动启动**隐身浏览器引擎** (`undetected-chromedriver`)，完美渲染JS动态页面，实现“所见即所得”的终极嗅探。
  * **经验学习系统**: 自动记录对特定域名最有效的嗅探策略，并在后续任务中给予“经验加分”，越用越聪明。

* **🎨 精致的GUI体验**:
  * **“忧郁霓虹”设计风格**: 深度定制的QSS样式表，融合了深邃的暗色背景与高亮的霓虹功能色，提供沉浸式视觉体验。
  * **动态粒子背景**: 流动的粒子效果为应用注入了生命力与科技感。
  * **流畅的微动画**: 所有核心交互按钮均带有平滑的颜色过渡动画，操作体验如丝般顺滑。
  * **永不卡顿**: 所有耗时操作均在后台线程执行，主界面始终保持响应，并提供可随时中断的“停止”功能。

* **强大的下载管理**:
  * **一键智能合并**: 只需勾选视频流，“自动合并最佳音轨”功能将利用`ffmpeg`为您产出有声有色的完整视频文件。
  * **下载队列与进度**: 支持批量添加下载任务，程序将按顺序执行，并为每个任务提供实时进度反馈。
    .   **上下文菜单**: 右键点击任务可快速进行移除、复制URL等操作。

---

## 🧠 技术架构：CSI智能嗅探模型

ReSniffer的设计哲学是“专业的事交给专业的工具”。其核心是一个名为 **CSI (Crawl, Sniff, Investigate)** 的智能嗅探模型，它将复杂的决策过程解耦为四个独立的模块：

![架构图](https://github.com/424635328/ReSniffer/blob/main/docs/architecture.png)

1. **`app_window.py`**: **UI层 (The Bridge)**。负责所有与用户界面的交互、布局和视觉呈现。它完全使用PyQt代码构建，并应用QSS样式。它不知道任何嗅探或下载的具体逻辑。
2. **`worker.py`**: **调度层 (The Dispatcher)**。作为UI和后端的桥梁。它接收来自UI的简单任务请求（如“嗅探这个URL”），然后调用策略分析器决定如何执行，并管理后台线程和子进程的生命周期。
3. **`strategy_profiler.py`**: **决策大脑 (The Profiler)**。包含所有策略的评分逻辑。它接收一个URL，输出一个按优先级排序的策略列表，供Worker执行。
4. **`backend_scraper.py`**: **工具箱 (The Toolbox)**。包含所有实际执行嗅探和下载的“工具函数”（如`sniff_engine_yt_dlp`）。每个函数都像一把独立的锤子或螺丝刀，等待被调度层调用。

---

## 📂 项目结构

```md
ReSniffer/
└── Gui/
    ├── main.py                 # 🚀 程序主入口, 应用QSS样式
    ├── app_window.py           # 🎨 GUI主窗口的布局与交互逻辑
    ├── worker.py                 # 👷‍♂️ 后台工作线程，调度和执行任务
    ├── strategy_profiler.py      # 🧠 智能策略选择引擎 (决策大脑)
    ├── backend_scraper.py        # 🛠️ 所有嗅探和下载的后端函数模块
    │
    ├── RSniffer.spec             # 📦 PyInstaller打包配置文件
    │
    ├── yt-dlp.exe                # 依赖：媒体嗅探核心
    ├── ffmpeg.exe                # 依赖：音视频合并工具
    ├── ffprobe.exe               # 依赖：音视频分析工具
    │
    ├── sniffer_gui.log           # 运行时生成的日志文件
    └── downloads/                # (自动创建) 下载文件存放目录
```

---

## 🚀 快速开始

### 依赖环境

* **Python**: 3.9 或更高版本
* **Google Chrome**: 需要安装最新版的Chrome浏览器。
* **Git**: 用于克隆仓库。

### 从源码运行

1. **克隆仓库**:

    ```bash
    git clone https://github.com/424635328/ReSniffer.git
    cd ReSniffer/Gui 
    ```

2. **创建并激活虚拟环境** (强烈推荐):

    ```bash
    python -m venv venv
    # Windows:
    .\venv\Scripts\activate
    # macOS / Linux:
    source venv/bin/activate
    ```

3. **安装Python依赖**:
    项目根目录下已提供 `requirements.txt` 文件，可直接安装。

    ```bash
    pip install -r requirements.txt
    ```

4. **准备外部依赖**:
    * 从 [yt-dlp Releases](https://github.com/yt-dlp/yt-dlp/releases/latest) 下载 `yt-dlp.exe`。
    * 从 [ffmpeg Builds](https://www.gyan.dev/ffmpeg/builds/) 下载 `ffmpeg-release-essentials.zip`，解压出 `ffmpeg.exe` 和 `ffprobe.exe`。
    * 将这**三个 `.exe` 文件**都放在 `Gui` 目录下，与 `main.py` 并列。

5. **运行程序**:

    ```bash
    python main.py
    ```

---

## 📦 打包为独立应用

我们使用 `PyInstaller` 和一个 `.spec` 文件来进行精确打包，以确保所有依赖（包括`.exe`文件）都被正确捆绑。

1. **准备**: 确保所有外部依赖 `.exe` 文件都在 `Gui` 目录下。准备一个 `.ico` 图标文件。
2. **编辑 `.spec` 文件**: 项目中已包含一个 `RSniffer.spec` 文件。您可以根据需要修改其中的 `name`, `icon` 和 `added_files` 路径。
3. **执行打包**: 在 `Gui` 目录下打开终端，运行：

    ```bash
    pyinstaller RSniffer.spec
    ```

    最终的可执行文件将位于 `Gui/dist/` 目录中。

---

## 💡 使用技巧与FAQ

* **GitHub速率限制**: 为了避免GitHub API的速率限制（匿名用户每小时60次请求），强烈建议生成一个[个人访问令牌](https://github.com/settings/tokens)（无需勾选任何权限），并将其设置为名为 `GITHUB_TOKEN` 的系统环境变量。
* **为何某个网站嗅探失败?**:
    1. **检查日志**: 日志窗口会显示每个策略引擎的尝试过程和失败原因。
    2. **网站复杂度**: 如果所有引擎都失败了，说明该网站可能使用了非常高级或私有的反爬取技术，超出了当前所有策略的范围。
    3. **提交Issue**: 欢迎将这类高难度网站提交到[Issues](https://github.com/424635328/ReSniffer/issues)，我们可以一起研究，并可能在未来版本中加入新的策略来支持它。
* **打包后的程序无法运行?**:
  * 最常见的原因是 `yt-dlp.exe` 或 `ffmpeg.exe` 未被正确捆绑。请确保 `.spec` 文件中的 `--add-data` 或 `datas` 字段正确无误。
  * 在Windows上，某些杀毒软件可能会误报，这是打包程序的常见情况，请尝试添加信任。

---

## 🤝 贡献指南

我们欢迎并感谢所有形式的贡献！无论是报告bug、提出新功能建议，还是直接贡献代码。

### 如何贡献

1. **Fork** 本仓库。
2. **创建** 您的特性分支 (`git checkout -b feature/YourAmazingFeature`)。
3. **提交** 您的更改 (`git commit -m 'feat: Add some AmazingFeature'`)。我们推荐使用 [Conventional Commits](https://www.conventionalcommits.org/) 规范。
4. **推送** 到分支 (`git push origin feature/YourAmazingFeature`)。
5. 开启一个 **Pull Request**，并详细描述您的更改。

### 扩展嗅探能力

要为一个新网站（例如 `new-site.com`）增加支持，您只需要：

1. 在 `backend_scraper.py` 中创建一个新的嗅探函数 `sniff_engine_new_site(url)`。
2. 在 `strategy_profiler.py` 中：
    * 将新策略添加到 `STRATEGY_METADATA`。
    * 编写一个新的分析器 `analyze_for_new_site(features)`，当 `features['netloc']` 是 `new-site.com` 时返回高分。
    * 将新分析器添加到 `STRATEGY_ANALYZERS` 字典中。

就是这么简单！您无需改动 `worker` 或 `app_window` 的任何核心逻辑。

---

## 📄 许可证

本项目采用 [Boost](https://github.com/424635328/ReSniffer/blob/main/LICENSE) 许可证。

<div align="center">
  <p>探索数字世界的深度，释放信息的自由。</p>
  <p>Made with ❤️ and a touch of melancholy neon.</p>
</div>