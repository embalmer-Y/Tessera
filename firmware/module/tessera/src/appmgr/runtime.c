/* SPDX-License-Identifier: Apache-2.0 */
/* APP 运行时宿主（LLD-ts-appmgr §4/§5；DEC-43 方案 A：每 APP 一个框架线程）。
 * V1 单活跃 APP（与 slot 单活跃语义一致；同时加载上限 4 = DEC-27，多实例
 * 随真机多 APP 支持启用）。
 * 事件串行化（DR-14）：tick/app_evt 均在 APP 线程内执行；外部事件入
 * mailbox（深度 DEC-27 #15: 8，满丢最旧 + 计数）。
 * 停止语义（DR-14）：停投递 → join（2s 超时强杀，DEC-27 #15）→ 回收
 * （WAMR 对象/ctx/邮箱）；强杀不触框架喂狗（合同 4 独立喂狗源）。
 * 健康探针：health_ping 周期〔DEC-27：1000ms〕，连续〔DEC-27：3〕次失败
 * （异常或非零返回）→ ts_appmgr_health_fail()（回滚状态机入口）并自停。
 * WAMR 生命周期：进程级单次 init/注册（平台层 init/destroy 不对称——
 * wamrdemo 实证；不重复销毁）。 */
#include <string.h>
#include <zephyr/kernel.h>
#include <zephyr/sys/printk.h>
#include <zephyr/sys/atomic.h>
#include <ts/appmgr.h>
#include <ts/core.h> /* ts_time_ms：合同 9 时基（L5 禁 uptime） */
#include <ts/hal.h>
#include <wasm_export.h>
#if defined(CONFIG_TS_APP_PSRAM_HEAP)
#include <zephyr/multi_heap/shared_multi_heap.h>
#endif

#define APP_STOP_JOIN_MS 2000 /* DEC-27 #15 */
#define APP_WASM_STACK   4096 /* wasm 应用栈（manifest.mem.stack 上限 8KB 前
			       * 的 V1 缺省；随 manifest 实装读入） */
#define APP_WASM_HEAP    8192

extern bool ts_app_natives_register(void);

struct ts_app_rt {
	bool used;
	atomic_t running;
	uint16_t app_id;
	ts_ctx_t ctx; /* hal 绑定（表已拷贝进绑定层，栈上表即可） */
	wasm_module_t mod;
	wasm_module_inst_t inst;
	wasm_exec_env_t env;
	wasm_function_inst_t fn_init, fn_tick, fn_evt, fn_health;
	struct k_thread thread;
	/* 观测计数（stats） */
	uint32_t evt_seen, tick_count, health_fails, mb_dropped, init_res;
	int32_t last_evt;
	bool health_failed;
};

static struct ts_app_rt rt;
static K_THREAD_STACK_DEFINE(app_stack, CONFIG_TS_APP_THREAD_STACK);
K_MSGQ_DEFINE(app_mb, sizeof(uint32_t), CONFIG_TS_APP_MBOX_DEPTH, 4);

/* 模块缓存（WAMR 平台怪癖规避，零上游补丁）：同进程内 unload→reload
 * 与 init→destroy→init 均实测失败（framework.wamr/wamrdemo 排障留痕，
 * dev-env §5-12）——V1 单 APP 语义下模块进程级复用：同字节流（指针+长度）
 * 直接复用，stop 不卸载；换包需重启（升级路径随板级/WAMR 修复版再议）。 */
static struct {
	const uint8_t *src;
	uint32_t len;
	wasm_module_t mod;
	bool loaded;
} mod_cache;

ts_ctx_t ts_app_rt_ctx(struct ts_app_rt *r)
{
	return r->ctx;
}

uint16_t ts_app_rt_id(struct ts_app_rt *r)
{
	return r->app_id;
}

/* ---- APP 线程主循环 -------------------------------------------------------- */

static bool call0(struct ts_app_rt *r, wasm_function_inst_t fn)
{
	uint32_t argv[1] = {0};

	/* DEC-48③（Q-28③A）：每次调用前设指令配额——超限抛
	 * "instruction limit exceeded" → 返回 false → 既有健康失败/回滚路径
	 * （无 abort、无持锁死锁面）。tick/evt/health 共用 TICK 预算。 */
	wasm_runtime_set_instruction_count_limit(r->env, CONFIG_TS_APP_INSTR_TICK);
	return wasm_runtime_call_wasm(r->env, fn, 0, argv);
}

