---
name: tessera-tsap
description: TSAP v1 包格式与 manifest 字段——打包/验签/部署的容器契约（APP 开发必读）
sources:
  - firmware/module/tessera/include/ts/tsap.h
  - design/LLD-ts-appmgr.md
  - design/LLD-A05-tsap-tools.md
---

# TSAP v1 容器（打包与 APP 开发）

> 派生自 include/ts/tsap.h（M2a 定稿）与 LLD-A05。权威 = 源文件。

## 容器布局

```
16B 头（大端）：magic "TSAP"(4) | fmt_ver u16(=1) | manifest_len u32 | wasm_len u32 | rsv u16
之后：manifest(CBOR) ‖ wasm ‖ COSE_Sign1(ed25519，覆盖 manifest‖wasm)
```

- 多字节整数一律**大端**；manifest 为 canonical CBOR（Agent/固件双实现互验）。
- 验签失败 = TS_E_INVALID_SIG + 留痕（越权事件外发，合同 10）。

## manifest 字段（TsapManifest v1）

`{ app_id, app_ver, min_fw_ver, caps[], stack_kb, heap_kb, exports[] }`

- `app_id`：反向域名式；`app_ver`/`min_fw_ver`：semver。
- `caps`：ts_perm_v1 能力文法（权限硬边界——越权访问拒绝并留痕，合同 10）。
- `stack_kb` ≤ 64；`heap_kb` 每板动态预算（DEC-27/DEC-28）。
- **`exports` 必含 `health_ping`**（健康探针，LLD-ts-appmgr §2——缺 = 打包拒绝）。

## 工具链

- `tsap_keygen`（strict）→ `tsap_package`（无签名不产出——硬点）→ `tsap_verify`
  （容器头 + COSE 双实现验签 + manifest 解码）。
- 部署面消费见 deploy_push_app：分块上传 → 固件 verify（容器事实对拍）→ activate。
