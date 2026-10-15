# SPDX-License-Identifier: Apache-2.0
# atkbench（K1）：ATK DNESP32-S3B V1.1 bring-up + 第二 cube 部署链载体
# （K 批主载体：ES8311 音频 / 信任链 E2E / SD 资源推送 / 多真机 LN）。
# 凭证与路由地址经 cmake 变量注入（本地脚本传入，不入仓库——deploybench 同纪律）：
#   west build ... -- -DATKBENCH_WIFI_SSID=... -DATKBENCH_WIFI_PASSWORD=... \
#                    -DATKBENCH_ROUTER='"tcp/192.168.2.91:9955"'
cmake_minimum_required(VERSION 3.20.5)
find_package(Zephyr REQUIRED HINTS $ENV{ZEPHYR_BASE})
project(atkbench)

target_compile_definitions(app PRIVATE
  ATKBENCH_WIFI_SSID="${ATKBENCH_WIFI_SSID}"
  ATKBENCH_WIFI_PASSWORD="${ATKBENCH_WIFI_PASSWORD}"
  ATKBENCH_ROUTER="${ATKBENCH_ROUTER}")

target_sources(app PRIVATE src/main.c)
