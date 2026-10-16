# SPDX-License-Identifier: Apache-2.0
"""测试环境统一面：LN 注册表单例走纯内存模式（G 批 D1——防默认路径
落盘造成的跨测试泄漏与 CI 副作用；显式持久化用例在自身用例内构造
LnRegistry(path)。"""
import os

os.environ.setdefault("TESSERA_LNO_REGISTRY", "memory")
