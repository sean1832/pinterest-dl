# Pinterest 媒体下载器 (pinterest-dl)

[![PyPI 版本](https://img.shields.io/pypi/v/pinterest-dl)](https://pypi.org/project/pinterest-dl/)
[![Python 版本支持](https://img.shields.io/badge/python-%3E%3D3.10-blue)](https://pypi.org/project/pinterest-dl/)
[![许可证](https://img.shields.io/pypi/l/pinterest-dl)](https://github.com/sean1832/pinterest-dl/blob/main/LICENSE)
[![下载量](https://static.pepy.tech/badge/pinterest-dl)](https://pepy.tech/project/pinterest-dl)

**[English](README.md) | 中文**

从任意 Pinterest 画板、图钉或搜索词下载图片和视频的命令行工具。

![scrape demo](https://raw.githubusercontent.com/sean1832/pinterest-dl/main/doc/images/pinterest-dl-scrape.gif)

## 功能

- 从画板、图钉、版块或搜索词中抓取和下载图片及视频。
- 默认通过 Pinterest API 抓取，速度更快；也支持浏览器自动化（Playwright 或 Selenium）。
- 支持将视频下载为 MP4（需要 ffmpeg），或直接保存原始 .ts 流（无需 ffmpeg）。
- 通过浏览器 cookies 登录，可访问私密画板和图钉。
- 支持同时抓取多个 URL 或搜索词，也可从文件批量导入。
- 异步下载，可将抓取结果保存为 JSON 文件供后续重复下载。
- 可将 alt 文本嵌入 EXIF 注释，或保存为独立的 sidecar 文本文件。

## 安装

需要 Python 3.10 或更高版本。

```bash
pip install pinterest-dl
```

可选依赖提供图像和元数据功能：

| 命令 | 新增功能 |
| --- | --- |
| `pip install pinterest-dl[image]` | 图像分辨率检测和修剪（Pillow） |
| `pip install pinterest-dl[exif]` | 将 alt 文本嵌入 EXIF 元数据（pyexiv2） |
| `pip install pinterest-dl[metadata]` | 以上两者 |

部分功能还需要系统级工具：

- 浏览器后端：使用 `--client chromium/firefox` 之前，先运行 `playwright install chromium`（或 `firefox`）。
- 视频转 MP4：需要安装 [ffmpeg](https://ffmpeg.org/)。不安装时可用 `--skip-remux` 保留原始 .ts 文件。

完整说明见[可选依赖文档](https://github.com/sean1832/pinterest-dl/blob/main/doc/OPTIONAL_DEPENDENCIES_CN.md)。

<details>
<summary>源码安装</summary>

```bash
git clone https://github.com/sean1832/pinterest-dl.git
cd pinterest-dl
pip install .          # 或：pip install .[all]
```
</details>

## 快速开始

### 命令行

```bash
# 下载一个pin（pin URL 会返回该pin本身）
pinterest-dl scrape "<pin_url>" -o ./output

# 下载50个pin及相关pin（pin + 49 个相关pin）
pinterest-dl scrape "<pin_url>" -o ./output -n 50

# 搜索并下载30个pin
pinterest-dl search "自然摄影" -o ./output -n 30

# 下载视频为 MP4（需要 ffmpeg）
pinterest-dl scrape "<pin_url>" --video -o ./output

# 访问私密画板：先登录保存 cookies，再使用
pinterest-dl login -o cookies.json
pinterest-dl scrape "<private_board_url>" -c cookies.json -o ./output
```

完整命令和选项请参阅 [CLI 文档](https://github.com/sean1832/pinterest-dl/blob/main/doc/CLI_CN.md)。

### Python

```python
from pinterest_dl import PinterestDL

# 抓取画板并下载图片
images = PinterestDL.with_api().scrape_and_download(
    url="https://www.pinterest.com/username/board-name/",
    output_dir="images/art",
    num=30,
)

# 搜索并下载
images = PinterestDL.with_api().search_and_download(
    query="风景艺术",
    output_dir="images/landscapes",
    num=50,
)
```

完整用法请参阅 [API 文档](https://github.com/sean1832/pinterest-dl/blob/main/doc/API_CN.md)，或查看[可运行示例](https://github.com/sean1832/pinterest-dl/blob/main/examples/)。

## 文档

- [CLI 文档](https://github.com/sean1832/pinterest-dl/blob/main/doc/CLI_CN.md) - 所有命令和选项
- [Python API 文档](https://github.com/sean1832/pinterest-dl/blob/main/doc/API_CN.md) - 编程调用示例和模式
- [可选依赖说明](https://github.com/sean1832/pinterest-dl/blob/main/doc/OPTIONAL_DEPENDENCIES_CN.md) - 完整的可选包矩阵
- [测试指南](https://github.com/sean1832/pinterest-dl/blob/main/doc/TESTING_CN.md) - 离线测试套件与集成测试
- [贡献指南](https://github.com/sean1832/pinterest-dl/blob/main/CONTRIBUTING.md) - 如何参与贡献

## 免责声明

> [!WARNING]
> 本项目为独立开发，与 Pinterest 官方无关，仅用于学习目的。自动化抓取可能违反 Pinterest [服务条款](https://developers.pinterest.com/terms/)。开发者不对工具滥用承担任何责任，使用前请自行评估法律风险。

## 相关项目

- [pinterest-dl-gui](https://github.com/sean1832/pinterest-dl-gui) - 基于本库开发的图形界面版本。
- 灵感来源于 [pinterest-image-scraper](https://github.com/xjdeng/pinterest-image-scraper)。

## 贡献

欢迎贡献代码！请查阅 [CONTRIBUTING.md](https://github.com/sean1832/pinterest-dl/blob/main/CONTRIBUTING.md) 了解行为准则、提交规范和 PR 流程。

## 许可证

采用 Apache 2.0 许可证，详见 [LICENSE](https://github.com/sean1832/pinterest-dl/blob/main/LICENSE)。

## 支持作者

如果本工具节省了你的时间，欢迎[请我喝杯咖啡](https://www.buymeacoffee.com/zekezhang)。

<a href="https://www.buymeacoffee.com/zekezhang" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/v2/default-blue.png" alt="Buy Me A Coffee" style="height: 40px !important;width: 145px !important;" ></a>

---

[sean1832](https://github.com/sean1832) 开发。与 Pinterest 官方无关，所有商标归各自所有者所有。
