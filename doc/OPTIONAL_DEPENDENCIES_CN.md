# 可选依赖说明

从 1.0.x 版本起，`pillow` 和 `pyexiv2` 被调整为可选依赖，以减小安装体积，让用户按需安装。

## 快速参考

| 功能 | 所需包 | 安装命令 |
|------|--------|----------|
| 核心抓取与下载 | 无（内置） | `pip install pinterest-dl` |
| 图像分辨率检测 | `pillow` | `pip install pinterest-dl[image]` |
| 图像修剪（`min_resolution`） | `pillow` | `pip install pinterest-dl[image]` |
| EXIF 元数据嵌入 | `pyexiv2` | `pip install pinterest-dl[exif]` |
| 所有图像/元数据功能 | 两者 | `pip install pinterest-dl[all]` |

## 安装方式

### 基础安装
仅核心功能，不含图像分析：
```bash
pip install pinterest-dl
```

### 包含图像操作
启用分辨率检测和图像修剪功能：
```bash
pip install pinterest-dl[image]
```

### 包含 EXIF 元数据支持
启用将 alt 文本嵌入图片 EXIF 元数据的功能：
```bash
pip install pinterest-dl[exif]
```

### 包含所有可选功能
同时安装 Pillow 和 pyexiv2：
```bash
pip install pinterest-dl[metadata]
# 或
pip install pinterest-dl[all]
```

### 开发环境
包含测试工具（pytest、pytest-mock）：
```bash
pip install pinterest-dl[dev,all]
```

## 不安装可选依赖能用哪些功能？

**不需要可选依赖即可使用：**
- 抓取 URL（画板、图钉）
- 搜索图片
- 下载图片和视频
- 将描述文字保存为独立文本文件（`caption="txt"`）
- 将完整元数据保存为 JSON（`caption="json"`）
- 通过 cookies 访问私密画板
- 所有 CLI 命令（依赖可选包的功能除外）

**需要可选依赖：**
- 分辨率检测（`set_local_resolution()`），需要 `pillow`
- 使用 `min_resolution` 参数修剪图像，需要 `pillow`
- 使用 `caption="metadata"` 嵌入 EXIF 元数据，需要 `pyexiv2`

## 缺少依赖时的提示

如果调用了需要可选依赖的功能，会收到明确的错误提示：

```python
# 未安装 pillow
images = scraper.scrape_and_download(
    url="...",
    min_resolution=(512, 512)
)
# ImportError: Pillow is required for image operations. Install it with: pip install pillow
```

```python
# 未安装 pyexiv2
from pinterest_dl.storage.media import write_exif_comment

write_exif_comment(media, "My caption")
# ImportError: pyexiv2 is required for EXIF operations. Install it with: pip install pyexiv2
```

## 性能说明

可选依赖采用**懒加载**并在模块级别缓存：

1. **首次调用**：执行一次导入检查，结果缓存
2. **后续调用**：直接使用缓存引用，几乎零开销
3. **从未调用**：完全没有导入开销

这样设计的好处：
- 批量处理图片时，热路径零额外开销
- 不需要可选功能时，启动更快
- 核心场景安装体积最小

## 迁移指南

### 从旧版本升级

如果你从 `pillow` 和 `pyexiv2` 还是必选依赖的旧版本升级：

**方案一：安装全部功能（推荐大多数用户）**
```bash
pip install --upgrade pinterest-dl[all]
```

**方案二：按需安装**
```bash
# 如果你用到了 min_resolution：
pip install --upgrade pinterest-dl[image]

# 如果你用到了 caption="metadata"：
pip install --upgrade pinterest-dl[exif]

# 两者都用：
pip install --upgrade pinterest-dl[all]

# 两者都不用：
pip install --upgrade pinterest-dl
```

### 打包分发时

如果你在为某个发行版打包 pinterest-dl：

```python
# requirements.txt 或 setup.py
pinterest-dl[all]  # 包含所有可选功能

# 或明确指定：
pinterest-dl
pillow>=10.4.0
pyexiv2
```

## 技术细节

### 懒加载实现

懒加载在 `pinterest_dl/storage/media.py` 中实现：

```python
# 模块级缓存（每个进程只检查一次）
_PIL: Optional[Any] = None
_PIL_available: Optional[bool] = None

def _get_PIL() -> Any:
    """懒加载 PIL，缓存结果。"""
    global _PIL, _PIL_available

    if _PIL_available is None:
        try:
            from PIL import Image
            _PIL = Image
            _PIL_available = True
        except ImportError:
            _PIL_available = False

    if not _PIL_available:
        raise ImportError(
            "Pillow is required for image operations. "
            "Install it with: pip install pillow"
        )

    return _PIL
```

优点：
- 每个 Python 进程只检查一次导入
- 热路径（如处理大量图片）零额外开销
- 缺少依赖时给出清晰的错误提示
- 通过 `TYPE_CHECKING` 对类型检查器友好

### 包配置

可选依赖在 `pyproject.toml` 中定义：

```toml
[project.optional-dependencies]
dev = ["pytest>=7.0.0", "pytest-mock>=3.10.0"]
image = ["pillow==10.4.0"]
exif = ["pyexiv2"]
metadata = ["pillow==10.4.0", "pyexiv2"]
all = ["pillow==10.4.0", "pyexiv2"]
```

## 常见问题

**为什么要把这些依赖改成可选的？**  
为了减小安装体积，让用户按需安装。如果你只需要基础抓取功能，不需要图像分析，就没必要安装 pillow 或 pyexiv2。

**我的现有代码会受影响吗？**  
不会，只要 pillow/pyexiv2 已安装就没有问题。运行 `pip install --upgrade pinterest-dl[all]` 即可确保所有可选依赖都已安装。

**忘了哪个功能需要哪个依赖怎么办？**  
错误信息会直接告诉你需要安装什么，例如："Pillow is required for image operations. Install it with: pip install pillow"。

**会影响性能吗？**  
不会。懒加载加缓存机制确保零性能开销，每个进程只检查一次导入。

**可以单独安装这些依赖吗？**  
可以，直接安装也完全没问题：
```bash
pip install pinterest-dl
pip install pillow pyexiv2
```

**我应该用哪种安装方式？**
- 大多数用户：`pip install pinterest-dl[all]`，最省心
- 最小安装：`pip install pinterest-dl`，不需要图像分析时用
- 按需定制：根据实际需求选择 `[image]` 或 `[exif]`

## 另请参阅

- [README_CN.md](../README_CN.md) - 安装说明
- [API_CN.md](API_CN.md) - Python API 文档
- [CLI_CN.md](CLI_CN.md) - 命令行文档
