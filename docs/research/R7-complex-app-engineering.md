# R7 · 复杂 APP 工程链与资源泛化调研（DEC-56 · R 批②）——Agent 批 + 合同泛化批设计输入

> **日期**：2026-10-13 · **触发**：DEC-56 D4（「APP 复杂度不受结构性预设限制」——四道结构上限全部重开重定）· **消费方**：Agent 批（工程链接入）+ 合同泛化批（资源分级/尺寸门重定）。
> **方法**：web 实抓（wasm-ld/WAMR 官方文档/Emscripten/aider/Wasmtime/Android——来源见 §9）+ 本地事实（现四道上限的代码出处与板级内存账）。
> **结论先行**：① 多文件→单 wasm 有标准链（clang 单命令多文件即可起步，wasi-sdk 为模板先例）；② WAMR 侧大模块无结构性障碍，**fast interp 内存代价 ~2×预编译码**是大 APP 内存账的关键变量；③ 资源放 wasm 内 vs 设备 fs（ts-fs 已有）两档取舍有 Emscripten 先例背书；④ 编辑模型证据支持按文件规模分档；⑤ 分级资源模型建议 = manifest 声明档位 + 构建期账 + 设备能力匹配安装期拒装（Android largeHeap / Wasmtime ResourceLimiter 同型）。

## 1. 现状四道结构上限（重开对象——本地代码事实）

| 上限 | 出处 | 现值 |
|---|---|---|
| wasm 尺寸门 | `tools_tsap/wasm_build.py` 面检查 | ≤16KB（一票拒绝） |
| 装载缓冲 | `TS_APP_LOAD_MAX`（每板裁剪） | deploybench 2048 / 部分板 4096 |
| 槽池 | deploybench 槽池 512KB / SLOT_SIZE 可配 | 单槽 ~128-256KB 级 |
| 内存账 | 每实例 ~150KB（rt[N] 数组 + WAMR 堆 256KB@PSRAM） | S3 PSRAM 8MB（当前用量 <5%） |

## 2. 多文件 C → 单 wasm 工程链（业界标准）

- **最简起步**：`clang --target=wasm32 a.c b.c lib/c.c -Wl,--no-entry -Wl,--export=app_init,... -o app.wasm`——clang 作驱动一条命令编多文件并自动调 wasm-ld（与现单文件链完全同构，仅枚举多文件）。
- **导出组织**：`-Wl,--export=符号`（可重复；符号缺失即报错——**这恰好是我们想要的 fail-closed**：四回调缺一编译即红）；`__attribute__((export_name))` 源内标注为备选。**`--export-all` 不可用**（需 `--no-gc-sections` 且对静态库失效——SO 实证）。
- **静态库**（若工程长大）：须 llvm-ar 打 .a（宿主 ar 不被接受）；归档成员按需拉入。
- **模板先例**：wasi-sdk = `--sysroot` + CMake 工具链文件，普通多文件 CMake 即出单 wasm——Tessera 工作区工程可用「文件清单 + clang 单命令」起步，CMake 化留后续按需。
- **Tessera 落点建议**：交付物仍是**单 wasm**（TSAP 容器 DEC-21 不变）；工程组织 = 工作区多 .c/.h + 编译步骤聚合（文件清单由创作循环维护，白名单面检查平移到聚合产物上）。

## 3. WAMR 大模块事实（内存账关键变量）

- 线性内存页 64KB：数据段 + 辅助栈 +（可选）堆同居；**app heap 是实例化时另设的独立堆**（module_malloc 落点）——官方建议导出 malloc/free 让 libc 堆接管并裁掉 app heap（省一份）。现 TSAP manifest `heap_kb` 字段语义与此对齐。
- 定容 flags：`-Wl,--initial-memory/--max-memory`、`-z stack-size`——**大 APP 的内存上限在链接期钉死**（manifest 声明 → 编译 flags 传递，三方一致的既有纪律平移）。
- 运行模式代价：**fast interp ≈ 2×内存存预编译码**（vs classic interp）——大 APP（数百 KB）下这是显著项；AOT（wamrc 预编译）"接近原生 + 快启动 + 小足迹"，DEC-25 已留作构建期选项——大 APP 档位可能触发 AOT 提前复评。
- x86-64 边界检查走硬件 mmap；**嵌入式（xtensa）为软件检查——内存账必须实算**（现每板内存预算表纪律维持，数值随档位扩展）。
- 数百 KB~MB 模块加载时间：官方基准（PolyBench/CoreMark 等）存在，加载时间数字未查到——**Agent 批拿真实大 APP 实测补**（现有 APP 冷启动 4.8ms 基线在 board-bench-01）。

## 4. 体积构成与资源放置（wasm 内 vs 设备 fs）

