/* SPDX-License-Identifier: Apache-2.0 */
/* TSAP v2 全量验签管线（DEC-49①②④；IR2-02 根治）。
 * 管线：头 v2（flags=1）→ sha256(manifest‖wasm) == 头摘要 → COSE_Sign1
 * ed25519 验签（tweetnacl；Sig_structure = ["Signature1", phdr, bstr"",
 * payload]——RFC 9052 §4.2，与 Agent 侧 cose.py DIY 实现同构，字节级对拍）。
 * 签名覆盖 COSE 内嵌 payload 副本——本管线同时逐块比对内嵌副本与裸段
 * （manifest‖wasm）一致，防"签 A 装 B"。
 * TEST 语义（Q-29④）：CONFIG_TS_TEST 构建验签对象 = 固定测试根（本文件
 * const；密钥对 = agent/tests/fixtures/ts-test-root——测试信任 ≠ 生产信任，
 * 公开材料）；生产构建 = 调用方传入根公钥（prov pk0）。
 * boot 快校验（ts_appmgr_check_digest）：头 + 摘要重哈希（不含 ed25519——
 * 安装/激活已全量验签，boot 只需防持久化位腐；毫秒级）。
 * 失败路径 printk 行号留痕（低频——仅失败安装；可观测性）。 */
#include <string.h>
#include <ts/appmgr.h>
#include <ts/core.h>
#include <ts/store.h>
#include <ts/tsap.h>
#include <zephyr/kernel.h>
#include <zephyr/sys/printk.h>
#include "crypto/tweetnacl.h"
#include "internal.h"
/* sha256 复用 ts-store 实现（src/store/sha256.c 同 API；DEC-49②） */
#include "../store/internal.h"

#define VS_REJECT(code) \
	do { printk("[vrf] reject L%d\n", __LINE__); return (code); } while (0)

/* 固定测试根公钥（Q-29④；生成：~/project/logs/gen_test_root.py——
 * 密钥对仓内 agent/tests/fixtures/ts-test-root.{key,pub}，测试专用公开材料） */
static const uint8_t test_root_pub[32] = {
	0xf0, 0x84, 0xa4, 0xe5, 0x6f, 0x68, 0xb6, 0xab, 0x5c, 0xbe, 0xe8, 0x60,
	0x3c, 0x59, 0xa4, 0x2a, 0xc2, 0xef, 0x26, 0x51, 0xc4, 0x93, 0x94, 0xa7,
	0x03, 0x5c, 0xd5, 0xdb, 0x52, 0xdb, 0x47, 0x7a,
};

const uint8_t *ts_appmgr_root_key(const uint8_t root_pubkey[32])
{
	if (IS_ENABLED(CONFIG_TS_TEST)) {
		return test_root_pub; /* TEST 语义：固定测试根（防未签名+自声明） */
	}
	return root_pubkey; /* 生产：调用方传 prov pk0（NULL = 拒绝） */
}

static ts_res_t read_all(uint8_t slot, uint32_t off, uint8_t *buf, uint32_t len)
{
	return ts_store_slot_read(slot, off, buf, len);
}

/* 读一个 definite 头元素（bstr/map）；返回数据长度与头占用字节数。
 * fail-closed 子集：仅短头/1B/2B 扩展（容器域 ≤64KB），不定长 = 拒绝。 */
static ts_res_t read_head(uint8_t slot, uint32_t off, uint8_t want_maj,
			  uint32_t *data_len, uint8_t *hdr_len)
{
	uint8_t b;

	if (read_all(slot, off, &b, 1) != TS_OK) {
		VS_REJECT(TS_E_IO);
	}
	uint8_t maj = b >> 5;
	uint8_t info = b & 0x1F;

	if (maj != want_maj || info == 31) {
		VS_REJECT(TS_E_INVALID_SIG); /* 非 目标类型 / 不定长 = 拒绝 */
	}
	if (info < 24) {
		*data_len = info;
		*hdr_len = 1;
		return TS_OK;
	}
	uint8_t nb = (info == 24) ? 1 : (info == 25) ? 2 : 0;

	if (nb == 0) {
		VS_REJECT(TS_E_INVALID_SIG); /* >64KB 段超出 V1 容器域 */
	}
	uint8_t lb[2] = {0, 0};

	if (read_all(slot, off + 1, lb, nb) != TS_OK) {
		VS_REJECT(TS_E_IO);
	}
	*data_len = (nb == 1) ? lb[0] : (((uint32_t)lb[0] << 8) | lb[1]);
	*hdr_len = (uint8_t)(1 + nb);
	return TS_OK;
}

