# Python API 使用指南

本文档详细介绍如何在 Python 代码中使用 PinterestDL 库。

## 目录
- [概述](#概述)
- [1. 高级整合方法](#1-高级整合方法)
  - [抓取并下载](#抓取并下载)
  - [搜索并下载](#搜索并下载)
  - [1a. 使用 Cookies 抓取私密内容](#1a-使用-cookies-抓取私密内容)
- [2. 底层控制方法](#2-底层控制方法)
  - [2a. 使用 API 模式](#2a-使用-api-模式)
  - [2b. 使用浏览器模式 (Playwright)](#2b-使用浏览器模式-playwright)
  - [2c. 使用浏览器模式 (Selenium - 遗留)](#2c-使用浏览器模式-selenium---遗留)

---

## 概述

`PinterestDL` 类提供三种初始化方式：

- **`PinterestDL.with_api()`** - 使用逆向工程的 Pinterest API（推荐，速度快）
- **`PinterestDL.with_browser()`** - 使用 Playwright 浏览器自动化（默认，更可靠但较慢）
- **`PinterestDL.with_selenium()`** - 使用 Selenium 浏览器自动化（遗留支持，将在1.1.0弃用）

> **注意：** 浏览器自动化现在默认使用 **Playwright**，更快速、更可靠。Selenium 仍可通过 `PinterestDL.with_selenium()` 作为备用。

---

## 1. 高级整合方法

这些方法将抓取和下载合并为一步操作，适合大多数使用场景。

### 抓取并下载

从 Pinterest URL 一步完成抓取和下载。

```python
from pinterest_dl import PinterestDL

# 初始化并运行 Pinterest 图片下载器
images = PinterestDL.with_api(
    timeout=3,        # 每个请求的超时时间（秒）（默认：3）
    verbose=False,    # 启用详细日志用于调试（默认：False）
    ensure_alt=True,  # 确保每张图片都有 alt 文本（默认：False）
).scrape_and_download(
    url="https://www.pinterest.com/pin/1234567",  # 要抓取的 Pinterest URL
    output_dir="images/art",                       # 保存下载图片的目录
    num=30,                                        # 最大下载数量
    download_streams=True,                         # 下载视频流（如可用）（默认：False）
    min_resolution=(512, 512),                     # 最低分辨率（宽，高）（默认：None）
    cache_path="art.json",                         # 缓存抓取数据为 JSON 的路径（默认：None）
    caption="txt",                                 # 标题格式：'txt' 为独立文件中的 alt 文本，
                                                   # 'json' 为独立文件中的完整图片数据，
                                                   # 'metadata' 嵌入图片文件，'none' 无标题
    delay=0.4,                                     # 请求之间的延迟（默认：0.2）
)
```

### 搜索并下载

通过关键词搜索并下载图片。

```python
from pinterest_dl import PinterestDL

# 初始化并运行 Pinterest 图片下载器
# `search_and_download` 仅在 API 模式下可用
images = PinterestDL.with_api( 
    timeout=3,        # 每个请求的超时时间（秒）（默认：3）
    verbose=False,    # 启用详细日志用于调试（默认：False）
    ensure_alt=True,  # 确保每张图片都有 alt 文本（默认：False）
).search_and_download(
    query="艺术",                       # Pinterest 搜索关键词
    output_dir="images/art",            # 保存下载图片的目录
    num=30,                             # 最大下载数量
    download_streams=True,              # 下载视频流（如可用）（默认：False）
    min_resolution=(512, 512),          # 最低分辨率（宽，高）（默认：None）
    cache_path="art.json",              # 缓存抓取数据为 JSON 的路径（默认：None）
    caption="txt",                      # 标题格式
    delay=0.4,                          # 请求之间的延迟（默认：0.2）
)
```

---

### 1a. 使用 Cookies 抓取私密内容

要访问私密画板和图钉，需要 Pinterest 账户的 cookies。

#### 步骤 1：获取 Cookies

首先登录 Pinterest 以获取浏览器 cookies。

```python
import os
import json
from pinterest_dl import PinterestDL

# 确保不要在代码中暴露密码
email = input("输入 Pinterest 邮箱: ")
password = os.getenv("PINTEREST_PASSWORD")

# 初始化浏览器并登录 Pinterest（默认使用 Playwright）
cookies = PinterestDL.with_browser(
    browser_type="chromium",  # 'chromium' 或 'firefox'
    headless=True,
).login(email, password).get_cookies(
    after_sec=7,  # 捕获 cookies 前等待的时间。登录可能需要时间。
)

# 将 cookies 保存到文件
with open("cookies.json", "w") as f:
    json.dump(cookies, f, indent=4)
```

#### 步骤 2：使用 Cookies 抓取

获取 cookies 后，可以用它们抓取私密画板和图钉。

```python
import json
from pinterest_dl import PinterestDL

# 从文件加载 cookies
with open("cookies.json", "r") as f:
    cookies = json.load(f)

# 使用指定设置初始化并运行 Pinterest 图片下载器
images = (
    PinterestDL.with_api()
    .with_cookies(
        cookies,  # Selenium 格式的 cookies
    )
    .scrape_and_download(
        url="https://www.pinterest.com/pin/1234567",  # 假设这是私密画板 URL
        output_dir="images/art",                       # 保存下载图片的目录
        num=30,                                        # 最大下载数量
    )
)
```

---

## 2. 底层控制方法

如果需要对抓取和下载图片进行更精细的控制，请使用这些方法。

### 2a. 使用 API 模式

#### 抓取媒体

```python
import json
from pinterest_dl import PinterestDL

# 1. 使用 API 初始化 PinterestDL 并抓取媒体
scraped_medias = PinterestDL.with_api().scrape(
    url="https://www.pinterest.com/pin/1234567",  # Pinterest 页面的 URL
    num=30,                                        # 最大抓取图片数量
    min_resolution=(512, 512),                     # 仅 API 模式可设置。浏览器模式需下载后修剪。
)

# 2. 下载媒体
# 将媒体下载到指定目录
output_dir = "images/art"
downloaded_items = PinterestDL.download_media(
    media=scraped_medias, 
    output_dir=output_dir, 
    download_streams=True  # 下载视频流（如可用）；否则仅下载图片
)

# 3. 将抓取的数据保存到 JSON（可选）
# 将抓取的数据转换为字典并保存到 JSON 文件以供将来访问
media_data = [media.to_dict() for media in scraped_medias]
with open("art.json", "w") as f:
    json.dump(media_data, f, indent=4)

# 4. 将 Alt 文本添加为元数据（可选）
# 从媒体中提取 `alt` 文本并将其设置为下载文件中的元数据
PinterestDL.add_captions_to_meta(images=downloaded_items)

# 5. 将 Alt 文本添加为文本文件（可选）
# 从媒体中提取 `alt` 文本并将其保存为下载目录中的文本文件
PinterestDL.add_captions_to_file(downloaded_items, output_dir, extension="txt")
```

#### 搜索媒体

```python
import json
from pinterest_dl import PinterestDL

# 1. 使用 API 初始化 PinterestDL
scraped_medias = PinterestDL.with_api().search(
    query="艺术",                 # Pinterest 搜索关键词
    num=30,                       # 最大抓取图片数量
    min_resolution=(512, 512),    # 最低分辨率
    delay=0.4,                    # 请求之间的延迟（默认：0.2）
)

# 2-5. 后续步骤与上面相同
# （下载、保存 JSON、添加标题等）
```

---

### 2b. 使用浏览器模式 (Playwright)

Playwright 是默认的浏览器自动化后端，提供更快速、更可靠的抓取。

```python
import json
from pinterest_dl import PinterestDL

# 1. 使用浏览器初始化 PinterestDL（Playwright - 默认）
scraped_medias = PinterestDL.with_browser(
    browser_type="chromium",  # 要使用的浏览器类型（'chromium' 或 'firefox'）
    headless=True,          # 在无头模式下运行浏览器
    ensure_alt=True,        # 确保每张图片都有 alt 文本（默认：False）
).scrape(
    url="https://www.pinterest.com/pin/1234567",  # Pinterest 页面的 URL
    num=30,                                        # 最大抓取图片数量
)

# 2. 将抓取的数据保存到 JSON
# 将抓取的数据转换为字典并保存到 JSON 文件以供将来访问
media_data = [media.to_dict() for media in scraped_medias]
with open("art.json", "w") as f:
    json.dump(media_data, f, indent=4)

# 3. 下载媒体
# 将媒体下载到指定目录
output_dir = "images/art"
downloaded_media = PinterestDL.download_media(
    media=scraped_medias,
    output_dir=output_dir,
    download_streams=False,  # 浏览器模式暂不支持视频流
)

# 4. 按分辨率修剪媒体（可选）
# 移除不符合最低分辨率标准的媒体
kept_media = PinterestDL.prune_images(images=downloaded_media, min_resolution=(200, 200))

# 5. 将 Alt 文本添加为元数据（可选）
# 从媒体中提取 `alt` 文本并将其设置为下载文件中的元数据
PinterestDL.add_captions_to_meta(images=kept_media)

# 6. 将 Alt 文本添加为文本文件（可选）
# 从媒体中提取 `alt` 文本并将其保存为下载目录中的文本文件
PinterestDL.add_captions_to_file(kept_media, output_dir, extension="txt")
```

### 2c. 使用浏览器模式 (Selenium - 遗留)

Selenium 作为备用方案保留，以保持向后兼容性。

```python
import json
import warnings
from pinterest_dl import PinterestDL

# 抑制弃用警告（Selenium 将在 1.1.0 版本弃用）
with warnings.catch_warnings():
    warnings.simplefilter("ignore", DeprecationWarning)
    
    # 使用 Selenium 初始化 PinterestDL
    scraped_medias = PinterestDL.with_selenium(
        browser_type="chrome",  # 要使用的浏览器类型（'chrome' 或 'firefox'）
        headless=True,          # 在无头模式下运行浏览器
        ensure_alt=True,        # 确保每张图片都有 alt 文本（默认：False）
    ).scrape(
        url="https://www.pinterest.com/pin/1234567",  # Pinterest 页面的 URL
        num=30,                                        # 最大抓取图片数量
    )

# 继续下载、保存 JSON、添加标题等操作
```

---

## 静态方法参考

### `PinterestDL.download_media()`

从抓取的媒体对象下载文件。

```python
PinterestDL.download_media(
    media: List[PinterestMedia],
    output_dir: str,
    download_streams: bool = False
) -> List[PinterestMedia]
```

### `PinterestDL.prune_images()`

过滤掉低于最低分辨率的图片。

```python
PinterestDL.prune_images(
    images: List[PinterestMedia],
    min_resolution: Tuple[int, int]
) -> List[PinterestMedia]
```

### `PinterestDL.add_captions_to_meta()`

将 alt 文本嵌入为图片元数据。

```python
PinterestDL.add_captions_to_meta(
    images: List[PinterestMedia]
) -> None
```

### `PinterestDL.add_captions_to_file()`

将 alt 文本保存到独立文件。

```python
PinterestDL.add_captions_to_file(
    images: List[PinterestMedia],
    output_dir: str,
    extension: str = "txt"  # 'txt' 或 'json'
) -> None
```

---

## 完整示例工作流

```python
from pinterest_dl import PinterestDL
import json

# 步骤 1：使用 cookies 初始化
with open("cookies.json", "r") as f:
    cookies = json.load(f)

scraper = PinterestDL.with_api().with_cookies(cookies)

# 步骤 2：抓取媒体
medias = scraper.scrape(
    url="https://www.pinterest.com/pin/123456",
    num=50,
    min_resolution=(1024, 768)
)

# 步骤 3：缓存结果
with open("scraped.json", "w") as f:
    json.dump([m.to_dict() for m in medias], f, indent=4)

# 步骤 4：下载
downloaded = PinterestDL.download_media(
    media=medias,
    output_dir="downloads",
    download_streams=True
)

# 步骤 5：添加标题
PinterestDL.add_captions_to_meta(downloaded)
PinterestDL.add_captions_to_file(downloaded, "downloads", "txt")

print(f"成功下载 {len(downloaded)} 个文件")
```

---

返回 [主 README](../README_CN.md)