- 体感标尺：minimp3 编译产物 ~34KB（压缩 ~20KB）；cJSON 低两位数 KB——**"复杂逻辑"与"大数据资源"是两种体积**：前者可控，后者应外置。
- 减体积三板斧：-Oz / nostdlib / `--strip-all`（WAMR 官方建议——现链已两项，strip 待评估〔双编译一致门不受影响〕）。
- **资源放置两档**（Emscripten 先例：embed-file 打进 wasm「更高效免下载」vs preload-file 旁挂「可分开托管」）：Tessera 对应 = **wasm 内嵌 vs ts-fs 读取**（fs_paths 白名单 + SD 卡先例 dsdbench n=68 实测）——字体/点阵/大表类资源走 fs、逻辑留 wasm，是内存账友好的正解；manifest 资源声明格式随合同泛化批定。

## 5. 编辑模型（R3 重定的证据）

- aider 分级：whole / diff（SEARCH/REPLACE）/ udiff；GPT-4 Turbo 类模型用 diff 惯写省略号（lazy），udiff 懒度降 ~3×；官方建议**少喂大文件**。
- Claude 系 = str_replace：old_str 全文唯一否则报错、先 view 再改。
- 共识：**整文件最稳但 token 贵；锚点替换省 token 但依赖唯一锚**。
- **Tessera 落点**（与 R6 呈递一致）：工作区文件编辑 = 唯一串替换式；小文件（阈值建议 ~200 行，实测调）维持整文件再生；交付管线四道门不受编辑模型影响。

## 6. 分级资源模型（档位设计输入）

- 先例一：Android 双档 heap（`heapgrowthlimit` 常规 vs `largeHeap=true` 大档，运行时 getMemoryClass 查询）——**声明式档位 + 运行时可查**。
- 先例二：Wasmtime `ResourceLimiter` 按 store 限线性内存/表增长 + fuel 确定性计费——**资源上限是实例属性不是全局常量**。
- **Tessera 建议形态**（Q-39 呈递主体）：manifest 声明 `tier: small | large`（或直接声明 needs：max_memory/stack/资源文件清单）→ 固件按档位给配额（槽尺寸/线性内存上限/指令预算档/装载缓冲档）→ **安装期设备能力匹配**（设备资源不够 = 拒装，非运行期 OOM）→ get-info 自报设备档位（异构设备生态的基础，DEC-56 形态不限的配套）。数值（small/large 的具体 KB）**待 Agent 批真实大 APP 实测定**。

## 7. 测试与调试（配套）

- wabt 面：`wasm2wat --generate-names`（可读反汇编）、`wasm-objdump -h/-x/-d`（段/符号/反汇编——面检查器交叉验证工具）、wasm-strip。DWARF 段可源级调试（Chrome DevTools 先例；WAMR 侧带 DWARF 调试另有开关——大 APP 批可评估）。
- 宿主单测先例 wasm-bindgen-test 绑定 JS 宿主——**不适用**；native_sim 重放（虚拟时钟 + golden + 判据行）仍是对口做法，大 APP 的 sim 场景 = 多文件工程编译产物照常进 replay 链（现有 test_90 先例）。

## 8. 呈递（Q-39 · 合同泛化批设计决策——随本文登记 decisions.md）

1. **工程链**：建议 = 工作区多文件 + clang 单命令聚合（wasi-sdk 模板备用），交付单 wasm 不变。
2. **档位模型**：建议 = manifest 声明 tier（small/large 起步）+ 设备能力匹配安装期拒装 + get-info 自报档位；数值 Agent 批实测定。
3. **资源放置**：建议 = 大资源外置 ts-fs（fs_paths 白名单扩展资源语义），wasm 内嵌仅限小常量。
4. **内存账**：建议 = initial/max-memory 链接期钉死（manifest 三方一致纪律平移）；fast interp 2× 预编译码代价入账；AOT 复评挂 large 档。
5. **尺寸门**：建议 = 16KB 单门改为按档位双门（small 维持现值/large 新值实测定）——**门不撤，只分档**。

## 9. 来源

- wasm-ld（lld.llvm.org/WebAssembly.html）/ wasi-sdk（github.com/WebAssembly/wasi-sdk）/ wasm-ld export-all 与静态库（SO 79234792）
- WAMR 官方：memory_tune / running-modes / performance-benchmark（wamr.gitbook.io）
- minimp3（github.com/lieff/minimp3）；Emscripten packaging-files
- aider edit-formats / unified-diffs；fabianhertwig.com 编码助手编辑机制对比
- Android heap 双档（SO 5350465）；Wasmtime interrupting-wasm + Config（docs.rs）
- wabt（github.com/webassembly/wabt）；Chrome DevTools wasm 调试；wasm-bindgen-test
- 本地：wasm_build.py（现门值）/ deploybench 槽池配置 / board-bench-01（冷启动 4.8ms 基线）/ HLD §4.6 内存预算表