static bool call1(struct ts_app_rt *r, wasm_function_inst_t fn, uint32_t arg,
		  uint32_t *ret)
{
	uint32_t argv[1] = {arg};

	wasm_runtime_set_instruction_count_limit(r->env, CONFIG_TS_APP_INSTR_TICK);
	if (!wasm_runtime_call_wasm(r->env, fn, 1, argv)) {
		return false;
	}
	if (ret != NULL) {
		*ret = argv[0];
	}
	return true;
}

static void health_probe(struct ts_app_rt *r)
{
	uint32_t ret = 0;

	/* 健康语义：调用成功且返回 0（异常或非零 = 失败一次） */
	if (!wasm_runtime_call_wasm(r->env, r->fn_health, 0, &ret) || ret != 0) {
		r->health_fails++;
		if (r->health_fails >= CONFIG_TS_APP_HEALTH_FAILS) {
			r->health_failed = true;
			atomic_set(&r->running, 0);
			(void)ts_appmgr_health_fail(); /* 回滚状态机入口 */
		}
		return;
	}
	r->health_fails = 0;
}

static void app_thread_entry(void *p1, void *p2, void *p3)
{
	ARG_UNUSED(p1);
	ARG_UNUSED(p2);
	ARG_UNUSED(p3);
	struct ts_app_rt *r = &rt;

	ts_wdt_feed(TS_WDT_APPMGR); /* DEC-48②：线程入口激活喂狗源 */
	if (r->fn_init != NULL) {
		uint32_t ret = 0;

		wasm_runtime_set_instruction_count_limit(r->env,
							 CONFIG_TS_APP_INSTR_INIT);
		if (!call1(r, r->fn_init, r->app_id, &ret)) {
			/* 失败可见性（军规 7 如实上报）：WAMR 异常文本留痕 */
			const char *exc = wasm_runtime_get_exception(r->inst);

			if (exc != NULL) {
				printk("[appmgr] app_init exception: %s\n", exc);
			}
			r->init_res = (uint32_t)TS_E_IO; /* init 异常 = 启动失败 */
			atomic_set(&r->running, 0);
			return;
		}
		r->init_res = ret;
	}
	uint32_t last_tick = (uint32_t)ts_time_ms();
	uint32_t last_health = last_tick;
	uint32_t v;

	while (atomic_get(&r->running) != 0) {
		ts_wdt_feed(TS_WDT_APPMGR); /* DEC-48②：主循环喂狗（≤20ms 轮询上界） */
		if (k_msgq_get(&app_mb, &v, K_MSEC(20)) == 0) {
			r->evt_seen++;
			r->last_evt = (int32_t)v;
			if (r->fn_evt != NULL && !call1(r, r->fn_evt, v, NULL)) {
				r->health_fails++; /* evt 异常计入健康 */
			}
		}
		uint32_t now = (uint32_t)ts_time_ms();

		if (r->fn_tick != NULL &&
		    (now - last_tick) >= CONFIG_TS_APP_TICK_MS) {
			last_tick = now;
			r->tick_count++;
			if (!call0(r, r->fn_tick)) {
				r->health_fails++;
			}
		}
		if ((now - last_health) >= CONFIG_TS_APP_HEALTH_MS) {
			last_health = now;
			health_probe(r);
		}
	}
}

/* ---- 公共 API -------------------------------------------------------------- */

/* G3（单元 F）：input monitor → APP mailbox 路由。
 * 订阅 TS_EVT_INPUT_CHANGED（一次性——evt 总线无退订 API，cb 内按
 * rt.used/running 门控）；payload 编码进 32 位 mailbox 槽：
 * (inst << 16) | (new_mv & 0xFFFF)——旧值/阈值语义归 APP。
 * 回调在发布者上下文（sysworkq 输入轮询）执行；k_msgq_put(K_NO_WAIT)
 * 线程安全，满 = 丢最旧 + 计数（DR-14）。 */
static void input_evt_cb(const ts_evt_t *evt, void *user)
{
	ARG_UNUSED(user);
	if (!rt.used || atomic_get(&rt.running) == 0) {
		return;
	}
	if (evt->data == NULL || evt->len < sizeof(struct ts_input_evt)) {
		return;
	}
	const struct ts_input_evt *p = evt->data;
	const uint32_t payload = ((uint32_t)(p->inst & 0xFFFF) << 16) |
				 ((uint32_t)p->new_mv & 0xFFFF);
	(void)ts_appmgr_app_evt(payload);
}

static void input_route_subscribe(void)
{
	static bool done;

	if (!done && ts_evt_subscribe(TS_EVT_INPUT_CHANGED, input_evt_cb,
				      NULL) == TS_OK) {
		done = true;
	}
}