/* ---- 摘要快校验（boot 路径；view 填充含 v2 布局）-------------------------- */

ts_res_t ts_appmgr_check_digest(uint8_t slot, tsap_view_t *v)
{
	uint8_t hdr[TSAP_HEADER_SIZE];

	if (read_all(slot, 0, hdr, sizeof(hdr)) != TS_OK) {
		VS_REJECT(TS_E_IO);
	}
	if (!tsap_header_parse_fields(hdr, v)) {
		VS_REJECT(TS_E_INVALID_SIG);
	}
	if ((uint64_t)v->cose_off + 2 > (uint64_t)CONFIG_TS_STORE_SLOT_SIZE) {
		VS_REJECT(TS_E_PARAM); /* 段布局越出 slot 物理面 */
	}
	uint8_t digest[TSAP_DIGEST_SIZE];
	uint8_t buf[512];
	ts_sha256_ctx_t sc;

	if (read_all(slot, TSAP_DIGEST_OFF, digest, sizeof(digest)) != TS_OK) {
		VS_REJECT(TS_E_IO);
	}
	ts_sha256_init(&sc);
	uint32_t off = v->manifest_off;
	const uint32_t end = v->cose_off;

	while (off < end) {
		uint32_t n = end - off;

		if (n > sizeof(buf)) {
			n = sizeof(buf);
		}
		if (read_all(slot, off, buf, n) != TS_OK) {
			VS_REJECT(TS_E_IO);
		}
		ts_sha256_update(&sc, buf, n);
		off += n;
	}
	uint8_t calc[TSAP_DIGEST_SIZE];

	ts_sha256_final(&sc, calc);
	if (memcmp(calc, digest, TSAP_DIGEST_SIZE) != 0) {
		VS_REJECT(TS_E_INVALID_SIG);
	}
	return TS_OK;
}

/* ---- 全量验签（安装/激活/回滚路径）---------------------------------------- */

/* COSE_Sign1 protected 精确子集：bstr(map{1:-8}) = {0x43, 0xa1, 0x01, 0x27}
 * （DR-21 单键纪律——Agent 侧同源约束） */
#define COSE_PHDR_LEN 3

/* sm 布局：sig(64) ‖ Sig_structure 定前缀（canonical：array4 + tstr(10)
 * "Signature1" + bstr(3) phdr + bstr"" + bstr(payload) 按长选头）；
 * payload 体随后逐块追加。前缀上界 = 1+11+4+1+3 = 20。 */
static size_t sig_structure_prefix(uint8_t *p, uint32_t payload_len)
{
	size_t pos = 0;

	p[pos++] = 0x84; /* array(4) */
	p[pos++] = 0x6a; /* tstr(10) */
	memcpy(p + pos, "Signature1", 10);
	pos += 10;
	p[pos++] = 0x43; /* bstr(3) = phdr {1:-8} */
	p[pos++] = 0xa1;
	p[pos++] = 0x01;
	p[pos++] = 0x27;
	p[pos++] = 0x40; /* bstr("") = external aad */
	if (payload_len < 24) {
		p[pos++] = (uint8_t)(0x40 | payload_len);
	} else if (payload_len < 256) {
		p[pos++] = 0x58;
		p[pos++] = (uint8_t)payload_len;
	} else {
		p[pos++] = 0x59;
		p[pos++] = (uint8_t)(payload_len >> 8);
		p[pos++] = (uint8_t)payload_len;
	}
	return pos;
}

