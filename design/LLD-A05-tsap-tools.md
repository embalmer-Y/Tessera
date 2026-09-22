# LLD-A05 · TSAP 打包签名工具（tsap_*）· v0.1 草案

> **上游**：HLD-agent §2/A05；决策 DEC-21（TSAP v1 单文件容器）、DEC-05（签名分发）；签名栈定案 R5 §4 / DR-21。格式权威 = 固件侧 `LLD-ts-appmgr.md` §2（本模块为 Agent 侧实现，**schema 同源镜像**）。

## 1. 库路线与纪律（R5 §4）

- 栈：`cbor2`（manifest 一律 `canonical=True`）+ `pycose`（COSE_Sign1/EdDSA）+ `cryptography`（密钥原语）。
- **单键纪律（DR-21）**：protected header 只放 `{1: -8}`（alg=EdDSA），KID 等入 unprotected——规避 pycose 非 canonical map 序的字节复现隐患。
- **DIY fallback 双验**：实现 `_sign_pycose()` 与 `_sign_diy()`（cryptography Ed25519 + cbor2 手构 RFC 9052 Sig_structure）；测试双实现互验（pycose 验 DIY 产物 / DIY 验 pycose 产物）；运行时用 pycose，异常切换 DIY 并在结果中标注 signer 实现。

## 2. Manifest 镜像 schema

- `TsapManifestV1`（Pydantic 模型，字段与固件 LLD-ts-appmgr §2 逐项对齐：app_id/version/min_fw/api_ver（ts_api_v1）/perms（ts_perm_v1 能力文法）/stack/heap/entry…）；**固件侧定稿前本模型标 baseline，M2a 后同步**（未决依赖）。
- 产物校验器（DomainPack 注册项）：模型校验 + 语义校验（perms 文法合法、预算上限不越 HLD §4.6 板表）。

## 3. 工具规格

### tsap_keygen（strict）
- Ed25519 密钥对生成；私钥写 `out_dir/{name}.key`（0600，路径白名单内），**私钥内容不进任何返回/日志/审计**；返回 {pub_key_path, pub_key_fingerprint}。
- 定位：**开发密钥**（dev 签名链）。生产根密钥体系（烧录根公钥、信任链）不属 Agent——属 prov/烧录纪律（合同 10），Agent 仅消费公钥做验签。

### tsap_package（confirm，句柄）
- 入参：{wasm_path, manifest, key_path}；执行：wasm 摘要 → manifest canonical CBOR → COSE_Sign1(phdr 单键, payload=manifest‖wasm) → 容器组装（格式随固件 LLD：TSAP magic/长度域）。
- **无签名不产出**（无豁免链硬点）：key 缺失/校验失败 = TA_E_TSAP 失败，**不降级出未签名包**。
- result：{package_path, size, manifest_digest, signature_fingerprint, signer_impl}。

### tsap_verify（auto）
- 全量反向：容器解析 → COSE 验签（pub_key）→ manifest 解码 → 字段校验 → 与固件侧验签语义对齐的检查清单（checks[]）。
- 用途：打包后自检、部署前复验（app_deploy 链内强制步骤）、往返回归测试。

## 4. 密钥与安全

- 密钥文件白名单路径 = workspace 内 `agent/keys/`（gitignore）；指纹（sha256 前 16 hex）作为展示/审计标识。
- 审计流记录 key 指纹与结果摘要，**永不记录私钥**（A00 §3 纪律的实例化）。

## 5. 测试要点（L7）

- 往返：package→verify 全绿；双实现互验矩阵；畸形矩阵（截断/坏签名/字段缺失/非 canonical 输入）对齐固件 L1 用例集（共享用例数据文件）。
- 单键纪律断言：手工构造多键 phdr 的包必须验签失败或被拒绝。
- 密钥纪律：0600 权限、内容不泄漏扫描。

## 6. 未决依赖

- 固件 M2a：TSAP v1 容器与 manifest 字段定稿（§2 镜像同步）；Q-19 提案 1（钉版）。