#ifdef CONFIG_XTENSA
/* DAV1 诊断（B2 后续批）：APPMGR 软看门狗逾期警告时 dump 冻结线程状态与
 * 栈内文本域字（返回地址候选——离线 addr2line 定位冻结点；av 流 APP 线程
 * 冻结 3/3 复现的归因证据链；一次 dump 防洪泛）。Xtensa 非用户态无保存
 * SP 字段（callee_saved 为哑结构）——全栈扫描法（公开 API）。 */
static void wdt_warn_diag_cb(const ts_evt_t *e, void *user)
{
	ARG_UNUSED(user);
	if (e->data == NULL || e->len < sizeof(ts_wdt_warn_evt_t)) {
		return;
	}
	const ts_wdt_warn_evt_t *w = e->data;

	if (w->src != TS_WDT_APPMGR || !rt.used) {
		return;
	}
	static bool dumped;

	if (dumped) {
		return;
	}
	dumped = true;
	char sb[48];
	k_tid_t cur = k_current_get();
	const char *cur_name = k_thread_name_get(cur);

	printk("[appmgr] WDT-WARN diag: APP state=%s prio=%d | cur=%s cur_prio=%d\n",
	       k_thread_state_str((k_tid_t)&rt.thread, sb, sizeof(sb)),
	       (int)rt.thread.base.prio,
	       cur_name != NULL ? cur_name : "?",
	       (int)cur->base.prio);
	/* 文本域字扫描（esp32s3：IRAM 0x40xxxxxx / IROM 0x42xxxxxx）——
	 * 返回地址候选按栈顶近端优先输出（最近调用层在前），上限 40 条。 */
	const uint32_t *st = (const uint32_t *)rt.thread.stack_info.start;
	const size_t words = rt.thread.stack_info.size / sizeof(uint32_t);
	int shown = 0;

	for (size_t i = words; i > 0 && shown < 40; i--) {
		uint32_t v = st[i - 1];

		if ((v & 0xFF000000U) == 0x40000000U ||
		    (v & 0xFF000000U) == 0x42000000U) {
			printk("[appmgr] wf[%02d] +%04x %08x\n", shown++,
			       (unsigned)((words - i) * 4U), v);
		}
	}
}
#endif

