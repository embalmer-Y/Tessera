# AGENTS.md · Tessera 会话入口

> **本文件是什么**：每个开发会话（ZCode）的第一入口。由 K1 依据 `FOUNDING_PROMPT.md` v1.0（2026-09-18）改写生成。
> **权威顺序**：owner 最新裁决（`decisions.md` 中的 DEC）> `FOUNDING_PROMPT.md` > 本文件摘要。若本文件与上述冲突，以裁决/原文为准，并登记 Q 修正本文件。
> **维护规则**："当前状态"节每会话结束前更新；本文件的修改权在主会话。

## 1. 当前状态

- **2026-10-24（一六〇） · 五笔随令推送 ✅ CI 全绿 + deepseek/deepseek-v4.1-flash 模型 Agent 真实链路测试 ✅ 双运行 PASS（owner「先将当前的提交push，然后采用deepseek/deepseek-v4.1-flash该模型进行Agent的测试」）**。① **push**：e963b3b..b862413 五笔（画像去重/仓整理×2/安装程序/LLM 探针）→ **远端 CI run #207 @ b862413 = SUCCESS（8m55s）**（fw tag 全在远端核对无滞留）。② **模型测试**：探针全绿（384K 窗口/¥1/M in/max_tokens 下限 16）→ 配置（env.sh 凭据 600 仓外 + config.toml 模型串 anthropic:deepseek/deepseek-v4.1-flash）→ **app_develop 创作循环两次独立运行均 PACKAGED**（126.4s 单轮收敛 + 四轮含修复链收敛——wasm 998B/imports 仅 ts_log_write〔log-only 纪律模型自守〕/四回调导出齐/确定性编译 ✓/2412B 签名包在盘，签名密钥对经 tsap_keygen 新生成〔新机无存量私钥——仓外 600〕）；证据 agent-test-ds41-flash-20261024.txt。③ **两发现随批修复**：(a) **anthropic SDK 传递依赖未钉版**——最新版 Beta 类型映射崩（typing.Union 实例化，venv 全新安装即踩）/＜1.3 provider 导入面缺 → **pyproject 钉 anthropic==1.3.\***（pydantic-ai 2.47 配套域实测）；(b) **anthropic SDK 自拼 /v1/messages**——base 已含 /v1 → /v1/v1/messages 路由 404 → env 用剥尾形态 `.../api`（SDK 直调 200 实证）+ llm_probe 建议面增 **sdk_base_url** 字段（+测试断言）。④ 板上部署段：本机在板卡同网段（192.168.2.91/161——.91 即 x86 时代路由 IP）但双路由地址板卡发现为空——**板不在网，部署段待板上线补测**（如实）。⑤ 回归：agent 366+2s 全绿 + ruff + repo 11 + sync。**待 owner：① 本笔（fix 类：钉版 + 探针建议面增强 + 测试证据）review + push；② 板上线后可补全链部署判据（判据窗 `HB n=` 单调递增）；③ L 表续作随点向（第 5-8 feature 攒批收口 fw-v0.16.0）。**

- **2026-10-24（一五九） · LLM 端点探针 ✅（owner「根据大模型 URL 和 KEY 自动检测是否合法/是否联通/支持哪些模型/模型是否可用——参考 CCR」+ 实测端点随令 → DEC-80 + L 表第四单元）**。① **五面检测**：URL 静态合法性（scheme/主机/CRLF 注入拒绝）/ 连通性（httpx 异常族分类 DNS·超时·TLS + 代理提示）/ 协议检测（OpenAI Bearer + Anthropic x-api-key 双头 /models）/ 模型列表（id/api_name/name 三形态归一）/ **KEY 有效性 + 模型可用性合一于鉴权面最小调用**（200+usage=可用、401=key 无效、429=限流◐、404/400=模型名问题）+ 配置建议（provider 前缀/模型串/env 名）。② **实测回填三事实**（owner 端点 197 模型双协议）：/models **可不鉴权**（坏 key 亦 200——key 必经鉴权面判定，探针据此设计）；max_tokens 下限 16（8→400 参数错恰证明连通+鉴权通过）；reasoning 模型小预算文本空 ≠ 不可用。③ **凭据红线**：MCP 面 key 只经 key_env 环境变量名（值不入参数/审计）；CLI 同；报告全程无 key（测试断言贯穿）；owner 提供的 key 仅经环境变量实测（glm-5.3-flash 冒烟 1522ms），未落任何仓内文件。④ **面**：MCP llm_check（confirm）+ CLI llm-check + tools/env 85 步安装联动（非阻断）；测试 +10（MockTransport 零网络）——**agent 366+2s 全绿**。V0.16.0 累积 4 feature（DEC-75 线渐近）。**待 owner：① 本批五笔 review + push；② L 表续作随点向（第 5-8 feature 攒批收口 fw-v0.16.0）。**

