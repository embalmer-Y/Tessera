/* SPDX-License-Identifier: Apache-2.0 */
/* ts-drv PDM 输入后端（V0.4.x M17b，Q-36/DEC-54②）：MP34DT05 PDM 麦克风
 * 采集——I2S0 PDM RX（i2s_ll 寄存器层，零上游补丁）+ GDMA AHB 环形描述符
 * + 轮询取帧（无 ISR——V1 bench 级；调用方 = ts_av_capture 阻塞语义）。
 *
 * 硬件（XIAO ESP32S3 Sense，引脚双源核验 2026-10-13：arduino-esp32#9921
 * + Seeed wiki）：GPIO41 = PDM DATA 入（I2S0I_SD 矩阵）、GPIO42 = PDM CLK
 * 出（I2S0I_WS_OUT 矩阵——S3 无独立 PDM CLK 信号，IDF 同路由）。
 *
 * 时钟（fs=16kHz mono 16bit，帧 = 320 采样 × 2B = 640B 定长）：
 *   sclk = PLL_160M；mclk = fs*256 = 4.096MHz（frac 除 39+1/16）；
 *   bclk(PDM CLK) = fs*64 = 1.024MHz（bck_div = 4，I2S_LL_PDM_BCK_FACTOR=64）
 *   ——MP34DT05 CLK 域 1.2-3.25MHz？1.024MHz 为下界邻域（数据手册下限
 *   1.2MHz 之上裕量不足时 bring-up 迭代位 1：bck_div=3 → 1.365MHz）。
 *   dsr = 16S（sinc 降采样档，SNR 优先）。
 * 采集面：GDMA ch0 in ← I2S0（peri_sel=3）；4×640B 环形描述符；EOF =
 * in_suc_eof（rx_eof_num=640 每帧触发）；轮询 suc_eof_des_addr 前进取帧。
 * cache 纪律：读前 invalidate（GDMA 直写 DRAM，Zephyr GDMA 驱动同款）。
 *
 * bring-up 状态（2026-10-13，8 轮真机迭代后如实登记为**半程**）：
 * init PASS（时钟树序修正：rx_reset 清 rx_clk_active → 使能须后置；
 * 缺 rx_enable_clock = rx_update 自旋实证）；但时钟链不出——寄存器回读
 * dump 全部配置位正确（rx_clk_active=1/rx_pdm_en=1/rx_start=1/分频写入
 * 0x24000009/0x080c080f），MCLK 与 WS 均不翻转（XTAL/PLL160 双源同象；
 * GPIO42 电平回读实证）。收口条件 = 逻辑分析仪或 IDF 同配置寄存器对照
 * 差分（盲调边界已到）。诊断面保留：无帧超时打印 GDMA/I2S 寄存器组。 */
#include <string.h>
#include <zephyr/kernel.h>
#include <zephyr/sys/printk.h>
#include <zephyr/cache.h>
#include <zephyr/drivers/gpio.h>
#include <hal/i2s_ll.h>
#include <hal/gdma_ll.h>
#include <hal/dma_types.h>
#include <hal/hal_utils.h>
#include <soc/gpio_sig_map.h>
#include <esp_private/periph_ctrl.h> /* I2S0_MCLK_OUT_IDX（诊断） */
#include <rom/gpio.h> /* esp_rom 矩阵函数（IO matrix——S3 PDM 无 IO_MUX 直通） */

/* 引脚绑定：zephyr,user（data-gpios = GPIO41 入；clk-gpios = GPIO42 出）——
 * estopbench/driver_dispatch 同族 DT 纪律；矩阵路由走 esp_rom（见文件头）。 */
#if !DT_NODE_HAS_PROP(DT_PATH(zephyr_user), pdm_data_gpios) || \
    !DT_NODE_HAS_PROP(DT_PATH(zephyr_user), pdm_clk_gpios)
#error "TS_DRV_PDM=y：zephyr,user 缺 pdm-data-gpios / pdm-clk-gpios"
#endif
static const struct gpio_dt_spec pdm_data =
	GPIO_DT_SPEC_GET(DT_PATH(zephyr_user), pdm_data_gpios);
static const struct gpio_dt_spec pdm_clk =
	GPIO_DT_SPEC_GET(DT_PATH(zephyr_user), pdm_clk_gpios);

