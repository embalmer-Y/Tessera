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