ts_res_t ts_appmgr_app_start(uint16_t app_id, const uint8_t *wasm,
			     uint32_t wasm_len, const char *caps)
{
	char err[128];

	if (wasm == NULL || wasm_len == 0 || caps == NULL) {
		return TS_E_PARAM;
	}
	if (rt.used) {
		return TS_E_STATE;
	}
	/* WAMR 进程级初始化 + natives 全局注册（一次）。
	 * 实例堆 = 显式池（DEC-27 #10 池模式；板级六修正：WAMR-2.4.5 的
	 * WASM_ENABLE_GLOBAL_HEAP_POOL 旗标对 runtime 路径已无消费者——
	 * wasm_runtime_init() 实为系统分配器，池语义须经 wasm_runtime_full_init
	 * 显式注入）：
	 *  - PSRAM 配置（CONFIG_TS_APP_PSRAM_HEAP，HLD §4.6 分层纪律：仅 APP
	 *    沙箱内存可入外部 RAM）= 共享多堆 SMH_REG_ATTR_EXTERNAL 分配
	 *   （esp32s3 PSRAM 注册面，官方机制）；
	 *  - 其余（native_sim/CI/未挂 PSRAM 板）= 内部 SRAM 静态池。 */
	static bool wamr_up;

	if (!wamr_up) {
#if defined(CONFIG_TS_APP_PSRAM_HEAP)
		static void *wamr_heap_buf;

		if (wamr_heap_buf == NULL) {
			wamr_heap_buf = shared_multi_heap_alloc(
				SMH_REG_ATTR_EXTERNAL, CONFIG_TS_APP_WAMR_HEAP);
		}
		if (wamr_heap_buf == NULL) {
			printk("[appmgr] wamr psram heap alloc %u failed\n",
			       CONFIG_TS_APP_WAMR_HEAP);
			return TS_E_NOMEM;
		}
#else
		static uint8_t wamr_heap_buf[CONFIG_TS_APP_WAMR_HEAP] __aligned(8);
#endif
		RuntimeInitArgs args = {0};

		args.mem_alloc_type = Alloc_With_Pool;
		args.mem_alloc_option.pool.heap_buf = wamr_heap_buf;
		args.mem_alloc_option.pool.heap_size = CONFIG_TS_APP_WAMR_HEAP;
		if (!wasm_runtime_full_init(&args)) {
#if defined(CONFIG_TS_APP_PSRAM_HEAP)
			shared_multi_heap_free(wamr_heap_buf);
			wamr_heap_buf = NULL;
#endif
			return TS_E_IO;
		}
		printk("[appmgr] wamr pool heap: buf=%p size=%u (%s)\n",
		       args.mem_alloc_option.pool.heap_buf,
		       CONFIG_TS_APP_WAMR_HEAP,
		       IS_ENABLED(CONFIG_TS_APP_PSRAM_HEAP) ? "psram/smh" : "sram/static");
		wamr_up = true;
	}
	if (!ts_app_natives_register()) {
		return TS_E_IO;
	}
	/* 权限表 → hal ctx 绑定（表拷贝入绑定层；防伪造边界）。
	 * caps 可为 ';' 分隔多条（boot 组合 manifest caps 数组；ts_perm_parse
	 * 语义 = 位图或合并） */
	ts_perm_table_t table;

	ts_perm_table_init(&table);
	if (caps[0] != '\0') {
		const char *p = caps;

		while (*p != '\0') {
			const char *seg = strchr(p, ';');
			size_t sl = (seg != NULL) ? (size_t)(seg - p) : strlen(p);
			char one[48];

			if (sl == 0 || sl >= sizeof(one)) {
				return TS_E_PARAM;
			}
			memcpy(one, p, sl);
			one[sl] = '\0';
			if (ts_perm_parse(one, &table) != TS_OK) {
				return TS_E_PARAM;
			}
			if (seg == NULL) {
				break; /* 末段（无 ';'）——防越过 NUL 越界 */
			}
			p = seg + 1;
		}
	}
	memset(&rt, 0, sizeof(rt));
	rt.app_id = app_id;
	if (ts_hal_bind_context(&rt.ctx, app_id, &table) != TS_OK) {
		return TS_E_NOMEM;
	}
	rt.mod = NULL;
	if (mod_cache.loaded) {
		if (mod_cache.len == wasm_len &&
		    memcmp(mod_cache.src, wasm, wasm_len) == 0) {
			rt.mod = mod_cache.mod; /* 内容一致 → 复用（见 mod_cache 注释：
						 * boot 缓冲与测试夹具为同 wasm 两份拷贝） */
		} else {
#ifndef CONFIG_TS_TEST
			return TS_E_STATE; /* 进程内换包不支持（怪癖规避——重启路径） */
#else
			/* TEST 构建：进程内换包放行（多夹具单测形态——sim 内存可
			 * 承受旧模块驻留；生产路径换包恒经重启，不走此分支）。 */
			rt.mod = wasm_runtime_load((uint8_t *)wasm, wasm_len,
						   err, sizeof(err));
			if (rt.mod == NULL) {
				ts_hal_unbind_context(&rt.ctx);
				return TS_E_IO;
			}
			mod_cache.src = wasm;
			mod_cache.len = wasm_len;
			mod_cache.mod = rt.mod;
#endif
		}
	} else {
		rt.mod = wasm_runtime_load((uint8_t *)wasm, wasm_len, err, sizeof(err));
		if (rt.mod == NULL) {
			printk("[appmgr] load fail: %s (len=%u)\n", err, wasm_len);
			ts_hal_unbind_context(&rt.ctx);
			return TS_E_IO;
		}
		mod_cache.src = wasm;
		mod_cache.len = wasm_len;
		mod_cache.mod = rt.mod;
		mod_cache.loaded = true;
	}
	rt.inst = wasm_runtime_instantiate(rt.mod, APP_WASM_STACK, APP_WASM_HEAP,
					   err, sizeof(err));
	if (rt.inst == NULL) {
		printk("[appmgr] inst fail: %s\n", err);
		/* 模块进程级持有（mod_cache 怪癖规避——不 unload） */
		ts_hal_unbind_context(&rt.ctx);
		return TS_E_IO;
	}
	rt.env = wasm_runtime_create_exec_env(rt.inst, APP_WASM_STACK);
	if (rt.env == NULL) {
		wasm_runtime_deinstantiate(rt.inst);
		/* 模块进程级持有（mod_cache 怪癖规避——不 unload） */
		ts_hal_unbind_context(&rt.ctx);
		return TS_E_NOMEM;
	}
	wasm_runtime_set_user_data(rt.env, &rt);

	rt.fn_health = wasm_runtime_lookup_function(rt.inst, "health_ping");
	if (rt.fn_health == NULL) {
		/* manifest v1 必选导出（缺 = 包非法） */
		wasm_runtime_destroy_exec_env(rt.env);
		wasm_runtime_deinstantiate(rt.inst);
		/* 模块进程级持有（mod_cache 怪癖规避——不 unload） */
		ts_hal_unbind_context(&rt.ctx);
		return TS_E_PARAM;
	}
	rt.fn_init = wasm_runtime_lookup_function(rt.inst, "app_init");
	rt.fn_tick = wasm_runtime_lookup_function(rt.inst, "app_tick");
	rt.fn_evt = wasm_runtime_lookup_function(rt.inst, "app_evt");

	k_msgq_purge(&app_mb);
	atomic_set(&rt.running, 1);
	rt.used = true;
	input_route_subscribe(); /* G3（单元 F）：INPUT_CHANGED → APP mailbox */
#ifdef CONFIG_XTENSA
	(void)ts_evt_subscribe(TS_EVT_WDT_WARN, wdt_warn_diag_cb, NULL);
#endif
	k_tid_t th = k_thread_create(&rt.thread, app_stack,
				     K_THREAD_STACK_SIZEOF(app_stack),
				     app_thread_entry, NULL, NULL, NULL,
				     CONFIG_TS_APP_THREAD_PRIORITY, 0,
				     K_NO_WAIT);
	if (th == NULL) {
		rt.used = false;
		atomic_set(&rt.running, 0);
		wasm_runtime_destroy_exec_env(rt.env);
		wasm_runtime_deinstantiate(rt.inst);
		/* 模块进程级持有（mod_cache 怪癖规避——不 unload） */
		ts_hal_unbind_context(&rt.ctx);
		return TS_E_NOMEM;
	}
	return TS_OK;
}