#define PDM_FS_HZ       16000U
#define PDM_FRAME_BYTES 640U
#define PDM_NDESC       4U
#define PDM_MCLK_HZ     (PDM_FS_HZ * 256U)  /* 4.096MHz */
#define PDM_BCLK_HZ     (PDM_FS_HZ * 64U)   /* 1.024MHz（PDM CLK 出） */
#define PDM_SCLK_HZ     40000000U           /* XTAL（bring-up 实证源选择） */
#define GDMA_CH         0U
#define GDMA_PERIPH_I2S0 3                  /* dma_esp32.h ESP_GDMA_TRIG_PERIPH_I2S0 */

static i2s_dev_t *const i2s = &I2S0;
static gdma_dev_t *const gdma = &GDMA;

static dma_descriptor_align4_t pdm_desc[PDM_NDESC] __aligned(4);
static uint8_t pdm_buf[PDM_NDESC][PDM_FRAME_BYTES] __aligned(4);
static bool pdm_inited;
static uint32_t pdm_last_eof; /* 上次已取帧的描述符地址（0 = 首帧待定） */

int ts_drv_pdm_init(void)
{
	if (pdm_inited) {
		return 0;
	}
	/* 引脚：GPIO 模式 + 矩阵路由（S3 PDM 走 IO matrix：SD 入 25 / WS 出 27） */
	if (!gpio_is_ready_dt(&pdm_data) || !gpio_is_ready_dt(&pdm_clk)) {
		printk("[pdm] gpio not ready\n");
		return -1;
	}
	gpio_pin_configure_dt(&pdm_data, GPIO_INPUT | GPIO_PULL_UP);
	gpio_pin_configure_dt(&pdm_clk, GPIO_OUTPUT_LOW);
	rom_gpio_pad_select_gpio(pdm_data.pin);
	rom_gpio_pad_input_enable(pdm_data.pin);
	rom_gpio_matrix_in(pdm_data.pin, I2S0I_SD_IN_IDX, false);
	rom_gpio_pad_select_gpio(pdm_clk.pin);
	rom_gpio_matrix_out(pdm_clk.pin, I2S0I_WS_OUT_IDX, false, false);
	/* 时钟树（序敏感——rx_reset 会清 rx_clk_active：复位先行、使能随后；
	 * IDF i2s_hal_set_rx_clock 同序）。源 = XTAL 40MHz（恒在——PLL_F160M
	 * 在 Zephyr 下疑未上电：bring-up 实证 MCLK 恒高后切换）。 */
	i2s_ll_enable_bus_clock(0, true);
	i2s_ll_reset_register(0);
	i2s_ll_enable_core_clock(i2s, true);
	i2s_ll_rx_reset(i2s);
	i2s_ll_rx_reset_fifo(i2s);
	i2s_ll_rx_clk_set_src(i2s, I2S_CLK_SRC_XTAL);

	/* mclk 分频（frac）：XTAL 40M / (9 + 49/64) = 4.096MHz */
	hal_utils_clk_div_t mdiv = {
		.integer = 9, .numerator = 49, .denominator = 64, /* 9.765625 */
	};
	uint32_t bck_div = PDM_MCLK_HZ / PDM_BCLK_HZ;      /* 4 */

	i2s_ll_rx_set_mclk(i2s, &mdiv);
	i2s_ll_rx_set_bck_div_num(i2s, bck_div);
	i2s_ll_mclk_bind_to_rx_clk(i2s);
	i2s_ll_rx_enable_clock(i2s); /* 复位后置（缺此 = rx_update 自旋，bring-up 实证） */
	i2s_ll_rx_set_sample_bit(i2s, 16, 16);
	i2s_ll_rx_set_ws_width(i2s, 32);
	i2s_ll_rx_set_half_sample_bit(i2s, 16);
	i2s_ll_rx_enable_mono_mode(i2s, true);
	i2s_ll_rx_set_pdm_dsr(i2s, I2S_PDM_DSR_16S);
	i2s_ll_rx_set_eof_num(i2s, PDM_FRAME_BYTES);
	i2s_ll_rx_enable_pdm(i2s, true);

	/* GDMA：环形描述符（owner check 关——环形覆写语义，取帧靠 EOF 轮询） */
	gdma_ll_enable_bus_clock(0, true); /* 组号形参（RCC 宏包） */
	gdma_ll_force_enable_reg_clock(gdma, true);
	gdma_ll_rx_reset_channel(gdma, GDMA_CH);
	gdma_ll_rx_enable_owner_check(gdma, GDMA_CH, false);
	gdma_ll_rx_connect_to_periph(gdma, GDMA_CH, GDMA_PERIPH_I2S0);
	for (uint32_t i = 0; i < PDM_NDESC; i++) {
		memset(&pdm_desc[i].dw0, 0, sizeof(pdm_desc[i].dw0));
		pdm_desc[i].dw0.size = PDM_FRAME_BYTES;
		pdm_desc[i].dw0.owner = 1; /* DMA */
		pdm_desc[i].buffer = pdm_buf[i];
		pdm_desc[i].next = &pdm_desc[(i + 1) % PDM_NDESC];
	}
	pdm_last_eof = 0;
	sys_cache_data_flush_range((void *)&pdm_desc, sizeof(pdm_desc));
	gdma_ll_rx_set_desc_addr(gdma, GDMA_CH, (uint32_t)(uintptr_t)&pdm_desc[0]);
	gdma_ll_rx_start(gdma, GDMA_CH);

	i2s_ll_rx_start(i2s);

	/* bring-up 诊断：GPIO42（PDM CLK）电平回读——翻转 = 时钟活 */
	{
		rom_gpio_pad_input_enable(pdm_clk.pin); /* 输出 + 输入使能 = 回读 */
		uint32_t hi = 0;
		const uint32_t samples = 20000;

		for (uint32_t i = 0; i < samples; i++) {
			hi += gpio_pin_get_raw(pdm_clk.port, pdm_clk.pin);
		}
		printk("[pdm] clk readback: %u/%u high (%s)\n", (unsigned)hi,
		       (unsigned)samples,
		       (hi > 100 && hi < samples - 100) ? "TOGGLING" : "FLAT");
	}
	printk("[pdm] init: fs=%u mclk=%u bclk(PDM CLK)=%u dsr=16S ring=%ux%uB\n",
	       (unsigned)PDM_FS_HZ, (unsigned)PDM_MCLK_HZ,
	       (unsigned)PDM_BCLK_HZ, (unsigned)PDM_NDESC,
	       (unsigned)PDM_FRAME_BYTES);
	pdm_inited = true;
	return 0;
}

