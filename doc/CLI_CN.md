# 命令行使用指南

## 通用命令结构

```bash
pinterest-dl [命令] [选项]
```

| 命令                             | 描述                        |
| -------------------------------- | --------------------------- |
| [`login`](#1-login---登录)       | 登录 Pinterest 获取 cookies |
| [`scrape`](#2-scrape---抓取)     | 从 URL 抓取媒体             |
| [`search`](#3-search---搜索)     | 通过关键词搜索媒体          |
| [`download`](#4-download---下载) | 从 JSON 文件下载媒体        |

---

## 命令

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
| `--headful`                       | 显示浏览器窗口   | -              |
| `--incognito`                     | 启用无痕模式     | -              |
| `--verbose`                       | 显示调试信息     | -              |

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
| `-f`, `--file [文件]`                | URL 列表文件路径（`-` 表示 stdin）                   | -              |
| `<url>`                              | Pinterest URL                                        | -              |
| `-o`, `--output [目录]`              | 保存目录（不指定则输出到 stdout）                    | -              |
| `-c`, `--cookies [文件]`             | cookies 文件路径                                     | `cookies.json` |
| `-n`, `--num [数量]`                 | 最大下载数量                                         | `100`          |
| `-r`, `--resolution [宽x高]`         | 最低分辨率（如 `512x512`）                           | -              |
| `--video`                            | 下载视频流（如可用）                                 | -              |
| `--skip-remux`                       | 跳过 ffmpeg 转封装，输出原始 .ts 文件（无需 ffmpeg） | -              |
| `--timeout [秒]`                     | 请求超时时间                                         | `10`           |
| `--delay [秒]`                       | 请求间隔延迟                                         | `0.2`          |
| `--cache [路径]`                     | 保存抓取结果到 JSON                                  | -              |
| `--caption [txt/json/metadata/none]` | 标题保存格式                                         | `none`         |
| `--ensure-cap`                       | 要求每张图都有 alt 文本                              | -              |
| `--cap-from-title`                   | 使用图片标题作为说明                                 | -              |
| `--debug`                            | 启用调试模式，将 API 请求/响应保存到 JSON 文件       | -              |
| `--debug-dir [路径]`                 | 调试文件保存目录                                     | `debug`        |
| `--client [api/chromium/firefox]`    | 抓取方式                                             | `api`          |
| `--backend [playwright/selenium]`    | 浏览器自动化后端（浏览器模式）                       | `playwright`   |
| `--headful`                          | 显示浏览器窗口（浏览器模式）                         | -              |
| `--incognito`                        | 无痕模式（浏览器模式）                               | -              |
| `--verbose`                          | 调试输出                                             | -              |

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
| `-f`, `--file [文件]`                | 关键词列表文件路径（`-` 表示 stdin）                 | -              |
| `<query>`                            | 搜索关键词                                           | -              |
| `-o`, `--output [目录]`              | 保存目录（不指定则输出到 stdout）                    | -              |
| `-c`, `--cookies [文件]`             | cookies 文件路径                                     | `cookies.json` |
| `-n`, `--num [数量]`                 | 最大下载数量                                         | `100`          |
| `-r`, `--resolution [宽x高]`         | 最低分辨率                                           | -              |
| `--video`                            | 下载视频流（如可用）                                 | -              |
| `--skip-remux`                       | 跳过 ffmpeg 转封装，输出原始 .ts 文件（无需 ffmpeg） | -              |
| `--timeout [秒]`                     | 请求超时时间                                         | `10`           |
| `--delay [秒]`                       | 请求间隔延迟                                         | `0.2`          |
| `--cache [路径]`                     | 保存结果到 JSON                                      | -              |
| `--caption [txt/json/metadata/none]` | 标题保存格式                                         | `none`         |
| `--ensure-cap`                       | 要求每张图都有 alt 文本                              | -              |
| `--cap-from-title`                   | 使用图片标题作为说明                                 | -              |
| `--debug`                            | 启用调试模式，将 API 请求/响应保存到 JSON 文件       | -              |
| `--debug-dir [路径]`                 | 调试文件保存目录                                     | `debug`        |
| `--verbose`                          | 调试输出                                             | -              |


---

### 4. download - 下载

从之前保存的缓存文件下载媒体。

```bash
pinterest-dl download <缓存.json> [选项]
```

![下载演示](images/pinterest-dl-download.gif)

#### 选项

| 选项                                 | 说明                                                 | 默认值           |
| ------------------------------------ | ---------------------------------------------------- | ---------------- |
| `-o`, `--output [目录]`              | 保存目录                                             | `./<json文件名>` |
| `-r`, `--resolution [宽x高]`         | 最低分辨率                                           | -                |
| `--video`                            | 下载视频流（如可用）                                 | -                |
| `--skip-remux`                       | 跳过 ffmpeg 转封装，输出原始 .ts 文件（无需 ffmpeg） | -                |
| `--caption [txt/json/metadata/none]` | 标题保存格式                                         | `none`           |
| `--ensure-cap`                       | 要求每张图都有 alt 文本                              | -                |
| `--verbose`                          | 调试输出                                             | -                |
