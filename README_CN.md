# Pinterest 图片下载器 (pinterest-dl)  
[English](README.md) | 中文  

[![PyPI - 版本](https://img.shields.io/pypi/v/pinterest-dl)](https://pypi.org/project/pinterest-dl/)  
[![PyPI - Python 版本](https://img.shields.io/pypi/pyversions/pinterest-dl)](https://pypi.org/project/pinterest-dl/)  
[![PyPI - 许可证](https://img.shields.io/pypi/l/pinterest-dl)](https://github.com/sean1832/pinterest-dl/blob/main/LICENSE)  
[![下载量](https://static.pepy.tech/badge/pinterest-dl)](https://pepy.tech/project/pinterest-dl)  

<a href="https://www.buymeacoffee.com/zekezhang" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/v2/default-blue.png" alt="请我喝杯咖啡" style="height: 40px !important;width: 145px !important;" ></a>  

本工具库专为从 [Pinterest](https://pinterest.com) 抓取和下载图片而设计。通过 [Selenium](https://selenium.dev) 和逆向工程的 Pinterest API 实现自动化，用户可以从指定的 Pinterest 链接提取图片并保存到指定目录。  

提供 [命令行工具](#-命令行使用) 直接使用，也支持 [Python API](#️-python-api) 编程调用。支持通过浏览器 cookies 抓取公开和私密画板、图钉的图片，并可将抓取的图片链接保存为 JSON 文件以便后续使用。  

> [!TIP]  
> 如需图形界面版本，请查看 [pinterest-dl-gui](https://github.com/sean1832/pinterest-dl-gui)。  
> 该版本基于相同底层库开发，提供了更友好的操作界面，也可作为集成本库到图形应用的参考案例。  

> [!WARNING]  
> 本项目为独立开发，与 Pinterest 官方无关，仅供学习研究。请注意自动化抓取行为可能违反其 [服务条款](https://developers.pinterest.com/terms/)。开发者不对工具滥用承担法律责任，请合理使用。  

> [!NOTE]  
> 本项目灵感来源于 [pinterest-image-scraper](https://github.com/xjdeng/pinterest-image-scraper)。  


## 目录
- [Pinterest 图片下载器 (pinterest-dl)](#pinterest-图片下载器-pinterest-dl)
  - [目录](#目录)
  - [🌟 功能亮点](#-功能亮点)
  - [🚩 已知问题](#-已知问题)
  - [📋 环境要求](#-环境要求)
  - [📥 安装指南](#-安装指南)
    - [通过 pip 安装（推荐）](#通过-pip-安装推荐)
    - [从 GitHub 克隆](#从-github-克隆)
  - [🚀 命令行使用](#-命令行使用)
    - [通用命令结构](#通用命令结构)
    - [命令详解](#命令详解)
      - [1. 登录](#1-登录)
      - [2. 抓取](#2-抓取)
      - [3. 搜索](#3-搜索)
      - [4. 下载](#4-下载)
  - [🛠️ Python API](#️-python-api)
    - [1. 快速抓取下载](#1-快速抓取下载)
    - [2. 使用 Cookies 抓取私密内容](#2-使用-cookies-抓取私密内容)
    - [3. 精细化控制](#3-精细化控制)
      - [3a. 使用 API](#3a-使用-api)
        - [抓取图片](#抓取图片)
        - [搜索图片](#搜索图片)
      - [3b. 使用浏览器](#3b-使用浏览器)
  - [🤝 参与贡献](#-参与贡献)
  - [📜 开源协议](#-开源协议)

## 🌟 功能亮点
- ✅ 直接从 Pinterest 链接抓图  
- ✅ 异步下载多张图片（[#1](https://github.com/sean1832/pinterest-dl/pull/1)）  
- ✅ 将图片链接保存为 JSON 文件  
- ✅ 无痕模式保护隐私  
- ✅ 详细日志输出便于调试  
- ✅ 支持 Firefox 浏览器  
- ✅ 将图片 `alt` 文本写入文件元数据（方便搜索）  
- ✅ 可选将 `alt` 文本另存为独立文件（[#32](https://github.com/sean1832/pinterest-dl/pull/32)）  
- ✅ 通过浏览器 cookies 抓取私密内容（[#20](https://github.com/sean1832/pinterest-dl/pull/20)）  
- ✅ 默认使用逆向工程 API（可通过 `--client chrome` 或 `--client firefox` 切换为浏览器模式）（[#21](https://github.com/sean1832/pinterest-dl/pull/21)）  
- ✅ 关键词搜索 Pinterest 图片（[#23](https://github.com/sean1832/pinterest-dl/pull/23)）  
- ✅ 单命令支持多链接/多关键词  
- ✅ 支持从文件批量读取链接和关键词  

## 🚩 已知问题
- 🔲 尚未实现完整测试  
- 🔲 在 ~~Linux 和~~ Mac 系统未充分测试，发现问题请提交 [Issue](https://github.com/sean1832/pinterest-dl/issues)  

## 📋 环境要求
- Python 3.10 或更高版本  
- （可选）Chrome 或 Firefox 浏览器  

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

## 🚀 命令行使用

### 通用命令结构
```bash
pinterest-dl [命令] [选项]
```

| 命令                  | 功能描述                                     |
| --------------------- | -------------------------------------------- |
| [`login`](#1-登录)    | 登录 Pinterest 获取 cookies 用于私密内容抓取 |
| [`scrape`](#2-抓取)   | 从 Pinterest 链接抓取图片                    |
| [`search`](#3-搜索)   | 通过关键词搜索 Pinterest 图片                |
| [`download`](#4-下载) | 从 JSON 文件中的链接下载图片                 |

---

### 命令详解

#### 1. 登录  
获取 Pinterest 登录 cookies 用于私密内容抓取。

```bash
pinterest-dl login [选项]
```

![login](doc/images/pinterest-dl-login.gif)

| 选项                        | 说明                  | 默认值         |
| --------------------------- | --------------------- | -------------- |
| `-o`, `--output [文件路径]` | 指定 cookies 保存路径 | `cookies.json` |
| `--client [chrome/firefox]` | 指定浏览器类型        | `chrome`       |
| `--headful`                 | 显示浏览器窗口        | -              |
| `--incognito`               | 启用无痕模式          | -              |
| `--verbose`                 | 显示详细日志          | -              |

> [!TIP]  
> 执行后会提示输入 Pinterest 账号密码，认证成功后将 cookies 保存至指定文件。

---

#### 2. 抓取  
从单个/多个图钉或画板链接抓取图片。

```bash
# 单链接或多链接模式：
pinterest-dl scrape <链接1> <链接2> …

# 从文件读取链接（每行一个链接）：
pinterest-dl scrape -f 链接文件.txt [选项]
pinterest-dl scrape -f 文件1.txt -f 文件2.txt [选项]

# 从stdin读取：
cat 链接文件.txt | pinterest-dl scrape -f - [选项]
```
![scrape](doc/images/pinterest-dl-scrape.gif)

| 选项                                 | 说明                                                                                                        | 默认值         |
| ------------------------------------ | ----------------------------------------------------------------------------------------------------------- | -------------- |
| `-f`, `--file [文件路径]`            | 指定链接来源文件，`-` 表示从stdin读取, 一行一个链接                                                         | -              |
| `<链接>`                             | 直接输入 Pinterest 链接                                                                                     | -              |
| `-o`, `--output [目录路径]`          | 图片保存目录（不指定则输出到终端）                                                                          | -              |
| `-c`, `--cookies [文件路径]`         | 指定 cookies 文件路径                                                                                       | `cookies.json` |
| `-n`, `--num [数量]`                 | 最大下载图片数                                                                                              | `100`          |
| `-r`, `--resolution [宽x高]`         | 最低分辨率（如 `512x512`）                                                                                  | -              |
| `--timeout [秒数]`                   | 请求超时时间                                                                                                | `3`            |
| `--delay [秒数]`                     | 请求间隔延迟                                                                                                | `0.2`          |
| `--cache [文件路径]`                 | 将抓取结果保存为 JSON 文件                                                                                  | -              |
| `--caption [txt/json/metadata/none]` | 标题保存格式：<br>`txt`-独立文本文件，<br>`json`-JSON文件，<br>`metadata`-写入图片元数据，<br>`none`-不保存 | `none`         |
| `--ensure-cap`                       | 确保每张图片都有 alt 文本                                                                                   | -              |
| `--client [api/chrome/firefox]`      | 选择抓取方式：<br>`api`-API模式（默认），<br>`chrome`/`firefox`-浏览器模式                                  | `api`          |
| `--headful`                          | 浏览器可见模式（仅浏览器模式有效）                                                                          | -              |
| `--incognito`                        | 浏览器无痕模式                                                                                              | -              |
| `--verbose`                          | 显示详细日志                                                                                                | -              |

---

#### 3. 搜索  
通过关键词搜索图片（仅限 API 模式），或从文件读取关键词批量搜索。

```bash
# 单关键词或多关键词：
pinterest-dl search <关键词1> <关键词2> ... [选项]

# 从文件读取关键词：
pinterest-dl search -f 关键词文件.txt [选项]
pinterest-dl search -f 文件1.txt -f 文件2.txt [选项]

# 从stdin读取：
cat 关键词文件.txt | pinterest-dl search -f - [选项]
```

![search](doc/images/pinterest-dl-search.gif)

| 选项                                 | 说明                                                   | 默认值         |
| ------------------------------------ | ------------------------------------------------------ | -------------- |
| `-f`, `--file [文件路径]`            | 指定关键词来源文件，`-` 表示从stdin读取， 一行一个链接 | -              |
| `<关键词>`                           | 直接输入搜索关键词                                     | -              |
| `-o`, `--output [目录路径]`          | 图片保存目录（不指定则输出到终端）                     | -              |
| `-c`, `--cookies [文件路径]`         | 指定 cookies 文件路径                                  | `cookies.json` |
| `-n`, `--num [数量]`                 | 最大下载图片数                                         | `100`          |
| `-r`, `--resolution [宽x高]`         | 最低分辨率                                             | -              |
| `--timeout [秒数]`                   | 请求超时时间                                           | `3`            |
| `--delay [秒数]`                     | 请求间隔延迟                                           | `0.2`          |
| `--cache [文件路径]`                 | 将搜索结果保存为 JSON 文件                             | -              |
| `--caption [txt/json/metadata/none]` | 标题保存格式                                           | `none`         |
| `--ensure-cap`                       | 确保每张图片都有 alt 文本                              | -              |
| `--verbose`                          | 显示详细日志                                           | -              |

---

#### 4. 下载  
从已保存的 JSON 文件下载图片。

```bash
pinterest-dl download <缓存文件.json> [选项]
```
![download](doc/images/pinterest-dl-download.gif)

| 选项                         | 说明             | 默认值           |
| ---------------------------- | ---------------- | ---------------- |
| `-o`, `--output [目录路径]`  | 指定图片保存目录 | `./<JSON文件名>` |
| `-r`, `--resolution [宽x高]` | 设置最低分辨率   | -                |
| `--verbose`                  | 显示详细日志     | -                |


## 🛠️ Python API
通过 `PinterestDL` 类可在 Python 程序中直接调用图片抓取功能。

### 1. 快速抓取下载
单步完成链接抓取和图片下载：

```python
from pinterest_dl import PinterestDL

# 初始化并执行抓取下载
images = PinterestDL.with_api(
    timeout=3,          # 单请求超时时间（秒）
    verbose=False,      # 关闭详细日志
    ensure_cap=True,    # 确保每张图片都有alt文本
).scrape_and_download(
    url="https://www.pinterest.com/pin/1234567",  # 目标链接
    output_dir="images/art",      # 保存目录
    num=30,                       # 最大下载数量
    min_resolution=(512, 512),    # 最低分辨率
    cache_path="art.json",        # 缓存文件路径
    caption="txt",                # 标题保存格式：txt/json/metadata/none
    delay=0.4,                    # 请求间隔延迟
)
```

关键词搜索并下载（仅限API模式）：

```python
from pinterest_dl import PinterestDL

images = PinterestDL.with_api().search_and_download(
    query="艺术",                 # 搜索关键词
    output_dir="images/art",      # 保存目录
    num=30,                       # 最大下载数量
    min_resolution=(512, 512),    # 最低分辨率
    cache_path="art.json",        # 缓存文件路径
    caption="txt",                # 标题保存格式
    delay=0.4,                    # 请求间隔延迟
)
```

### 2. 使用 Cookies 抓取私密内容
**2a. 获取 Cookies**
```python
import os
import json
from pinterest_dl import PinterestDL

# 避免在代码中明文存储密码
email = input("输入Pinterest邮箱：")
password = os.getenv("PINTEREST_PASSWORD")

# 通过浏览器登录获取cookies
cookies = PinterestDL.with_browser(
    browser_type="chrome",
    headless=True,
).login(email, password).get_cookies(
    after_sec=7  # 等待登录完成的缓冲时间
)

# 保存cookies到文件
with open("cookies.json", "w") as f:
    json.dump(cookies, f, indent=4)
```

**2b. 使用 Cookies 抓取**
```python
import json
from pinterest_dl import PinterestDL

# 加载cookies
with open("cookies.json", "r") as f:
    cookies = json.load(f)

# 执行抓取下载
images = (
    PinterestDL.with_api()
    .with_cookies(cookies)  # 注入cookies
    .scrape_and_download(
        url="https://www.pinterest.com/pin/1234567",  # 私密画板链接
        output_dir="images/art",
        num=30,
    )
)
```

### 3. 精细化控制
适用于需要分步控制的场景。

#### 3a. 使用 API

##### 抓取图片
```python
import json
from pinterest_dl import PinterestDL

# 1. 初始化并抓取
scraped_images = PinterestDL.with_api().scrape(
    url="https://www.pinterest.com/pin/1234567",
    num=30,
    min_resolution=(512, 512),  # 仅API模式支持直接设置分辨率过滤
)

# 2. 保存抓取结果
with open("art.json", "w") as f:
    json.dump([img.to_dict() for img in scraped_images], f, indent=4)

# 3. 下载图片
output_dir = "images/art"
downloaded_imgs = PinterestDL.download_images(scraped_images, output_dir)

# 4. 添加alt文本到元数据
PinterestDL.add_captions_to_meta(downloaded_imgs, range(len(downloaded_imgs)))

# 5. 另存alt文本为独立文件
PinterestDL.add_captions_to_file(downloaded_imgs, output_dir, extension="txt")
```

##### 搜索图片
```python
from pinterest_dl import PinterestDL

# 1. 搜索图片
scraped_images = PinterestDL.with_api().search(
    query="艺术",
    num=30,
    min_resolution=(512, 512),
    delay=0.4,
)
# 后续步骤与抓取相同...
```

#### 3b. 使用浏览器
```python
import json
from pinterest_dl import PinterestDL

# 1. 浏览器模式抓取
scraped_images = PinterestDL.with_browser(
    browser_type="chrome",
    headless=True,
    ensure_cap=True,
).scrape(
    url="https://www.pinterest.com/pin/1234567",
    num=30,
)

# 2. 保存结果
with open("art.json", "w") as f:
    json.dump([img.to_dict() for img in scraped_images], f, indent=4)

# 3. 下载图片
output_dir = "images/art"
downloaded_imgs = PinterestDL.download_images(scraped_images, output_dir)

# 4. 分辨率过滤（浏览器模式需后置处理）
valid_indices = PinterestDL.prune_images(downloaded_imgs, (200, 200))

# 5. 添加元数据和文本标题
PinterestDL.add_captions_to_meta(downloaded_imgs, valid_indices)
PinterestDL.add_captions_to_file(downloaded_imgs, output_dir, "txt")
```

## 🤝 参与贡献
欢迎提交 Pull Request！请先阅读 [贡献指南](CONTRIBUTING.md)。

## 📜 开源协议
[Apache License 2.0](LICENSE)