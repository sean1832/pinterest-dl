# Pinterest 图片下载器 (pinterest-dl)
[English](README.md) | 中文

[![PyPI - 版本](https://img.shields.io/pypi/v/pinterest-dl)](https://pypi.org/project/pinterest-dl/)
[![PyPI - Python 版本](https://img.shields.io/pypi/pyversions/pinterest-dl)](https://pypi.org/project/pinterest-dl/)
[![PyPI - 许可证](https://img.shields.io/pypi/l/pinterest-dl)](https://github.com/sean1832/pinterest-dl/blob/main/LICENSE)
[![下载量](https://static.pepy.tech/badge/pinterest-dl)](https://pepy.tech/project/pinterest-dl)

<a href="https://www.buymeacoffee.com/zekezhang" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/v2/default-blue.png" alt="Buy Me A Coffee" style="height: 40px !important;width: 145px !important;" ></a>

本库提供从 [Pinterest](https://pinterest.com) 抓取和下载图片的功能。通过 [Selenium](https://selenium.dev) 和逆向工程 Pinterest API 实现自动化，用户可从指定 Pinterest URL 提取图片并保存至目标目录。

包含 [CLI 命令行工具](#-cli-usage) 和 [Python API](#️-python-api) 两种使用方式。支持通过浏览器 cookies 获取公开/私密画板和图钉 (pin) 中的图片，并可将抓取的 URL 保存为 JSON 文件供后续使用。

> [!TIP]
> 如需图形界面版本，请查看 [pinterest-dl-gui](https://github.com/sean1832/pinterest-dl-gui)。
> 该工具基于相同核心库开发，提供了更友好的交互界面，也可作为 GUI 应用集成参考案例。

> [!WARNING] 
> 本项目为独立开发，与 Pinterest 官方无关。仅供学习用途，自动化抓取可能违反 Pinterest [服务条款](https://developers.pinterest.com/terms/)。开发者不对工具滥用承担法律责任，请谨慎使用。

> [!NOTE]
> 灵感来源于 [pinterest-image-scraper](https://github.com/xjdeng/pinterest-image-scraper)。

# 目录
- [Pinterest 图片下载器 (pinterest-dl)](#pinterest-图片下载器-pinterest-dl)
- [目录](#目录)
  - [功能亮点](#功能亮点)
  - [已知问题](#已知问题)
  - [环境要求](#环境要求)
  - [安装指南](#安装指南)
    - [pip 安装（推荐）](#pip-安装推荐)
    - [GitHub 源码安装](#github-源码安装)
  - [命令行使用](#命令行使用)
    - [通用命令结构](#通用命令结构)
    - [使用示例](#使用示例)
    - [命令详解](#命令详解)
      - [1. 登录](#1-登录)
      - [2. 抓取](#2-抓取)
      - [3. 搜索](#3-搜索)
      - [4. 下载](#4-下载)
  - [Python API](#python-api)
    - [1. 快速抓取下载](#1-快速抓取下载)
    - [2. 使用 Cookies 抓取私密内容](#2-使用-cookies-抓取私密内容)
    - [3. 精细化控制](#3-精细化控制)
      - [3a. API 模式](#3a-api-模式)
        - [图片抓取](#图片抓取)
        - [图片搜索](#图片搜索)
      - [3b. 浏览器模式](#3b-浏览器模式)
  - [贡献指南](#贡献指南)
  - [开源协议](#开源协议)

## 功能亮点
- ✅ 直接从 Pinterest URL 抓取图片
- ✅ 异步下载图片列表 ([#1](https://github.com/sean1832/pinterest-dl/pull/1))
- ✅ 将抓取结果保存为 JSON 文件
- ✅ 无痕模式保护隐私
- ✅ 详细日志输出便于调试
- ✅ 支持 Firefox 浏览器
- ✅ 将图片 `alt` 文本作为元数据嵌入下载文件
- ✅ 可选将 `alt` 文本另存为独立文件 (`txt`, `json`) ([#32](https://github.com/sean1832/pinterest-dl/pull/32))
- ✅ 通过浏览器 cookies 抓取私密画板内容 ([#20](https://github.com/sean1832/pinterest-dl/pull/20))
- ✅ 默认使用逆向工程 Pinterest API（可通过 `--client chrome` 或 `--client firefox` 切换为浏览器模式）([#21](https://github.com/sean1832/pinterest-dl/pull/21))
- ✅ 关键词搜索 Pinterest 图片并下载 ([#23](https://github.com/sean1832/pinterest-dl/pull/23))

## 已知问题
- 🔲 尚未实现完整测试
- 🔲 Linux/Mac 系统兼容性待验证，发现问题请提交 [Issue](https://github.com/sean1832/pinterest-dl/issues)

## 环境要求
- Python 3.10 或更高版本
- Chrome 或 Firefox 浏览器

## 安装指南

### pip 安装（推荐）
```bash
pip install pinterest-dl
```

### GitHub 源码安装
```bash
git clone https://github.com/sean1832/pinterest-dl.git
cd pinterest-dl
pip install .
```

## 命令行使用

### 通用命令结构
```bash
pinterest-dl [命令] [选项]
```

| 命令                      | 功能说明                                     |
| ------------------------- | -------------------------------------------- |
| [`login`](#1-login)       | 登录 Pinterest 获取 cookies 用于私密内容抓取 |
| [`scrape`](#2-scrape)     | 从 Pinterest URL 抓取图片                    |
| [`search`](#3-search)     | 通过关键词搜索 Pinterest 图片                |
| [`download`](#4-download) | 从 JSON 文件中的 URL 列表下载图片            |

---
### 使用示例

**匿名模式抓取图片：**

从 `https://www.pinterest.com/pin/1234567` 抓取 30 张分辨率不低于 512x512 的图片到 `./images/art` 目录，并保存 URL 到 `art.json`：
```bash
pinterest-dl scrape "https://www.pinterest.com/pin/1234567" -o "images/art" -n 30 -r 512x512 --cache art.json
```

**获取浏览器 Cookies：**

在可见浏览器窗口中登录 Pinterest 并保存 cookies 到 `cookies.json`：
```bash
pinterest-dl login -o cookies.json --headful
```
> [!TIP]
> 按提示输入 Pinterest 邮箱和密码，工具会将 cookies 保存至指定文件供后续使用。

**抓取私密画板：**

使用 `cookies.json` 中的认证信息抓取私密画板内容：
```bash
pinterest-dl scrape "https://www.pinterest.com/pin/1234567" -o "images/art" -n 30 -c cookies.json
```

> [!TIP]
> 可通过 `--client` 选项选择 `chrome` 或 `firefox` 浏览器驱动，速度较慢但更可靠。
> 默认使用无头模式，添加 `--headful` 参数可显示浏览器窗口。

**从缓存文件下载：**

将 `art.json` 中的图片下载到 `./downloaded_imgs` 目录，分辨率不低于 1024x1024：
```bash
pinterest-dl download art.json -o downloaded_imgs -r 1024x1024
```
---
### 命令详解

#### 1. 登录
获取 Pinterest 登录 cookies 用于私密内容抓取。

**语法：**
```bash
pinterest-dl login [选项]
```

![login](https://github.com/sean1832/pinterest-dl/blob/main/doc/images/pinterest-dl-login.gif)

**选项：**
- `-o`, `--output [文件]`: cookies 保存路径（默认：`cookies.json`）
- `--client`: 选择浏览器类型 (`chrome` / `firefox`)（默认：`chrome`）
- `--headful`: 显示浏览器窗口
- `--verbose`: 输出详细日志
- `--incognito`: 启用无痕模式

> [!TIP]
> 执行后会提示输入 Pinterest 邮箱和密码，认证信息将保存至指定文件（未指定时默认保存到 `./cookies.json`）

#### 2. 抓取
从指定 Pinterest URL 提取图片。

**语法：**
```bash
pinterest-dl scrape [URL] [选项]
```

![scrape](https://github.com/sean1832/pinterest-dl/blob/main/doc/images/pinterest-dl-scrape.gif)

**选项：**

- `-o`, `--output [目录]`: 图片保存目录（未指定时输出到控制台）
- `-c`, `--cookies [文件]`: 包含 cookies 的认证文件（需先执行 `login` 命令获取）
- `-n`, `--num [数量]`: 最大下载数量（默认：100）
- `-r`, `--resolution [宽]x[高]`: 图片最低分辨率（如 512x512）
- `--timeout [秒]`: 请求超时时间（默认：3）
- `--delay [秒]`: 请求间隔延迟（默认：0.2）
- `--cache [路径]`: 将抓取结果保存为 JSON 文件
- `--caption [格式]`: 图片描述保存格式：`txt` 为独立文本文件，`json` 为完整元数据文件，`metadata` 嵌入图片文件，`none` 不保存（默认：`none`）
- `--verbose`: 输出详细日志
- `--client`: 选择抓取方式 (`api` / `chrome` / `firefox`)（默认：api）
- `--incognito`: 启用无痕模式（仅浏览器模式有效）
- `--headful`: 显示浏览器窗口（仅浏览器模式有效）

#### 3. 搜索
通过关键词搜索 Pinterest 图片（目前仅限 API 模式）。

**语法：**
```bash
pinterest-dl search [关键词] [选项]
```

![search](https://github.com/sean1832/pinterest-dl/blob/main/doc/images/pinterest-dl-search.gif)

**选项：**
- `-o`, `--output [目录]`: 图片保存目录（未指定时输出到控制台）
- `-c`, `--cookies [文件]`: 包含 cookies 的认证文件（需先执行 `login` 命令获取）
- `-n`, `--num [数量]`: 最大下载数量（默认：100）
- `-r`, `--resolution [宽]x[高]`: 图片最低分辨率（如 512x512）
- `--timeout [秒]`: 请求超时时间（默认：3）
- `--delay [秒]`: 请求间隔延迟（默认：0.2）
- `--cache [路径]`: 将抓取结果保存为 JSON 文件
- `--caption [格式]`: 图片描述保存格式（同 scrape 命令）
- `--verbose`: 输出详细日志

#### 4. 下载
从缓存文件（JSON）下载图片。

**语法：**
```bash
pinterest-dl download [缓存文件] [选项]
```

![download](https://github.com/sean1832/pinterest-dl/blob/main/doc/images/pinterest-dl-download.gif)

**选项：**
- `-o`, `--output [目录]`: 输出目录（默认：./<json文件名>）
- `-r`, `--resolution [宽]x[高]`: 图片最低分辨率（如 512x512）
- `--verbose`: 输出详细日志


## Python API
可通过 `PinterestDL` 类在 Python 代码中直接调用图片抓取功能。

### 1. 快速抓取下载
单步完成 Pinterest URL 的图片抓取和下载。

```python
from pinterest_dl import PinterestDL

# 初始化并执行图片下载
images = PinterestDL.with_api(
    timeout=3,  # 单次请求超时（秒）（默认：3）
    verbose=False,  # 启用详细日志（默认：False）
).scrape_and_download(
    url="https://www.pinterest.com/pin/1234567",  # Pinterest pin 链接
    output_dir="images/art",  # 保存目录
    num=30,  # 最大下载数量
    min_resolution=(512, 512),  # 最低分辨率（宽, 高）（默认：None）
    cache_path="art.json",  # 缓存文件路径（默认：None）
    caption="txt",  # 描述保存格式：'txt'/'json'/'metadata'/'none'
    delay=0.8,  # 请求间隔延迟（秒）（默认：0.2）
)
```

关键词搜索并下载图片（仅限 API 模式）：

```python
from pinterest_dl import PinterestDL

images = PinterestDL.with_api( 
    timeout=3,
    verbose=False,
).search_and_download(
    query="art",  # 搜索关键词
    output_dir="images/art",
    num=30,
    min_resolution=(512, 512),
    cache_path="art.json",
    caption="txt",
    delay=0.8,
)
```

### 2. 使用 Cookies 抓取私密内容
**2a. 获取 cookies**
首先需要登录 Pinterest 获取认证 cookies。
```python
import os
import json
from pinterest_dl import PinterestDL

# 避免在代码中直接暴露密码
email = input("输入 Pinterest 邮箱：")
password = os.getenv("PINTEREST_PASSWORD")

# 通过浏览器登录获取 cookies
cookies = PinterestDL.with_browser(
    browser_type="chrome",
    headless=True,
).login(email, password).get_cookies(
    after_sec=7,  # 等待登录完成的缓冲时间（秒）
)

# 保存 cookies 到文件
with open("cookies.json", "w") as f:
    json.dump(cookies, f, indent=4)
```

**2b. 使用 cookies 抓取**
获取 cookies 后可用于私密内容抓取。
```python
import json
from pinterest_dl import PinterestDL

# 加载 cookies
with open("cookies.json", "r") as f:
    cookies = json.load(f)

# 使用 cookies 抓取私密内容
images = (
    PinterestDL.with_api()
    .with_cookies(cookies)  # 加载 selenium 格式的 cookies
    .scrape_and_download(
        url="https://www.pinterest.com/pin/1234567",  # 假设这是私密画板链接
        output_dir="images/art",
        num=30,
    )
)
```

### 3. 精细化控制
需要更精细控制时，可分离抓取和下载步骤。

#### 3a. API 模式

##### 图片抓取
```python
import json
from pinterest_dl import PinterestDL

# 1. 初始化 API 模式抓取
scraped_images = PinterestDL.with_api().scrape(
    url="https://www.pinterest.com/pin/1234567",
    num=30,
    min_resolution=(512, 512),  # ← 此参数仅 API 模式有效
)

# 2. 保存抓取结果
images_data = [img.to_dict() for img in scraped_images]
with open("art.json", "w") as f:
    json.dump(images_data, f, indent=4)

# 3. 下载图片
output_dir = "images/art"
downloaded_imgs = PinterestDL.download_images(scraped_images, output_dir)

# 4. 添加元数据（可选）
valid_indices = list(range(len(downloaded_imgs)))  # 所有图片均有效
PinterestDL.add_captions_to_meta(downloaded_imgs, valid_indices)

# 5. 保存独立描述文件（可选）
PinterestDL.add_captions_to_file(downloaded_imgs, output_dir, extension="txt")
```

##### 图片搜索
```python
import json
from pinterest_dl import PinterestDL

# 1. 关键词搜索
scraped_images = PinterestDL.with_api().search(
    query="art",  # 搜索关键词
    num=30,
    min_resolution=(512, 512),
    delay=0.4, # 请求间隔（默认：0.2）
)
# ...（后续步骤同上）
```

#### 3b. 浏览器模式
```python
import json
from pinterest_dl import PinterestDL

# 1. 初始化浏览器模式
scraped_images = PinterestDL.with_browser(
    browser_type="chrome",  # 浏览器类型（'chrome' 或 'firefox'）
    headless=True,  # 无头模式
).scrape(
    url="https://www.pinterest.com/pin/1234567",
    num=30,
)

# 2. 保存结果
images_data = [img.to_dict() for img in scraped_images]
with open("art.json", "w") as f:
    json.dump(images_data, f, indent=4)

# 3. 下载图片
output_dir = "images/art"
downloaded_imgs = PinterestDL.download_images(scraped_images, output_dir)

# 4. 按分辨率筛选（可选）
valid_indices = PinterestDL.prune_images(downloaded_imgs, min_resolution=(200, 200))

# 5. 添加元数据（可选）
PinterestDL.add_captions_to_meta(downloaded_imgs, valid_indices)

# 6. 保存独立描述文件（可选）
PinterestDL.add_captions_to_file(downloaded_imgs, output_dir, extension="txt")
```

## 贡献指南
欢迎提交贡献！请阅读[贡献指南](CONTRIBUTING.md)后再提交 Pull Request。

## 开源协议
[Apache License 2.0](LICENSE)