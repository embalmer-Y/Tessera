# SPDX-License-Identifier: Apache-2.0
"""创作工作区与循环引擎（LLD-A08 · DEC-57 Q-38）：域无关平台组件。

AG2 = 工作区模型 + ws_* 编辑动词（本包 workspace/tools）；
AG3 = 循环引擎/验证器协议/快照（loop/verifier/snapshot——LLD-A08 §4-§6）。
"""

from tessera_agent.creation.workspace import Workspace

__all__ = ["Workspace"]
