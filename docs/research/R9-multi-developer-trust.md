# R9 · 多开发者信任链调研（DEC-56 · R 批④）——生态批设计输入

> **日期**：2026-10-13 · **触发**：DEC-56 D5（多开发者类安卓生态；分期裁决 = 生态批前维持单开发者单根）· **消费方**：生态批 design。
> **方法**：web 实抓（Android 官方签名文档 / iOS 描述文件 / MCUboot / TUF-Uptane / RFC 9052 / OpenWrt / sigstore——来源见 §8）+ 本地事实（TSAP v2 = COSE_Sign1 ed25519 单根验签，DEC-49）。
> **结论先行**：① 安卓哲学 = **开发者身份即私钥**（自签、无中心 CA、设备侧纯密码学验证）——与 Tessera 单根模型最兼容；② **MCUboot 多公钥 + KEYHASH TLV 选键**是"单根多开发者"的最近嵌入式先例（编译期嵌多把 → 我们需要的差异是运行期注册）；③ 撤销在离线设备上**没有在线手段**——TUF 的"根元数据重签 + 单调版本计数器"是离线可行解；④ 嵌入式设备"安装期本地 UI 确认权限"**无公开成熟先例**（我们是先行者位置，设计须自证）；⑤ 侧载反面教材 = OpenWrt sysupgrade 无验签（教训：任意介质输入必须先验签后接受）。

## 1. 安卓 APK 签名体系（哲学与机制）

- 演进：v1 JAR 签名（逐条目）→ v2 整文件 APK Signing Block（1MB 分块默克尔摘要、并行验证、防降级、防剥签）→ v3 **proof-of-rotation 密钥轮换谱系**（旧平台忽略仍可装）→ v4 fs-verity 流式（ADB 增量安装场景）。
- **核心哲学**：开发者身份 = 自签 X.509 证书，**无中心 CA**；v2 验签仅校验证书首张 SPKI 与公钥一致——身份是"持有同一密钥"的连续性，不是"权威背书"。
- 安装时验证 = 纯密码学；**无 CRL/OCSP/有效期环节**（v2 验证步骤实证）。
- 密钥丢失：自管密钥无法恢复、无法再更新同应用（换签名 = 视为新应用）；Play App Signing 代持 signing key 可重置 upload key（Android 13 起支持 key upgrade）——**商店代持与设备验证是两层**，Play 明示不参与安装时验签。

## 2. 开发者注册 / 信任根分发（Tessera 候选模式）

| 模式 | 机制 | 对 Tessera 的适配度 |
|---|---|---|
| 安卓自签 | 身份 = 私钥连续性；信任根 = 首次安装的签名 | 设备侧最简；但"首装即信任"对预装信任根的我们无需采用 |
| **MCUboot 多公钥** | 编译期嵌入多把公钥，镜像 KEYHASH TLV 迭代匹配选键（另有 MCUBOOT_HW_KEY 运行时供给哈希 / PSA BUILTIN_KEY 两模式） | **最近先例**——差异：MCUboot 编译期定集，我们需要**运行期注册**（provisioning 面扩展） |
| U-Boot FIT | 验签公钥编入 control DTB | 同为静态集；DTS 形态可借鉴 |
| TUF/Uptane | root.json 声明全部角色公钥 + 门限数；targets 可**多角色委托**（多供应商） | 元数据层信任链——生态成熟期的完整形态（含离线撤销）；V1 生态批过重 |
| iOS 描述文件 | 五要素绑定（谁〔证书链至 Apple Root〕/什么〔App ID〕/哪台设备/何时〔~一年过期〕/如何〔entitlements 白名单〕） | "profile = 权限+设备+时限打包签名"的形态值得借鉴（时效与设备绑定我们暂不需要） |

## 3. 撤销与过期（离线设备的现实）

