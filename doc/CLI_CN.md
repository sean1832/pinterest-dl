# 命令行使用指南

本文档详细介绍 Pinterest-DL 命令行界面的所有命令和选项。

## 目录
- [通用命令结构](#通用命令结构)
- [命令详解](#命令详解)
  - [1. login - 登录](#1-login---登录)
  - [2. scrape - 抓取](#2-scrape---抓取)
  - [3. search - 搜索](#3-search---搜索)
  - [4. download - 下载](#4-download---下载)

---

## 通用命令结构

```bash
pinterest-dl [命令] [选项]
```

| 命令       | 描述                        |
| ---------- | --------------------------- |
| `login`    | 登录 Pinterest 获取 cookies |
| `scrape`   | 从 URL 抓取媒体             |
| `search`   | 通过关键词搜索媒体          |
| `download` | 从 JSON 文件下载媒体        |

---

## 命令详解

### 1. login - 登录

获取浏览器 cookies 用于访问私密画板和图钉。

```bash
pinterest-dl login [选项]
```

![登录演示](images/pinterest-dl-login.gif)

#### 选项

| 选项                              | 说明             | 默认值         |
| --------------------------------- | ---------------- | -------------- |
| `-o`, `--output [文件]`           | cookies 保存路径 | `cookies.json` |
| `--client [chromium/firefox]`     | 使用的浏览器类型 | `chromium`     |
| `--backend [playwright/selenium]` | 浏览器自动化后端 | `playwright`   |
| `--headful`                       | 显示浏览器窗口   | 无             |
| `--incognito`                     | 启用无痕模式     | 无             |
| `--verbose`                       | 显示调试信息     | 无             |

#### 使用示例

```bash
# 使用默认设置登录
pinterest-dl login

# 保存 cookies 到自定义文件
pinterest-dl login -o my_cookies.json

# 使用 Firefox 浏览器
pinterest-dl login --client firefox

# 显示浏览器窗口（非无头模式）
pinterest-dl login --headful
```

> [!TIP]
> 执行后会提示输入 Pinterest 账号密码，成功登录后 cookies 将保存到指定文件。

---

### 2. scrape - 抓取

从单个/多个 Pinterest URL 或文件列表抓取媒体。

```bash
# 单个或多个 URL：
pinterest-dl scrape <url1> <url2> ...

# 从文件（每行一个 URL）：
pinterest-dl scrape -f urls.txt [选项]
pinterest-dl scrape -f urls1.txt -f urls2.txt [选项]

# 从标准输入：
cat urls.txt | pinterest-dl scrape -f - [选项]
```

![抓取演示](images/pinterest-dl-scrape.gif)

#### 选项

| 选项                                 | 说明                                                 | 默认值         |
| ------------------------------------ | ---------------------------------------------------- | -------------- |
| `-f`, `--file [文件]`                | URL 列表文件路径（`-` 表示 stdin）                   | 无             |
| `<url>`                              | Pinterest URL                                        | 必填           |
| `-o`, `--output [目录]`              | 保存目录（不指定则输出到 stdout）                    | 无             |
| `-c`, `--cookies [文件]`             | cookies 文件路径                                     | `cookies.json` |
| `-n`, `--num [数量]`                 | 最大下载数量                                         | `100`          |
| `-r`, `--resolution [宽x高]`         | 最低分辨率（如 `512x512`）                           | 无             |
| `--video`                            | 下载视频流（如可用）                                 | 无             |
| `--skip-remux`                       | 跳过 ffmpeg 转封装，输出原始 .ts 文件（无需 ffmpeg） | 无             |
| `--timeout [秒]`                     | 请求超时时间                                         | `3`            |
| `--delay [秒]`                       | 请求间隔延迟                                         | `0.2`          |
| `--cache [路径]`                     | 保存抓取结果到 JSON                                  | 无             |
| `--caption [txt/json/metadata/none]` | 标题保存格式                                         | `none`         |
| `--ensure-cap`                       | 要求每张图都有 alt 文本                              | 无             |
| `--client [api/chromium/firefox]`    | 抓取方式                                             | `api`          |
| `--backend [playwright/selenium]`    | 浏览器自动化后端（浏览器模式）                       | `playwright`   |
| `--headful`                          | 显示浏览器窗口（浏览器模式）                         | 无             |
| `--incognito`                        | 无痕模式（浏览器模式）                               | 无             |
| `--verbose`                          | 调试输出                                             | 无             |

#### 使用示例

```bash
# 从单个 URL 抓取 50 张图片
pinterest-dl scrape https://www.pinterest.com/pin/123456 -o output -n 50

# 从画板抓取所有图片
pinterest-dl scrape https://www.pinterest.com/username/board-name/ -o my_images

# 使用 cookies 抓取私密内容
pinterest-dl scrape https://www.pinterest.com/pin/private-pin -c cookies.json -o private

# 设置最低分辨率过滤
pinterest-dl scrape <url> -o output -r 1024x768

# 同时下载视频流（转换为 MP4，需要 ffmpeg）
pinterest-dl scrape <url> -o output --video

# 下载视频为原始 .ts 文件（无需 ffmpeg）
pinterest-dl scrape <url> -o output --video --skip-remux

# 保存元数据到文本文件
pinterest-dl scrape <url> -o output --caption txt

# 从文件批量抓取
pinterest-dl scrape -f urls.txt -o batch_output

# 使用浏览器模式抓取
pinterest-dl scrape <url> -o output --client chrome
```

---

### 3. search - 搜索

通过关键词搜索媒体（仅 API 模式支持）。

```bash
# 简单查询：
pinterest-dl search <关键词1> <关键词2> ... [选项]

# 从文件：
pinterest-dl search -f queries.txt [选项]
pinterest-dl search -f q1.txt -f q2.txt [选项]

# 从标准输入：
cat queries.txt | pinterest-dl search -f - [选项]
```

![搜索演示](images/pinterest-dl-search.gif)

#### 选项

| 选项                                 | 说明                                                 | 默认值         |
| ------------------------------------ | ---------------------------------------------------- | -------------- |
| `-f`, `--file [文件]`                | 关键词列表文件路径（`-` 表示 stdin）                 | 无             |
| `<query>`                            | 搜索关键词                                           | 必填           |
| `-o`, `--output [目录]`              | 保存目录（不指定则输出到 stdout）                    | 无             |
| `-c`, `--cookies [文件]`             | cookies 文件路径                                     | `cookies.json` |
| `-n`, `--num [数量]`                 | 最大下载数量                                         | `100`          |
| `-r`, `--resolution [宽x高]`         | 最低分辨率                                           | 无             |
| `--video`                            | 下载视频流（如可用）                                 | 无             |
| `--skip-remux`                       | 跳过 ffmpeg 转封装，输出原始 .ts 文件（无需 ffmpeg） | 无             |
| `--timeout [秒]`                     | 请求超时时间                                         | `3`            |
| `--delay [秒]`                       | 请求间隔延迟                                         | `0.2`          |
| `--cache [路径]`                     | 保存结果到 JSON                                      | 无             |
| `--caption [txt/json/metadata/none]` | 标题保存格式                                         | `none`         |
| `--ensure-cap`                       | 要求每张图都有 alt 文本                              | 无             |
| `--verbose`                          | 调试输出                                             | 无             |

#### 使用示例

```bash
# 搜索并下载风景照片
pinterest-dl search "风景摄影" -o landscapes -n 50

# 搜索多个关键词
pinterest-dl search "抽象艺术" "现代设计" -o art -n 30

# 从文件批量搜索
pinterest-dl search -f queries.txt -o search_results

# 设置分辨率和缓存
pinterest-dl search "壁纸" -o wallpapers -r 1920x1080 --cache results.json
```

---

### 4. download - 下载

从之前保存的缓存文件下载媒体。

```bash
pinterest-dl download <缓存.json> [选项]
```

![下载演示](images/pinterest-dl-download.gif)

#### 选项

| 选项                         | 说明       | 默认值           |
| ---------------------------- | ---------- | ---------------- |
| `-o`, `--output [目录]`      | 保存目录   | `./<json文件名>` |
| `-r`, `--resolution [宽x高]` | 最低分辨率 | 无               |
| `--verbose`                  | 调试输出   | 无               |

#### 使用示例

```bash
# 从缓存文件下载
pinterest-dl download cached_data.json

# 指定输出目录
pinterest-dl download cached_data.json -o downloaded_images

# 设置分辨率过滤
pinterest-dl download cached_data.json -r 800x600

# 启用详细输出
pinterest-dl download cached_data.json --verbose
```

---

## 高级用法

### 管道和重定向

将 URL 列表通过管道传递：
```bash
cat urls.txt | pinterest-dl scrape -f - -o output
```

将抓取结果输出到 stdout（不下载）：
```bash
pinterest-dl scrape <url> -n 10
```

### 组合多个文件

```bash
# 从多个 URL 文件抓取
pinterest-dl scrape -f urls1.txt -f urls2.txt -f urls3.txt -o combined

# 从多个查询文件搜索
pinterest-dl search -f queries1.txt -f queries2.txt -o search_all
```

### 调试和日志

启用详细输出查看完整日志：
```bash
pinterest-dl scrape <url> -o output --verbose
```

---

返回 [主 README](../README_CN.md)
