# 测试

## 原则：默认测试套件不访问网络

Pinterest 的 API 属于非官方的逆向工程实现。测试套件在运行时绝对不应向 Pinterest 发送请求。如果每次跑测试都去访问他们的服务器，既浪费资源，也容易触发限流，对一个我们没有任何控制权的服务来说也不太礼貌。单元测试验证的是**我们自己的**代码逻辑，没有任何理由联网。

因此，默认测试套件完全离线运行，不依赖网络连接。这一限制是自动强制执行的，不是靠约定俗成。

## 运行测试

```bash
# 运行默认（离线）测试套件
pytest

# 详细输出
pytest -v

# 运行单个文件或测试用例
pytest tests/test_pinterest_api.py
pytest tests/test_pinterest_api.py::TestPinterestAPIUrlParsing::test_parse_pin_id_valid_url
```

如果尚未安装测试工具：

```bash
pip install -e ".[dev]"
```

## 离线是如何强制执行的

`tests/conftest.py` 中有一个 autouse fixture `_offline_guard`，作用于每一个测试：

1. 它替换了 `Api._get_default_cookies`，使得构建 `Api(...)` 实例时不再从 `https://www.pinterest.com` 获取默认 cookies。否则，每次在测试中创建 `Api(...)` 都会因为 `__init__` 的副作用触发一次真实请求。
2. 它阻断所有真实的出站 socket 连接。回环地址（`127.*`、`::1`、`localhost`）仍然允许访问，保证 asyncio 事件循环和 Playwright 等本地机制正常工作。任何其他连接尝试都会抛出异常：

   ```
   RuntimeError: Network access is not allowed in unit tests.
   Mark the test with @pytest.mark.integration to hit the real API.
   ```

这样，如果有新测试不小心访问了网络，测试会明确报错，而不是悄悄地去骚扰 Pinterest。

## 集成测试（API 健康检查）

单元测试无法发现 Pinterest 修改了 API，因为它们只是针对固定输入验证我们自己的解析逻辑。为了捕获 API 漂移，我们在 `tests/integration/` 下保留了一小批有意联网的测试，标记为 `@pytest.mark.integration`。这些测试被排除在默认运行之外（见 `pyproject.toml` 中的 `addopts`），不受离线限制。

只在确实需要时才运行它们：

```bash
pytest -m integration
```

保持这个套件尽量精简。几个真实断言就足以发现 API 变更；更多请求只会给 Pinterest 增加额外负担，却不能提供更多有效信号。

### 定期运行

`.github/workflows/integration.yml` 设置了每月定时触发和手动触发，不会在每次 push 时运行。每周一次的受控运行对 Pinterest 来说负载极低，同时能在非官方 API 发生变化时及时告警。

## 写需要联网的测试

默认用离线方式。通过 mock HTTP 客户端、`requests`、`m3u8.load`、`subprocess.run` 等边界来隔离网络，用模拟响应测试自己的业务逻辑。测试套件中大部分用例已经这样做了。

只有当测试的目的本身就是验证 Pinterest 真实 API 的行为时，才有理由联网。这种情况下，把测试放在 `tests/integration/` 目录下并标记：

```python
import pytest

pytestmark = pytest.mark.integration

def test_something_live():
    ...
```

## 另请参阅

- [Dump 模式](DUMP.md) - 捕获真实 API 请求和响应，用于调试和分析
- [API 文档](API.md)