- **2026-10-24（一五八） · 开发环境恢复 + 自动化环境部署脚本 ✅（owner「恢复项目开发环境」+「面向Linux（X86/AArch64）的自动化环境部署脚本……V0.16.0的一部分」+ 三点修正〔sudo 交互索密 root 密码 / 代理支持不做网络绕行（本机代理 http://127.0.0.1:7890 实测 ~6MB/s）/ **面向用户的产品安装程序定位**——LLM URL 与 API key 运行时输入或 --config 文件导入〕→ DEC-79 + L 表第三单元）**。① **本机恢复（x86_64/Ubuntu 26.04 无预装）**：apt 全家桶（root 密码 sudo -S——**clang-18 = 18.1.8 精确对齐 CI**）+ west 工作区 10G（代理通道；ghfast 种子续传）+ blobs 73 件 + SDK 1.0.1（xtensa+riscv64 解 gnu/）+ WAMR 444 屏障 + zenoh-pico 接入三步 + zenohd 1.10.1 + 固件 venv（**cmake 钉 3.31.6**——发行版 4.x 兼容风险免疫）。② **安装套件 tools/env/**：install.sh 单入口（标准档 = Agent venv + zenohd + esptool + 用户配置引导；--dev 追加固件全链）+ env_common（PIN_* 钉版/ARCH 探测/--proxy 全链代理〔git/wget/curl/pip/apt〕/sudo 交互〔tty sudo -v 索密 + 管道 sudo -S〕）+ steps×10 幂等（真实状态探测跳过——断点续装）+ verify_env.sh（checklist §11 ①-⑤ 机械）+ README（用户文档）+ 凭据红线（交互隐藏输入/--config KEY=VALUE 导入 → 600 仓外 env.sh + gitignored config.toml；已存在不覆盖）。③ **顺带修复两枚仓内潜伏缺陷（新机必踩——本机首战即抓）**：zenoh-pico-tls.patch tcp 段 hunk 计数头 19→12 + primitives.h 段缺 --- a/ 头行（git apply 严格域全拒；GNU patch 部分容忍——历史机侥幸过的根因）；**剥宏清单 12→13**（+AUTO_RECONNECT——R5-V 起补丁基线，checklist §3 滞后勘误 v1.4）。④ **验证**：twister 17/17 套件 115+2s（framework.net 并行 configure_file 竞态单跑 17/17 过——v1.148 同型环境域）+ **agent 356 passed + 2 skipped 全绿**（clang 恢复后 23 环境域失败全转正）+ repo pytest 11（含新 test_env_installer 6：bash -n/步骤引用/钉版三方/diff 计数自检器——正防本批补丁缺陷类别/help 契约/命名合规）+ ruff + sync。⑤ 环境注记：本机 root 密码经 stdin 使用未落任何仓内文件；LLM/WiFi 凭据未配置（env.sh 已建骨架——owner 手工补或删后交互重跑 install.sh）。证据 docs/evidence/env-restore-x86-20261024.txt。**待 owner：① 本批（+此前三笔）review + push；② L 表续作随点向（v4.5.0 平移捆绑/R12/R13/HW-4 P4 引脚采集候选不变）。**