ts_res_t ts_appmgr_app_stop(void)
{
	if (!rt.used) {
		return TS_E_STATE;
	}
	atomic_set(&rt.running, 0); /* 停止投递；线程排空 mailbox 后自退 */
	if (k_thread_join(&rt.thread, K_MSEC(APP_STOP_JOIN_MS)) != 0) {
		/* IR2-06 根治（单元 F）：join 超时 = 线程卡在不可中断点（native
		 * 阻塞/持锁段）——**不 k_thread_abort**（在持锁点截断 = k_mutex
		 * 无 owner-death 回收 → 全输出写路径永久死锁）。改为弃管升级：
		 * 线程留在原地（不再喂 TS_WDT_APPMGR）→ 软看门狗逾期判定 →
		 * system_fail（noinit 留痕归因）→ task_wdt 复位闭环（DEC-48 分
		 * 层防线）。运行时资源（实例/env/rt.used）不回收——重启即净；
		 * 如实登记（返回 E_TIMEOUT，调用方按健康失败/回滚语义处置）。 */
		printk("[appmgr] app_stop: thread stuck — abandon to WDT escalation\n");
		return TS_E_TIMEOUT;
	}
	wasm_runtime_destroy_exec_env(rt.env);
	wasm_runtime_deinstantiate(rt.inst);
	/* 模块进程级持有（mod_cache 怪癖规避——不 unload） */
	ts_hal_unbind_context(&rt.ctx);
	ts_wdt_deactivate(TS_WDT_APPMGR); /* 单元 F：停后无人喂 = 预期态 */
	k_msgq_purge(&app_mb);
	rt.used = false;
	return TS_OK;
}

ts_res_t ts_appmgr_app_evt(uint32_t payload)
{
	if (!rt.used || atomic_get(&rt.running) == 0) {
		return TS_E_STATE;
	}
	if (k_msgq_put(&app_mb, &payload, K_NO_WAIT) != 0) {
		uint32_t drop;

		(void)k_msgq_get(&app_mb, &drop, K_NO_WAIT); /* 满丢最旧（DR-14） */
		rt.mb_dropped++;
		(void)k_msgq_put(&app_mb, &payload, K_NO_WAIT);
	}
	return TS_OK;
}

bool ts_appmgr_app_running(void)
{
	return rt.used && atomic_get(&rt.running) != 0;
}

void ts_appmgr_app_stats(struct ts_app_rt_stats *out)
{
	if (out == NULL) {
		return;
	}
	memset(out, 0, sizeof(*out));
	out->evt_seen = rt.evt_seen;
	out->tick_count = rt.tick_count;
	out->health_fails = rt.health_fails;
	out->mb_dropped = rt.mb_dropped;
	out->init_res = rt.init_res;
	out->last_evt = rt.last_evt;
	out->running = ts_appmgr_app_running();
	out->health_failed = rt.health_failed;
}

#ifdef CONFIG_TS_TEST
void ts_appmgr_app_test_reset(void)
{
	if (rt.used) {
		(void)ts_appmgr_app_stop();
	}
	memset(&rt, 0, sizeof(rt));
	k_msgq_purge(&app_mb);
}
#endif