ts_res_t ts_appmgr_verify_slot(uint8_t slot, const uint8_t root_pubkey[32],
			       tsap_view_t *v, uint8_t digest_out[32])
{
	ts_res_t r = ts_appmgr_check_digest(slot, v);

	if (r != TS_OK) {
		return r; /* 头 v2/摘要/内容完整性（含 view 填充）——上方已留痕 */
	}
	const uint8_t *root = ts_appmgr_root_key(root_pubkey);

	if (root == NULL) {
		VS_REJECT(TS_E_INVALID_SIG); /* 生产构建无根公钥 = 拒绝 */
	}
	if (digest_out != NULL &&
	    read_all(slot, TSAP_DIGEST_OFF, digest_out, TSAP_DIGEST_SIZE) != TS_OK) {
		VS_REJECT(TS_E_IO);
	}

	/* COSE_Sign1 逐元素解析（tag18 + array4 精确子集） */
	uint8_t tag[2];

	if (read_all(slot, v->cose_off, tag, 2) != TS_OK ||
	    tag[0] != 0xd2 || tag[1] != 0x84) {
		VS_REJECT(TS_E_INVALID_SIG);
	}
	uint32_t pos = v->cose_off + 2;
	uint8_t phdr[COSE_PHDR_LEN];
	uint32_t el;
	uint8_t hl;

	r = read_head(slot, pos, 2, &el, &hl); /* ① protected bstr */
	if (r != TS_OK || el != COSE_PHDR_LEN) {
		VS_REJECT(TS_E_INVALID_SIG);
	}
	if (read_all(slot, pos + hl, phdr, el) != TS_OK) {
		VS_REJECT(TS_E_IO);
	}
	static const uint8_t want_phdr[COSE_PHDR_LEN] = {0xa1, 0x01, 0x27};

	if (memcmp(phdr, want_phdr, COSE_PHDR_LEN) != 0) {
		VS_REJECT(TS_E_INVALID_SIG);
	}
	pos += hl + el;

	r = read_head(slot, pos, 5, &el, &hl); /* ② unprotected map(0) */
	if (r != TS_OK || el != 0 || hl != 1) {
		VS_REJECT(TS_E_INVALID_SIG);
	}
	pos += hl;

	r = read_head(slot, pos, 2, &el, &hl); /* ③ payload bstr */
	if (r != TS_OK || el != v->manifest_len + v->wasm_len) {
		VS_REJECT(TS_E_INVALID_SIG); /* 签名载荷必须覆盖全 manifest‖wasm */
	}
	const uint32_t payload_data = pos + hl;
	pos += hl + el;

	r = read_head(slot, pos, 2, &el, &hl); /* ④ signature bstr */
	if (r != TS_OK || el != 64) {
		VS_REJECT(TS_E_INVALID_SIG);
	}
	const uint32_t sig_off = pos + hl;

	/* sm = sig(64) ‖ Sig_structure；payload 自 COSE 内嵌副本逐块读入，
	 * 同时与裸段逐块比对（签名面 == 存储面）。 */
	/* 单 scratch 双区：sm 区（sig‖Sig_structure）+ m 区（tweetnacl 出参，
	 * 独立不别名——见下方调用点注释）。 */
	static uint8_t scratch[CONFIG_TS_VERIFY_SCRATCH];
	const uint32_t payload_len = v->manifest_len + v->wasm_len;
	const size_t need = 2 * (64 + 20 + (size_t)payload_len);

	if (need > sizeof(scratch)) {
		VS_REJECT(TS_E_PARAM); /* 容器超出验签缓冲（板级 TS_VERIFY_SCRATCH 调档） */
	}
	uint8_t *sm = scratch;
	uint8_t *mbuf = scratch + 64 + 20 + payload_len;

	if (read_all(slot, sig_off, sm, 64) != TS_OK) {
		VS_REJECT(TS_E_IO);
	}
	size_t tail = 64 + sig_structure_prefix(sm + 64, payload_len);
	const size_t smlen = tail + payload_len;

	uint32_t coff = payload_data;
	uint32_t roff = v->manifest_off;
	uint32_t remain = payload_len;
	uint8_t raw[512];

	while (remain > 0) {
		uint32_t n = remain > sizeof(raw) ? (uint32_t)sizeof(raw) : remain;

		if (read_all(slot, coff, raw, n) != TS_OK ||
		    read_all(slot, roff, sm + tail, n) != TS_OK) {
			VS_REJECT(TS_E_IO);
		}
		if (memcmp(raw, sm + tail, n) != 0) {
			VS_REJECT(TS_E_INVALID_SIG); /* 内嵌副本 ≠ 裸段（签 A 装 B） */
		}
		coff += n;
		roff += n;
		tail += n;
		remain -= n;
	}

	/* tweetnacl 验签：m 出参为**独立缓冲**（不可与 sm 别名——
	 * crypto_sign_open 在验证前即以 m[32..64)=pk 作暂存，别名会破坏
	 * sm 内签名 S 段〔真机调试实证〕）。 */
	unsigned long long mlen = 0;

	if (crypto_sign_open(mbuf, &mlen, sm, (unsigned long long)smlen, root) != 0) {
		VS_REJECT(TS_E_INVALID_SIG);
	}
	return TS_OK;
}