- **2026-10-24（一五七） · 全仓整理与命名规范化 ✅ + 子智能体复核（owner「现在的项目已经开始变得混乱和臃肿……精简文档，规范各种文件的命名，不允许出现类似l1，l2, l3，review-01，review-02这类名称，删除不必要的文件，优化多余的代码……本次整理也作为V0.16.0的主要任务之一」→ DEC-78 + plan L 表第二单元）**。① **删除（14 件）**：九份一次性评审/自检档合并 `docs/history/review-archive.md`（IR/IR2/DR/SC 发现编号溯源链保留——代码出处注释改指档案）+ migration-x86（x86 机已销毁，env-rebuild-checklist 为唯一重建总单）+ agent-llm-smoke-01 + agent-demo-readiness-01（结论均已消费）+ agent/decisions.md（陈旧孤儿副本，零引用）+ legacy//hardware/ 空占位目录。② **改名（引用同步 200+ 文件；evidence 留痕原名不回溯）**：LLD-A00…A17/LLD-00 → **LLD-agent-\*/LLD-ts-common**（19 件）；docs \*-01 系列 16 件去号 + md12c-pdm-eval → pdm-audio-eval；demos D1…D9/D-\*/P4W → **demo-\***（16 目录描述性命名）；firmware/l3app → **firmware/tests/netlab**（native_sim zenoh 联调镜像——test_deploy_e2e 夹具路径同步）+ firmware/tests/l5 → **tests/safety_check**（check_l5 → check_safety_contract，CI/SKILL 同步）；tools/board 16 个会话代号脚本描述化（ak3_trust_e2e → e2e_trust_chain 等）；scenarios 2 件（d8-v1-ramp → lifecycle-ramp / d9-linkloss → linkloss）。③ **文档瘦身**：AGENTS §1 留近三会话 + 归档指针（658 → ~100 行；历史 560 行逐字入 docs/history/agents-status-archive.md）；project-plan 重构为现行计划（§1-6 + L 表 + 纪律 + 近 9 修订；§7-11g/F 表/旧修订入 docs/history/plan-archive-2026-10.md）；names 旧修订归档 + **§6 重命名登记册**（新旧映射唯一权威）。④ **新立**：`docs/std/naming.md`（命名规范：描述性 slug、纯序号名禁用；DEC/Q/R 等注册代号行内使用不在此限）+ `docs/evidence/README.md`（证据索引——55 件留痕一表可查）。⑤ **代码面**：agent Python 死模块扫描**零命中**（peer.py = 登记在案接口缝预留不算死码；ruff E/F/I/B/UP/ASYNC 严选既绿）；固件 C **逻辑**不动（~25 文件仅注释中的文档引用随全库改名同步；本会话机无 Zephyr 工具链——军规 10 交付即验证，逻辑面无可验证改法，如实登记）。⑥ **验证**：代码与路径形式引用扫零（豁免：evidence 留痕/历史档案/登记文本中的叙述性旧名——names §6 注记）+ agent pytest 333+2s+23 env-fail（clang 缺失环境域——stash 基线同败非本笔引入）+ ruff + repo pytest + sync --update。⑧ **复核修补轮**：**子智能体全库复核**（断链/孤儿引用/命名违例/映射一致性/归档保真/登记数字独立复跑六面——主体通过：§6 登记册 71 映射自洽、归档逐字保真、回归数字逐项吻合）抓出疏漏并全闭合——plan §7 重复引言块 + §2 旧引用（agent-demo-readiness/board-\*-01）+ 头部版本行 v1.37 陈旧 + E 节误带 §G 空悬节头 + **d8_client.py → lifecycle_client.py**（纯漏改，Python 不涉 C）+ evidence 索引 nv1 文件名误与计数 55→52 + naming 存量声明例外登记（d4/d6/d9_pkg.h 内嵌包头改名牵固件 C include 链——**随固件批缓办**入 §6）+ 固件三处裸 impl-review 注释补指档案 + 本项措辞勘误。⑦ **登记**：DEC-78 + plan v1.155（L 表 ✅ 第二单元）+ README 重写（仓库地图/Demo 表新名；hostools 原文笔误顺手修正）。**待 owner：① 本笔 + 此前 af3df09 review + push；② L 表续作随点向（候选不变：v4.5.0 平移捆绑/R12/R13/HW-4 P4 引脚采集）。**

