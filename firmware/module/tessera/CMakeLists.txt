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