- 安卓**无内建撤销**——事实约束是"更新须同签名"，恶意旧版本靠版本号 + 商店下架，设备侧无主动手段。
- **离线可行解 = TUF 模式**：root 角色重签 root.json（替换被泄密钥）+ 元数据版本号严格 N+1 链式校验（回滚保护）+ 单调版本计数器——无需在线 CRL。Uptane 为车载（部分在线）变体。
- Tessera 落点：设备侧维护**信任根表 + 单调版本号**（重装/更新信任表须版本 +1，防回滚复投被撤公钥）；被泄开发者的既有 APP 拒更新 + 可选卸载（逐 APP 处置随生态批 design）。

## 4. 权限的安装期确认

- 安卓三类：install-time（normal 安装即授 / **signature 同签名才授**）/ runtime（dangerous，6.0+ 弹窗可撤销）/ special。
- iOS entitlements = profile 内白名单，进程启动时强制。
- **嵌入式设备"本地 UI 确认新 APP 权限"：无公开成熟先例**（多轮检索未查到文档化案例）——我们若做即先行；注意 D6 合同泛化批的本地交互面是前提（无本地交互设备走网络装包 + Agent 侧呈报权限面替代）。

## 5. 签名算法与容器（技术基线核对）

- ed25519 嵌入式主流地位实证：MCUboot TLV 0x24 原生支持；sigstore cosign 支持 Ed25519（默认 ECDSA P-256，Ed25519 经导入）。
- **COSE（RFC 9052）**：COSE_Sign1（单签名）与 COSE_Sign（多签名，各签名独立 COSE_Signature、可混算法）结构**不可互换**；countersignature 因安全属性错误已从 RFC 9052 移除弃用——**TSAP 若需多签须换 COSE_Sign 容器（格式变更 = 门③）**。
- 生态普遍单签名（安卓 v2 格式支持多 signer 但"同签名才可更新"使其实际无意义；多签/门限仅见于 TUF 元数据层）——**Tessera 单签名 + 信任根表多键**与业界同型，无需多签容器。
- 基线：RSA2048/3072-PSS、ECDSA P-256、Ed25519 均在列——现选型 ed25519 无须动。

## 6. 侧载（sideload）模式

- 安卓 8.0 起 per-app "Install unknown apps"（安装器权限 + 设置开关 + 安装确认）——**本地侧载 = 显式开关 + 确认交互**，非默认敞开。
- **反面教材 OpenWrt**：sysupgrade 原生无密码学验签（仅元数据/sha256）——教训 = **任意介质输入必须先验签后接受**，Tessera 侧载（将来 SD/USB/网络任一）复用同一验签链，无例外。
- YubiKey 固件出厂固化不可现场升级（EUCLEAK 漏洞对旧固件永久有效为例证）——"不可升级"是安全收益与可维护性的极端取舍，不适用我们（我们有 MCUmgr OTA 底线）。

## 7. 呈递（Q-40 · 生态批设计决策——本文只登记方向，具体方案生态批展开）

1. **信任根形态**：建议 = 设备侧信任根表（prov 扩展：开发者公钥注册/撤销 + 单调版本号防回滚）+ COSE_Sign1 单签名维持（开发者身份 = 其私钥，安卓哲学）；TUF 完整元数据链挂生态成熟期再评。
2. **注册/撤销通道**：建议 = 网络侧（Agent/zenoh provisioning 命令面）起步；本地侧载通道随设备形态按需。
3. **安装期权限确认**：建议 = 有本地交互设备走本地确认（D6 前置）；无交互设备走 Agent 呈报 + strict 审批（复用审批闸）。
4. **TSAP 容器**：维持 COSE_Sign1；多签不引入（业界证据：单签名 + 多信任根已覆盖多开发者语义）。

## 8. 来源

- Android：source.android.com/docs/security/features/apksigning{,/v2,/v3,/v4}；developer.android.com app-signing + permissions overview + 8.0 changes
- iOS：TN3125 Inside Code Signing Provisioning Profiles
- MCUboot design（docs.mcuboot.com/design.html）；TUF specification/latest + FAQ；Uptane standard/best-practices
- RFC 9052；sigstore cosign key-management
- OpenWrt sysupgrade techref；docs.u-boot-project.org；YubiKey（EUCLEAK）
- 本地：TSAP v2 / DEC-49 / prov CBOR schema（DEC-30⑤）