- **2026-10-24（一五六） · 板卡画像同板去重合并 ✅（owner「atk-dnesp32s3b / dnesp32s3b 这两个应该是一块板子」——fix 类卫生笔，DEC-75：随修随发不占 feature 计数）**。① **同板实证**：正点原子 ATK DNESP32-S3B V1.1 = Zephyr 收录板 alientek/dnesp32s3b——两画像串口 by-id 全同（CH343 5909066900）/ boya 16MB 真硅同源 / atk 画像 `[hardware].zephyr_board="dnesp32s3b_esp32s3"` 即 BV2 收录键；重复根源 = BV2 实战（一五五）为同板经流水线新开画像。② **合并**：保留 `agent/boards/dnesp32s3b.toml`（**流水线规范名**——install_profile 生成 `agent/boards/<Zephyr 板名>.toml`；保留 atk- 前缀名会在下次 BV2 再生成时重现重复），吸收 atk 画像全部物理事实（[hardware] LEDB=pwm:0 引脚节〔source 补 BV2 adapt overlay LEDC_CH0_GPIO4 同源〕/ boya JEDEC 出处 / 持有器与 C0 注记）；现行镜像态取 BV2 值（zenoh.cube=dbc 显式回填〔一五五观察项④就此板闭合〕/ caps slot 32KB 注记 atkbench 产线镜像 2048 重烧后回填 / smoke=P4W 架构中立探针）；**atk-dnesp32s3b.toml 删除**。③ **附带修复（重复画像的实际危害）**：HW-1 `_match_catalog` 恰一命中门——「ATK DNESP32-S3B」全名提及此前双命中（norm 含于两 id）→ 拒绝绑定转收录检查路，去重后恰一命中恢复 profile 绑定；test_hardware 画像路径 / test_clarify ×2（提及改全名 + 断言）/ clarify 文档串随改；LLD-agent-board-validation §2 示例 id 同步（v0.1.2）。④ **验证**：受影响套件（clarify/hardware/board_validation/board_adapt）71 全绿 + ruff 干净 + 目录匹配 sanity 矩阵恰一命中；agent 全量 333 passed + 2 skipped + **23 failed = 新机 clang 缺失环境域**（stash 基线对照同败——非本笔引入；test_wasm_build 16 / creation_loop 5 / app_chain 2）。⑤ **环境注记（本会话机 = 全新环境）**：仓库 2026-10-24 全新 clone（zephyr 工作区/SDK/clang/wamr 均未建——固件面回归暂不可跑）；agent venv 已按 checklist §10 重建（**uv + Python 3.12 全 wheel 口径** @ `~/project/agent-venv`——本机 ensurepip 缺失、uv 在位）。⑥ **迁移注记**：本地 config `[agent] board_profile` 若仍指旧名须改 `dnesp32s3b`（load_bound_profile 缺文件静默跳过——不报错只跳面）。plan v1.154 / names 同日登记。**待 owner：① 本笔 review + push；② L 表累积池续作随点向（候选不变：v4.5.0 平移捆绑/R12/R13/HW-4 P4 引脚采集）。**

