# SPDX-License-Identifier: Apache-2.0
# Tessera framework module root.
# 子系统按 design/LLD-* 加入：M1 = ts-core + ts-safety；M2/M3 追加 hal/appmgr/
# net/power/periph/store（各 LLD）。
zephyr_include_directories(${CMAKE_CURRENT_SOURCE_DIR}/include)

zephyr_library()

zephyr_library_sources_ifdef(CONFIG_TS_CORE
  src/core/time.c
  src/core/events.c
  src/core/wdt.c
  src/core/boot.c
)

zephyr_library_sources_ifdef(CONFIG_TS_SAFETY
  src/safety/channel.c
  src/safety/commit.c
  src/safety/force.c
  src/safety/driver_dispatch.c
)

zephyr_library_sources_ifdef(CONFIG_TS_STORE
  src/store/part.c
  src/store/meta.c
  src/store/prov.c
  src/store/noinit.c
  src/store/slot.c
  src/store/sha256.c
)

zephyr_library_sources_ifdef(CONFIG_TS_TEST
  src/store/prov_test.c
)

zephyr_library_sources_ifdef(CONFIG_TS_HAL
  src/hal/perm.c
  src/hal/api.c
  src/hal/input.c
)

zephyr_library_sources_ifdef(CONFIG_TS_APPMGR
  src/appmgr/pkg.c
  src/appmgr/slot.c
)

zephyr_library_sources_ifdef(CONFIG_TS_NET
  src/net/keyspace.c
  src/net/pubq.c
  src/net/session.c
  src/net/linkmon.c
  src/net/cbor_min.c
  src/net/cmd.c
  src/net/lease.c
  src/net/pub.c
  src/net/init.c
)

zephyr_library_sources_ifdef(CONFIG_TS_NET_ZENOH
  src/net/zenoh.c
)

zephyr_library_sources_ifdef(CONFIG_TS_POWER
  src/power/slots.c
  src/power/budget.c
)

zephyr_library_sources_ifdef(CONFIG_TS_PERIPH
  src/periph/desc.c
  src/periph/hotplug.c
)

# ---- WAMR 运行时（M2b.2a 环境批；CONFIG_TS_APP_WAMR 门控）------------------
# DEC-17（WAMR）/ DEC-25（fast 解释器 + WASI 全关 + AOT 不入固件构建）/
# DEC-31（线程/共享内存特性编译期不启用）。源码根经环境变量 TS_WAMR_DIR 注入
# （本地 = ~/project/deps/wamr，CI 检出步骤注入；仓库不含三方源码——与
# zenoh-pico 同纪律）。板级目标随移植批映射（ESP32-S3 = XTENSA）。
if(CONFIG_TS_APP_WAMR)
  if(NOT DEFINED ENV{TS_WAMR_DIR})
    message(FATAL_ERROR
      "TS_WAMR_DIR not set (WAMR source root; local: ~/project/deps/wamr, CI: checkout step)")
  endif()
  set(WAMR_BUILD_PLATFORM "zephyr")
  set(WAMR_BUILD_TARGET "X86_32")     # native_sim 32 位基线
  set(WAMR_BUILD_INTERP 1)
  set(WAMR_BUILD_FAST_INTERP 1)       # DEC-25：fast 解释器
  set(WAMR_BUILD_AOT 0)               # DEC-25：AOT = Agent 构建期选项，不入固件
  set(WAMR_BUILD_JIT 0)
  set(WAMR_BUILD_LIBC_BUILTIN 1)
  set(WAMR_BUILD_LIBC_WASI 0)         # DEC-25：WASI 全关
  set(WAMR_BUILD_MULTI_MODULE 0)
  set(WAMR_BUILD_SHARED_MEMORY 0)     # DEC-31：共享内存不启用
  set(WAMR_BUILD_LIB_PTHREAD 0)       # DEC-31：APP 自建线程编译期禁用
  # 通用 C 版 invokeNative：ia32 汇编缺 .note.GNU-stack（可执行栈警告被
  # Zephyr --fatal-warnings 升级为链接错误）；C 版跨板一致且零补丁。
  set(WAMR_BUILD_INVOKE_NATIVE_GENERAL 1)
  set(WAMR_BUILD_GLOBAL_HEAP_POOL 1)  # 池模式（PSRAM 分层纪律，DEC-27）
  set(WAMR_BUILD_GLOBAL_HEAP_SIZE ${CONFIG_TS_APP_WAMR_HEAP})
  set(WAMR_ROOT_DIR $ENV{TS_WAMR_DIR})
  include($ENV{TS_WAMR_DIR}/build-scripts/runtime_lib.cmake)
  # 三方源码独立成库并 -w：钉版上游不裁剪告警（ems_gc.c 的 GB 常量与
  # Zephyr util.h 单位宏撞名等）——零上游补丁纪律（DR-22 教训同源）。
  zephyr_library_named(tessera_wamr)
  zephyr_library_sources(${WAMR_RUNTIME_LIB_SOURCE})
  zephyr_library_sources(src/appmgr/wamr_compat.c)
  zephyr_library_compile_options(-w)
  # 消费面（app/测试）include 传播：runtime_lib.cmake 内部为目录级
  # include_directories（仅本模块编译域可见）——Zephyr 下消费方须经
  # zephyr_include_directories 取到 wasm_export.h。
  zephyr_include_directories($ENV{TS_WAMR_DIR}/core/iwasm/include)
endif()
