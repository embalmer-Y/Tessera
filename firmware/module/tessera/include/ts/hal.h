/* SPDX-License-Identifier: Apache-2.0 */
/*
 * ts-hal 公共 API（design/LLD-ts-hal.md）：面向 APP 的板无关外设 API +
 * **权限执行点**（manifest 能力 → 每调用裁决，合同 10）。
 * 输出路径：写类 API 全部收敛到 ts_safety_commit（本模块零直接驱动调用——L5）。
 */
#ifndef TS_HAL_H__
#define TS_HAL_H__

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include <ts/err.h>

#ifdef __cplusplus
extern "C" {
#endif

/* ---- ts_ctx_t（LLD-00 §3.1，DR-10）：调用者不透明上下文 ------------------ */
struct ts_ctx_opaque {
	uint16_t app_id;    /* 分配序号（ts-appmgr 管理） */
	uint16_t _rsv;
};
struct ts_ctx_opaque;
typedef struct ts_ctx_opaque ts_ctx_t;

/* ---- 能力文法 ts_perm_v1（LLD-ts-hal §2）-------------------------------- */

typedef enum {
	TS_PERM_CLASS_GPIO,
	TS_PERM_CLASS_PWM,
	TS_PERM_CLASS_ADC,
	TS_PERM_CLASS_POWER,
	TS_PERM_CLASS_FS,   /* DEC-47⑤：文件系统（ts-fs 能力面，MD1.2e） */
	TS_PERM_CLASS_AV,   /* DEC-47⑤：音视频采集/流通道（ts-av 能力面，MD1.2g） */
	TS_PERM_CLASS_MSG,
	TS_PERM_CLASS_SYS,
	TS_PERM_CLASS_COUNT,
} ts_perm_class_t;

typedef enum {
	TS_PERM_OP_READ,
	TS_PERM_OP_WRITE,
	TS_PERM_OP_SET,
	TS_PERM_OP_LIST,   /* DEC-47⑤：fs 专用（list） */
	TS_PERM_OP_DELETE, /* DEC-47⑤：fs 专用（delete） */
	TS_PERM_OP_COUNT,
} ts_perm_op_t;

/* 实例位图：每 class 最多 32 实例（CONFIG_TS_HAL_MAX_INSTANCES=24 → 够用） */
typedef struct {
	uint32_t bitmap[TS_PERM_CLASS_COUNT][TS_PERM_OP_COUNT];
} ts_perm_table_t;

/** 解析一条能力串（"class:op:instances"）→ 更新表。返回 TS_OK 或 TS_E_PARAM。 */
ts_res_t ts_perm_parse(const char *cap, ts_perm_table_t *table);

/** 裁决：class+op+inst 是否在表内。返回 TS_OK 或 TS_E_PERM（+ 事件发布）。 */
ts_res_t ts_perm_check(ts_ctx_t ctx, ts_perm_class_t cls, ts_perm_op_t op, uint8_t inst);

/** 清零表（加载期用）。 */
void ts_perm_table_init(ts_perm_table_t *table);

/** 绑定 ctx → perm 表（ts-appmgr 加载 APP 时调用；一对一绑定）。 */
ts_res_t ts_hal_bind_context(ts_ctx_t *ctx, uint16_t app_id, const ts_perm_table_t *table);
void ts_hal_unbind_context(ts_ctx_t *ctx);

/* ---- ts-fs 能力面（DEC-47④⑤，MD1.2e）-------------------------------------
 * 路径授权 = manifest fs_paths 前缀白名单（';' 分隔 CSV，经
 * ts_fs_paths_bind 绑定到 ctx）；class 位图只管 op 开关。fail-closed：
 * 未绑定/无前缀匹配 = TS_E_PERM。无句柄（无泄漏面）；V1 = 已挂载 FAT。 */

/** 绑定 fs_paths 白名单（CSV："/SD:/apps;/SD:/tmp"）到 app_id 对应 ctx。
 * 覆盖式（重复绑定 = 替换）；V1 单活跃 APP。 */
ts_res_t ts_fs_paths_bind(uint16_t app_id, const char *csv);

/** ts_ctx_t 形态的绑定入口（appmgr 装载链用）。 */
ts_res_t ts_fs_paths_bind_ctx(ts_ctx_t c, const char *csv);

/** 路径前缀白名单裁决（内部/测试用；含边界：前缀后须 '/' 或恰好等长）。 */
ts_res_t ts_fs_path_allowed(ts_ctx_t c, const char *path);

/** 目录列举：names 以 ';' 连接写入 out（截断到 cap），*out_len = 实际长度。 */
ts_res_t ts_fs_list(ts_ctx_t c, const char *dir, char *out, uint16_t cap, uint16_t *out_len);

/** 读文件 @off：*len 入=容量 出=实际读得。 */
ts_res_t ts_fs_read(ts_ctx_t c, const char *path, uint32_t off, uint8_t *buf, uint16_t *len);

/** 写文件 @off（不存在则创建；无 O_APPEND 语义）。 */
ts_res_t ts_fs_write(ts_ctx_t c, const char *path, uint32_t off, const uint8_t *data, uint16_t len);

/** 删除文件（目录非空 = 拒绝——由 FS 后端语义决定）。 */
ts_res_t ts_fs_delete(ts_ctx_t c, const char *path);

/* ---- ts-av 能力面（DEC-47③⑥，MD1.2g）-------------------------------------
 * 最小采集面：阻塞取一帧到 APP 缓冲；格式/分辨率经 manifest 声明
 * （av_fmt/av_w/av_h）→ ts_av_config_bind 随载绑定，未绑定 = TS_E_STATE
 * fail-closed。采集/发布均为读类（合同 3 输入面——不经安全提交层）。
 * 发布 = ts_av_publish 经 ts-net avq 分片通道（chunk≤1KB/打拍≥4ms/
 * 重试≤5×20ms——DEC-47②）；权限 = av:read:0（DEC-47⑤）。 */

typedef enum {
	TS_AV_FMT_JPEG,   /* DEC-47②：JPEG 优先（OV2640 硬件压缩） */
	TS_AV_FMT_RGB565, /* 演示保底（无压缩，QQVGA ~38KB/帧） */
} ts_av_fmt_t;

ts_res_t ts_av_config_bind(uint16_t app_id, ts_av_fmt_t fmt, uint16_t w, uint16_t h);
ts_res_t ts_av_config_bind_ctx(ts_ctx_t c, ts_av_fmt_t fmt, uint16_t w, uint16_t h);

/** 阻塞取一帧到 buf（≤cap；*len = 实际帧长；帧 > cap = TS_E_RANGE）。 */
ts_res_t ts_av_capture(ts_ctx_t c, uint8_t *buf, uint32_t cap, uint32_t *len);

/** 发布一分片（len ≤ CONFIG_TS_NET_PUBLISH_MAX_BYTES；入队即返回，
 * 满队 TS_E_BUSY 由 APP 稍后重发本分片）。 */
ts_res_t ts_av_publish(ts_ctx_t c, uint32_t frame_id, uint32_t chunk_id,
		       uint32_t n_chunks, const uint8_t *data, uint32_t len);

/* ---- ts_api_v1（APP 可见的全部导入符号，LLD-ts-hal §3）------------------ */

ts_res_t ts_gpio_write(ts_ctx_t c, uint8_t inst, bool v);
ts_res_t ts_gpio_read(ts_ctx_t c, uint8_t inst, bool *out);
ts_res_t ts_pwm_set(ts_ctx_t c, uint8_t inst, uint32_t hz, uint16_t permille);
ts_res_t ts_adc_read(ts_ctx_t c, uint8_t inst, int32_t *mv);
uint64_t ts_time_ms_api(ts_ctx_t c);
ts_res_t ts_log_write(ts_ctx_t c, uint8_t lvl, const char *msg, uint32_t len);

/* ---- 输入采集 input monitor（DR-02；G3 = 单元 F）------------------------- */

/* TS_EVT_INPUT_CHANGED 载荷（单元 F v2：ADC 模拟面——旧 bool 载荷无消费者，
 * pub.c 通用分支不解码；语义 = 传输级"变了"，阈值归 APP）。 */
struct ts_input_evt {
	uint32_t inst;   /* 注册表全局索引（= ts_adc_read 的 inst 域） */
	int32_t old_mv;
	int32_t new_mv;
};

/** 框架侧 ADC 采样（input monitor 观测路径，无权限面——合同 3 观测侧；
 *  APP 侧读值走 ts_adc_read）。未绑定真后端 = 桩 0mV。 */
ts_res_t ts_adc_sample_fw(uint8_t inst, int32_t *mv);

#ifdef CONFIG_TS_TEST
/** 测试注入：input monitor 轮询取注入值（驱动确定性变化序列）。 */
void ts_hal_input_test_inject(uint32_t inst, int32_t mv);
#endif

/* ---- 实例注册（registry.c，ts-periph 调用）------------------------------ */

typedef enum {
	TS_DEV_GPIO_OUT,
	TS_DEV_GPIO_IN,
	TS_DEV_PWM,
	TS_DEV_ADC,
	TS_DEV_POWER,
} ts_dev_kind_t;

typedef struct {
	const char *uid;       /* 稳定逻辑名（命名空间寻址用） */
	ts_dev_kind_t kind;
	uint8_t ts_out_ch_idx; /* TS_DEV_GPIO_OUT/PWM/POWER → ts-safety 通道 uid 哈希映射 */
} ts_hal_dev_desc_t;

ts_res_t ts_hal_register_dev(const ts_hal_dev_desc_t *desc);
size_t ts_hal_dev_count(void);
const ts_hal_dev_desc_t *ts_hal_dev_get(size_t idx);

/* ---- 输入采集 input monitor（DR-02）-------------------------------------- */

/** 启动输入轮询周期项（sysworkq，无独立线程）。 */
ts_res_t ts_hal_input_start(void);

/** 单次采集（input_poll_fn 内部调用 + 测试钩子）。 */
void ts_hal_input_poll_once(void);

/** [boot/board] 真机 ADC 输入后端初始化（板级九；api.c）。
 * 依赖 CONFIG_TS_DRV_ADC=y + zephyr,user 节点（adc-uid + io-channels）；
 * 未启用/缺绑定返回 -ENODEV。输入直读不经保护层（合同 3）。 */
int ts_adc_drv_init(void);

#ifdef __cplusplus
}
#endif

#endif /* TS_HAL_H__ */