- **2026-10-23（一五五） · BV2 适配流水线真板首实战 ✅ 全链闭环（owner「我通过一些技术手段已经成功将两块板子都接入了开发机，需要请你评估供电是否足够，请你自行完成剩余开发项」→ §11h L 表新立 V0.16.0 累积池首单元〔DEC-75 纪律〕）**。① **供电评估双证**：hub Self-Powered（lsusb）+ dmesg 零过流（静态）+ 双板 WiFi 同网/部署突发/LN 扇出全程零 brownout 零 WDT（带载实证）——供电充足。② **BV2 全链**：atk flash-id 实测（boya 16MB = 一四三档案全同）→ 流水线生成五件套（**板级面唯一来源**——deploybench 经 EXTRA overlay/conf 消费，零手写板级件；dram0 溢出 25164B → heap 98304 MP 纪律实测敲定）→ 烧录 + prov 重生成（陈旧 x86 路由修复入树）→ **第二板入 LN 网（CONNECTED 9957）**→ **BV1 C1-C6 全 PASS** → 画像 dnesp32s3b.toml 入目录（owner「自行完成」委托记 + 草稿全文随批呈递供事后 review）→ **双板 LN 双 ACTIVE PASS**（扇出双 confirmed + 暖复位 + 聚合零降级）。③ **实战回填生成器三缺口**：&wifi soc 分派 / PWM 硬依赖面（pwm_led_pin 调用方事实参数）/ 网络内存家族（R1/R2+xtensa 8192+PSRAM 家族）；BV1 C4 probe_cube 直查兜底；deploybench -C 缓存须 CACHE set()（一三二同型坑）。④ **观察项**：全通配查询单回执 quirk（zenoh 域）；双板网络画像 cube 空值歧义。证据 docs/evidence/bv2_first_board_console.txt。**待 owner：① 本笔 review + push；② L 表累积池续作随点向（v4.5.0 平移捆绑/R12/R13/HW-4 P4 引脚采集为候选）。**

- **2026-10-22（一五四） · V0.15.0「新板适配批」全批交付 ✅（owner「我已经完成review，请你继续开发」→ V0.14.0 四提交 + tag fw-v0.14.0 随令推送 + DEC-74 BV2 门③三裁决按建议值过裁）——FIX-2 板级专项根治 + BV2-I 实现收口，P4 板 C1-C6 全链首次全绿**。① **FIX-2 板载插桩破案**（FIX-1 同 playbook：meta flash 真值直读 + 临时插桩 + 决定性复现）：**root cause 三连（同根 WAMR 调用契约）**——appmgr/runtime.c call0() 以 argc=0 调 wasm_runtime_call_wasm，WAMR 契约 argc ≥ param_cell_num，约定签名 app_tick(int ctx) 每 tick 必陷 "invalid argument count 0"（无参 fixture tick 恒过 = sim/bench 全绿、带参 app 必死——V0.4 起存量，首例带参 tick app = P4 探针）；WAMR 实例异常位跨调用存活（一次 trap 毒化后续全部调用）；health_probe 不设指令配额。**故障闭环**：tick 陷 → health_fails 累积 → 3 败健康回退 → meta 翻槽（TS_TEST 构建静默）→ app 线程退出 → APPMGR WDT（noinit 0x00020001）→ 复位；「meta 交替」= 每次 C6 重跑重激活。**修复**（runtime.c 23+/15-）：tick 经 call1 带 ctx（argc=1 ≥ 任意 ≤1 参 cell，无参钳制不扰）+ call1 失败清实例异常 + health_probe 显式配额/带参/清异常；**顺带 agent 抓取面**：post_deploy_check 增 reset_before_capture（单端口会话 reset_and_capture——CH343 两段式关/开竞态 no_verdict 假 FAIL 根治，缺省不变）+1 用例。② **板上闭环**：探针 **ALIVE t=11s 首印** + fail 恒 0 + 零复位零回退 + 槽乒乓按设计 + bench 同固件 P4B PASS + **BV1 C4+C6 PASS（93.3s）= P4 C1-C6 全链首次全绿**。③ **BV2-I ✅（LLD-agent-board-adaptation §2/§3/§4——DEC-74 三裁决落地）**：domain/board_adapt.py 收录板路全链（locate_board → plan_partitions 布局模板族〔**P4 playbook 真锚——测试与在树 overlay 逐偏移对拍**；未知尺寸 fail-closed〕→ 接入件五件套〔overlay/board conf 架构表/prov offset 注记/workorder〕→ c0_preflight 机械预检 → **agent/adapt/<board>/ 工作区〔产物非源码〕**）+ install_profile owner 闸（未批准恒拒零落盘；**BV1 loader 可装载 = clarify 分支 A 同源可绑——工单两端闭环**）+ MCP `board_adapt`（strict，mode=included/schematic）+ 未收录清单五项全 pending-confirm 态（**go_build 恒 False**——原理图无机械判据，人工确认闸如实登记）；测试 +11。④ **入册事实**：meta 双副本乒乓快照纪律（单读 copy0 误判未变）；P4 烧录布局（ROM 自 **0x2000** 简单引导 app；west flash = 单产物 0x2000；**误写 0x0 = boot 循环**——本会话误烧一轮回 erase_region 恢复，ts 分区无损）；twister 并行 configure_file 写共享 WAMR 源树竞态（wamr 套件 error 单跑 PASS——环境域）。⑤ **登记**：DEC-74（LLD-agent-board-adaptation §5 三决策按建议值）+ §11h K 表 V0.15.0（FIX-2 ✅ → BV2-I ✅ → 收口）+ v4.5.0 平移顺延 V0.16.0 候选 + HLD-agent v0.2.4（工具面 +board_adapt）+ README 计数（agent 346/adapt 行）。证据 docs/evidence/fix2_p4_probe_console.txt。**追加四（2026-10-23）：DEC-77 硬件域两项——① C6 stock 重烧任务剔除（owner 确认无问题，双证闭合）；② 轮烧工作流（单 USB 口约束：第二块板可通电驻网，烧录走 USB 轮流窗口、测试全程走 WiFi）——**BV2 真板实战 + 多真机 LN 复验由挂起转可执行**（板身份首烧 flash-id 定；BV1 C1-C3 限 USB 窗口/C4-C6 随时）。**

