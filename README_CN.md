# Pinterest 媒体下载器 (pinterest-dl)
[![PyPI 版本](https://img.shields.io/pypi/v/pinterest-dl)](https://pypi.org/project/pinterest-dl/)
[![Python 版本支持](https://img.shields.io/badge/python-%3E%3D3.10-blue
)](https://pypi.org/project/pinterest-dl/)
[![许可证](https://img.shields.io/pypi/l/pinterest-dl)](https://github.com/sean1832/pinterest-dl/blob/main/LICENSE)
[![下载量](https://static.pepy.tech/badge/pinterest-dl)](https://pepy.tech/project/pinterest-dl)

<a href="https://www.buymeacoffee.com/zekezhang" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/v2/default-blue.png" alt="Buy Me A Coffee" style="height: 40px !important;width: 145px !important;" ></a>

**[English](README.md) | 中文**


本工具库用于从 [Pinterest](https://pinterest.com) 抓取和下载媒体内容（包括图片和视频流）。通过浏览器自动化（默认使用 [Playwright](https://playwright.dev)，[Selenium](https://selenium.dev) 作为备用）和逆向工程的 Pinterest API 实现自动化，支持从指定 Pinterest URL 提取图片并保存到指定目录。

提供 [命令行工具](#-命令行使用) 直接使用，也支持 [Python API](#️-python-api) 编程调用。支持通过浏览器 cookies 获取私密画板和图钉中的媒体内容，并可将抓取的 URL 保存为 JSON 文件供后续使用。

> [!TIP]
> 如需图形界面版本，请查看 [pinterest-dl-gui](https://github.com/sean1832/pinterest-dl-gui)。
> 该工具基于同一核心库开发，提供了更友好的用户界面，也可作为将本库集成到 GUI 应用的参考示例。

> [!WARNING] 
> 本项目为独立开发，与 Pinterest 官方无关，仅用于学习目的。请注意自动化抓取可能违反 Pinterest [服务条款](https://developers.pinterest.com/terms/)。开发者不对工具滥用承担法律责任，请合理使用。

> [!NOTE]
> 本项目灵感来源于 [pinterest-image-scraper](https://github.com/xjdeng/pinterest-image-scraper)。

## 目录
- [Pinterest 媒体下载器 (pinterest-dl)](#pinterest-媒体下载器-pinterest-dl)
  - [目录](#目录)
  - [🌟 功能特性](#-功能特性)
  - [🚩 已知问题](#-已知问题)
  - [📋 环境要求](#-环境要求)
  - [📥 安装指南](#-安装指南)
    - [通过 pip 安装（推荐）](#通过-pip-安装推荐)
    - [从 GitHub 克隆](#从-github-克隆)
  - [🚀 快速开始](#-快速开始)
    - [命令行使用](#命令行使用)
    - [Python API](#python-api)
  - [📚 文档](#-文档)
  - [🤝 贡献指南](#-贡献指南)
  - [📜 许可证](#-许可证)

## 🌟 功能特性
- ✅ 直接从 Pinterest URL 抓取媒体
- ✅ 异步下载媒体文件（[#1](https://github.com/sean1832/pinterest-dl/pull/1)）
- ✅ 将抓取结果保存为 JSON 文件
- ✅ 无痕模式保护隐私
- ✅ 详细日志输出便于调试
- ✅ 支持 Firefox 浏览器
- ✅ 将媒体 `alt` 文本作为元数据嵌入下载文件
- ✅ 可选将 `alt` 文本另存为单独文件（[#32](https://github.com/sean1832/pinterest-dl/pull/32)）
- ✅ 通过浏览器 cookies 访问私密内容（[#20](https://github.com/sean1832/pinterest-dl/pull/20)）
- ✅ 使用逆向工程 API 抓取（默认方式，可通过 `--client chrome/firefox` 切换为浏览器模式）（[#21](https://github.com/sean1832/pinterest-dl/pull/21)）
- ✅ 通过关键词搜索媒体（[#23](https://github.com/sean1832/pinterest-dl/pull/23)）
- ✅ 单命令支持多 URL 和多查询
- ✅ 支持从文件批量处理 URL 和查询
- ✅ 下载视频流（如可用）
- ✅ **Playwright 支持** - 更快速、更可靠的浏览器自动化（默认），Selenium 作为备用（`--backend selenium`）

## 🚩 已知问题
- 🔲 一些嵌套 Pinterest 板块无法正确抓取

## 📋 环境要求
- Python 3.10 或更高版本
- （可选）Playwright 浏览器：`playwright install chromium` 或 `playwright install firefox`
- （可选）Selenium 后端：Chrome 或 Firefox 浏览器及对应 WebDriver
- （可选）[ffmpeg](https://ffmpeg.org/) 用于视频流下载（`--video` 选项）

## 📥 安装指南

### 通过 pip 安装（推荐）
```bash
pip install pinterest-dl
```

### 从 GitHub 克隆
```bash
git clone https://github.com/sean1832/pinterest-dl.git
cd pinterest-dl
pip install .
```


## 🚀 快速开始

### 命令行使用

使用命令行从 Pinterest 抓取图片：

```bash
# 从 Pinterest 画板或图钉抓取
pinterest-dl scrape <url> -o output_folder -n 50

# 搜索图片
pinterest-dl search "自然摄影" -o output_folder -n 30

# 登录以访问私密画板
pinterest-dl login -o cookies.json
```

**📖 [查看完整命令行文档 ->](doc/CLI_CN.md)**

可用命令：`login`、`scrape`、`search`、`download`

---

### Python API

在 Python 代码中使用 PinterestDL：

```python
from pinterest_dl import PinterestDL

# 快速抓取和下载
images = PinterestDL.with_api().scrape_and_download(
    url="https://www.pinterest.com/pin/1234567",
    output_dir="images/art",
    num=30
)

# 搜索图片
images = PinterestDL.with_api().search_and_download(
    query="风景艺术",
    output_dir="images/landscapes",
    num=50
)
```

**📖 [查看完整 API 文档 ->](doc/API_CN.md)**

包含：高级 API、私密画板访问、高级抓取模式

---

## 📚 文档

- **[命令行指南](doc/CLI_CN.md)** - 完整的命令行界面文档
- **[Python API 指南](doc/API_CN.md)** - 编程使用示例和模式
- **[贡献指南](CONTRIBUTING.md)** - 如何为项目做贡献

## 🤝 贡献指南
欢迎贡献代码！提交 PR 前请阅读[贡献指南](CONTRIBUTING.md)。

## 📜 许可证
[Apache License 2.0](LICENSE)