int ts_drv_pdm_capture(uint8_t *buf, uint32_t len)
{
	if (!pdm_inited || buf == NULL || len < PDM_FRAME_BYTES) {
		return -1;
	}
	/* 轮询 in_suc_eof 描述符地址前进（每帧 640B 触发一次；4 槽环 = 最多
	 * 丢 3 帧后取最新——bench 速率下无丢弃）。 */
	/* 超时上界 500ms（31ms/帧）——时基用 hw cycles（L5 禁 uptime 族；
	 * 板级 240MHz 档换算；轮询间隔 k_msleep 不受限） */
	const uint32_t deadline = k_cycle_get_32() +
		k_ms_to_cyc_ceil64(500);
	uint32_t eof = 0;

	for (;;) {
		eof = gdma_ll_rx_get_success_eof_desc_addr(gdma, GDMA_CH);
		if (eof != 0 && eof != pdm_last_eof) {
			break;
		}
		if ((int32_t)(k_cycle_get_32() - deadline) >= 0) {
			uint32_t hi = 0;
			uint32_t mhi = 0;
			const uint32_t samples = 20000;

			for (uint32_t i = 0; i < samples; i++) {
				hi += gpio_pin_get_raw(pdm_clk.port, pdm_clk.pin);
				mhi += gpio_pin_get_raw(pdm_data.port, pdm_data.pin);
			}
			printk("[pdm] no frame: int_raw=%08x owner=%u eof=%08x ws=%u mclk=%u /%u\n",
			       (unsigned)gdma_ll_rx_get_interrupt_status(gdma, GDMA_CH, false),
			       (unsigned)pdm_desc[0].dw0.owner,
			       (unsigned)gdma_ll_rx_get_prefetched_desc_addr(gdma, GDMA_CH),
			       (unsigned)hi, (unsigned)mhi, (unsigned)samples);
			printk("[pdm] regs: rx_clkm=%08x div=%08x conf=%08x conf1=%08x\n",
			       (unsigned)i2s->rx_clkm_conf.val,
			       (unsigned)i2s->rx_clkm_div_conf.val,
			       (unsigned)i2s->rx_conf.val,
			       (unsigned)i2s->rx_conf1.val);
			return -2;
		}
		k_msleep(5);
	}
	pdm_last_eof = eof;
	const dma_descriptor_align4_t *d =
		(const dma_descriptor_align4_t *)(uintptr_t)eof;

	sys_cache_data_invd_range(d->buffer, PDM_FRAME_BYTES);
	memcpy(buf, d->buffer, PDM_FRAME_BYTES);
	return (int)PDM_FRAME_BYTES;
}