**追加三（2026-10-23）：DEC-76 渠道裁撤（owner「pi 渠道标记取消，我们永不引入node」）——M1 终态裁撤非 HOLD（DEC-66⑤ 接入面废止）+ Node.js 永不引入 = 项目硬边界（web 案 A 零 Node 升格永久约束）；渠道定格 Terminal/stdio/MCP-HTTP/web 四渠道，harness 槽位留作架构预留；plan v1.151/HLD §1/§7/§9 同步。**

**追加二（2026-10-23）：owner 勘误 = 完成 review 的是 V0.15.0（非 V0.14.0）→ 三笔 + 登记笔随令推送（main + tag fw-v0.15.0）；**DEC-75 版本节奏纪律**：minor（0.X.0）须累积 ~5-8 个 feature 方可收口，issue fix 只走 patch（0.0.X）随修随发，存量版本号不回溯（plan v1.150）。**

**追加（同日）：V0.14.0 推送后远端 CI 实况 = native-build/l5/repo 三绿 + agent-checks 红（dc62682 SOURCES.lock 漂移复发——4f83586 同类第二发：收口笔触源文档但锁未随更，提交消息「sync 全绿」失实已勘误）；修复已随本地 V0.15.0 线（HEAD sync 绿，push 后复绿）；教训升级 = sync 校验升级为 commit 前最后一步。** **待 owner：① 本批两笔（FIX-2 修复笔 + BV2-I/收口笔）review + push；② tag fw-v0.15.0 确认后推；③ 后续候选：v4.5.0 正式版平移（V0.16.0，上游 ~10-26）/ BV2 真板实战（第二块板到位 = 适配流水线首应用）。**

- **更早会话记录（一五三及以前 · 2026-09-19…2026-10-21）**：已归档 `docs/history/agents-status-archive.md`（2026-10-24 仓整理——逐字搬运；AGENTS.md 只保留近三会话）。

## 2. 会话 bootstrap（每次会话固定执行）

1. 读本文件，重点是"当前状态"节；
2. 读 `decisions.md`，确认未裁 Q；
3. 读当前阶段文档（`docs/research/` 或 `design/`）；
4. 长会话上下文被压缩后，一律以文件现状为准续写，不以记忆续写。

