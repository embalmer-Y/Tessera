---
name: tessera-workflow
description: Tessera 开发流程纪律——阶段白名单、review 门、军规十条摘要（agent 行为约束）
sources:
  - AGENTS.md
  - docs/project-plan.md
---

# Tessera 开发流程（workflow）

> 派生自 AGENTS.md §4/§5 与 docs/project-plan.md（双轨 M/MA 序）。镜像纪律：
> 本 skill 为摘要，权威以源文档为准。

## 主线与阶段白名单

- 主线：research → owner 裁决 → design → owner 确认 → impl（实现+测试）→ 阶段退出 review → 下一阶段。
- 阶段产出白名单：research 只出 `docs/research/*.md` 与 Q 登记；design 只出 `design/` 规格与修订；impl 只出规格清单内代码 + 同批测试。**越权产出 = 撤回并留痕**。
- 单会话预算：一个会话交付一个可验证交付单元；超出部分登记待办另起会话。
- 决策登记：一切选型与默认值先登记 Q（`decisions.md`），owner 裁决成 DEC 后才落盘/进代码常量。

## APP spec 四节模板（NV-2 质量门，2026-10-11 起）

app_develop 的 spec 推荐四节模板（缺节/判据无引号串 = 阻塞级）：

```
【需求】APP 做什么（行为语义，确定性描述）。
【资源】caps=["class:op:inst"...]；fs_paths=["/SD:/..."]（可选，仅 fs 类）。日志判据行需要 "log:write:0"（V0.4.0 起生产语义 fail-closed——TEST 根签名包自动授予，生产包必声明）。状态持久化（跨重启/升级保留 ≤250B）需要 "kv:write:0"+"kv:read:0"（ts_kv_save/ts_kv_load）。
【判据】输出行 "精确判据串"（引号包裹，≥3 字符）即达成；心跳稳态。
【安全声明】输出经保护层限幅；确定性输出；无越权访问。
```

【判据】节引号串是修复闭环（repair_loop）与 sim↔real 对拍的机器判据
单一事实源——写 spec 时必须把终态判据行写成精确串（含格式细节如补零）；
**主判据串写在【判据】节最前**（闭环只认主判据，附属证据串随后）。

## Review 门（必须停下等 owner，不得自裁）

1. 一切选型与默认值；2. 阶段退出（DoD 对照）；3. 公共 API/文件格式/网络协议/权限模型变更；
4. 安全合同任何改动；5. 技术栈变更（须证阻塞性）。

## 军规十条（违反即流程缺陷）

1. 流程至上（白名单不越、门不闯）；2. 无 Q 不落盘；3. 文字自包含（现状+动因+后果）；
4. 全库 UTF-8 无 BOM；5. git 每交付单元一提交、失败留痕；6. 跨文档标识符登记 `docs/names.md`；
7. 测试与实现同批、失败如实报告；8. 结论落盘（聊天不是状态）；9. 禁顺手重构（登记不动手）；
10. 交付即验证（DoD + 构建/测试全绿 + lint）。

## 当前双轨（project-plan）

固件 M 系（M0…M3b→板级）与 Agent MA 系（MA0…MA3）交替推进；依赖咬合点与 owner 待办
（GitHub 远端、Zephyr SDK for Linux）见 plan §4/§5。