## 3. 项目一句话（详见 FOUNDING_PROMPT §0）

**Tessera**：立方体智能 I/O 模块——基于 Zephyr RTOS 的模块化末端输入输出系统。业务逻辑以**可安装、可迁移的 APP** 形态运行（类安卓：APP 与板卡硬件解耦）；输入输出外设**可插拔**；多个立方体可经扩展面**并联为一个逻辑节点**；物理输出具备**安全限制**；配套 **MCP 形态 AI Agent** 完成"需求分析 → 软件设计 → 编程开发 → 模拟测试 → 部署"的完整编程链路。本项目完全由 AI（ZCode）开发，owner 负责裁决与 review。

## 4. 开发流程（摘要；全文见 FOUNDING_PROMPT §2）

- **主线**：research → owner 裁决 → design（规格）→ owner 确认 → impl（实现+测试）→ 阶段退出 review → 下一阶段。
- **阶段产出白名单**：research 只出 `docs/research/*.md` 与 Q 登记；design 只出 `design/` 规格与修订记录；impl 只出规格清单内代码 + 同批测试。**越权产出 = 立即撤回并留痕**。
- **单会话预算**：一个会话交付一个可验证交付单元；超出部分登记待办另起会话。
- **review 门**（必须停下等 owner，不得自裁）：① 一切选型与默认值（先登记 Q）；② 阶段退出（对照 DoD）；③ 公共 API / 文件格式 / 网络协议 / 权限模型变更；④ 安全合同任何改动；⑤ 技术栈变更（须证明阻塞性，附备选对比与迁移成本）。
- **呈递格式（强制，不自包含直接重写）**：背景（现状 + 为何是问题）→ 选项 → 建议 → 影响。
- **决策登记**：`decisions.md`；生命周期 Q-xx → owner 回复 → DEC-xx（附日期与原文）；编号不复用，REJECTED 留档。
- **默认值三问**（写任何常量前自答）：从哪来（Q/推导）？越界会怎样？改动破坏什么？

## 5. 工程纪律（军规十条，违反即流程缺陷）

1. **流程至上**：阶段白名单不越、review 门不闯。
2. **无 Q 不落盘**：未裁决的默认值/选型不得写成"已决定"，不得进代码常量。
3. **文字纪律**：只记录必要内容；必要内容必须**自包含**（现状 + 动因 + 后果三要素齐全），不带会话上下文也能读懂。
4. **编码纪律**：全库文本 UTF-8 无 BOM；批量文本操作显式指定编码；禁用依赖系统代码页的工具。
5. **git 纪律**：每交付单元一提交 + 会话结束兜底提交；里程碑与重大裁决打 tag；失败与回退留痕，禁改写历史。
6. **命名纪律**：跨文档标识符（DEC/Q/M/REQ/模块名/板名）登记于 `docs/names.md`；新造先查碰撞；禁裸单字母作跨文档标识符。
7. **测试同批**：实现与测试同一交付；失败如实报告，禁美化、禁把失败改写为"选择不行动"。
8. **结论落盘**：聊天与记忆不是项目状态；会话结束前把持久结论写入文档/登记册。
9. **顺手重构禁止**：任务外的发现登记不动手，不混入本批交付。
10. **交付即验证**：DoD 对照 + 构建/测试全绿 + lint 通过，才算完成；有缺口如实列出。

## 6. 安全与确定性合同（硬约束；HLD 可细化，不得削弱；v2 · DEC-58 措辞批准 2026-10-13）

1. **三安全态**：每个输出通道（含受控供电）显式声明上电态 / 断链态 / 故障态；无声明不予注册。
2. **写入路径唯一**：一切输出必经保护层校验（限幅 / slew-rate / 限流）后才落驱动；绕过保护层的写入 = 缺陷（须可机械检查）。
3. **断链 fail-safe（部署模式化）**：**被编排的设备**：宿主/网络失联 → 输出进安全态（断链 fail-safe）；**独立运行的设备**：编排通道失联为留痕事件，不改变输出控制权；输入流不因保护而中断（两种模式相同）。部署模式由 provisioning 显式声明，运行时不推断。
4. **看门狗**：超时 → 全输出安全态；每子系统独立喂狗（可定位卡死来源）。
5. **estop 硬件通道**：急停 ISR 直达安全态，**不经协议栈、不经调度排队**；响应时间上界可测；事后补发事件。**清除**：具备本地交互能力的设备以本地清除为主（远程清除可由 provisioning 禁用）；无本地交互能力的设备允许远程清除但须硬令牌确认。清除不解除锁存条件外任何状态、不引发输出。
6. **初始化顺序固定**：任一步失败 → 全系统 fail-safe，不得半启动。
7. **受控供电**（DEC-03）纳入 1–6 同一合同（它是特殊形式的输出）。
8. **并联安全归属**（DEC-02 遗留题）：estop 与保护必须能在**本地设备**独立生效，不依赖逻辑节点内部通信——这是逻辑节点拓扑设计的硬约束。
9. **确定性**：同一输入序列必得同一输出序列（重放测试机械验证）；禁依赖未播种随机、墙钟、容器迭代序。
10. **固件核心不学习**：安全参数、权限模型、输出限值不经运行时自适应修改；APP 权限清单是硬边界，越权访问一律拒绝并留痕。
11. **控制源仲裁**：设备可接受远程编排与本地交互两类控制源。本地交互源激活期间，远程写命令被拒绝；控制权切换本身不产生输出，且全程留痕。estop 硬件通道高于一切控制源（合同 5 不受本条影响）。

## 7. 仓库地图

```text
AGENTS.md            本文件（会话入口；§1 只留近三会话——历史归档 docs/history/）
FOUNDING_PROMPT.md   创始 prompt 原文（K1 起始输入，存档不删）
decisions.md         DEC/Q 登记册（权威裁决记录——仓整理不瘦身、历史不回溯）
docs/project-plan.md 现行开发计划（L 表 V0.16.0 累积池 + 纪律 + 近期修订；历史批次计划归档 docs/history/）
docs/names.md        命名空间登记表（§6 = 2026-10-24 重命名登记册——新旧映射唯一权威）
docs/std/            开发规范套件（testing/versioning/progress/coding/naming）
docs/research/       调研文档（R1-R13）
docs/evidence/       真机验证留痕（README 有索引；历史文件名不回溯）
docs/history/        历史归档（AGENTS 状态日志/旧版计划与修订/历史评审档案——2026-10-24 仓整理）
docs/                其余：dev-environment（环境事实源）/ env-rebuild-checklist（重建总单）/ board-*/netbench 等交付报告 / memory-baseline
design/              规格文档（HLD×2 + LLD-ts-* 固件七模块+公共 + LLD-agent-* Agent 域）
firmware/            Zephyr 工程（app/ module/ tests/〔twister 套件 + bench + netlab + safety_check〕；west 工作区在仓库外）
agent/               MCP server + 模拟器 + TSAP 工具链 + skills + web 渠道 + boards/adapt/demos（PC 侧）
tools/board/         板级联调工具（README 含清单与典型编排；WiFi 凭据经 TS_WIFI_* 环境变量注入不入仓）
tools/env/          自动化安装程序（面向用户：install.sh 标准档/--dev 开发者档 + verify_env.sh——DEC-79）
```

## 8. 子代理纪律

委派子代理时提示词自包含；`AGENTS.md` / `decisions.md` / `design/` 的修改权只在主会话。

## 9. 会话结束检查单

- [ ] 交付单元已提交（git log 可溯）
- [ ] 持久结论已落盘（文档/登记册，而非聊天记录）
- [ ] `docs/names.md` 已登记本会话新标识符
- [ ] 本文件"当前状态"节已更新
- [ ] 如触发 review 门：已停在门内并按呈递格式（背景→选项→建议→影响）呈报 owner
