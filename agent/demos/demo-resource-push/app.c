/* SPDX-License-Identifier: Apache-2.0 */
/* D-AK4: K4 net+SD 资源推送真机 demo（CG5-B 方案 A 消费端）。
 * Zero #include, zero libc（D-SD 同型纪律）。宿主在激活后经部署会话推送
 * 资源文件 /SD:/res/ak4.txt（36B = "AK4-RES-" + 28 数字）；APP 每 tick
 * 轮询读出直至字节全匹配 → 宣告 AK4 DONE（超时 40 tick 宣告 FAIL）。
 * 判据（console [appN/l0] 行）：
 *   ak4 wait rc=N   —— 资源未就绪期逐 tick 如实
 *   ak4 match=1     —— 推送内容字节级命中
 *   AK4 DONE        —— 收口行（驱动侧另以 push_resources verified 回执判）
 */

static const char PATH_RES[] = "/SD:/res/ak4.txt";

static const char EXPECT[36] = {
	'A', 'K', '4', '-', 'R', 'E', 'S', '-',
	'0', '1', '2', '3', '4', '5', '6', '7', '8', '9',
	'0', '1', '2', '3', '4', '5', '6', '7', '8', '9',
	'0', '1', '2', '3', '4', '5', '6', '7', '8'
};

static char RBUF[36];
static int g_state = 0; /* 0 = 轮询；1 = done；2 = fail */
static int g_ticks = 0;
static int g_ctx = 0;

extern int ts_fs_read(int ctx, const char *path, int path_len, int off,
		      char *buf, int cap);
extern int ts_log_write(int ctx, int lvl, const char *msg, int len);

static int my_strlen(const char *s)
{
	int n = 0;

	while (s[n] != 0) {
		n++;
	}
	return n;
}

static void append_n(char *buf, int *pos, const char *s, int n)
{
	int i;

	for (i = 0; i < n; i++) {
		buf[(*pos)++] = s[i];
	}
}

static void append_dec(char *buf, int *pos, int v)
{
	char tmp[16];
	int t = 0;
	int i;

	if (v == 0) {
		buf[(*pos)++] = '0';
		return;
	}
	if (v < 0) {
		buf[(*pos)++] = '-';
		v = -v;
	}
	while (v > 0 && t < 16) {
		tmp[t++] = (char)('0' + (v % 10));
		v = v / 10;
	}
	for (i = t - 1; i >= 0; i--) {
		buf[(*pos)++] = tmp[i];
	}
}

__attribute__((export_name("app_init")))
int app_init(int ctx)
{
	char msg[12];
	int pos = 0;

	g_ctx = ctx;
	append_n(msg, &pos, "ak4 init", 8);
	ts_log_write(g_ctx, 0, msg, pos);
	return 0;
}

__attribute__((export_name("app_tick")))
int app_tick(void)
{
	char msg[36];
	int pos = 0;

	if (g_state != 0) {
		return 0;
	}
	g_ticks++;
	int p_len = my_strlen(PATH_RES);
	int rc = ts_fs_read(g_ctx, PATH_RES, p_len, 0, RBUF, 36);

	if (rc == 36) {
		int i;
		int match = 1;

		for (i = 0; i < 36; i++) {
			if (RBUF[i] != EXPECT[i]) {
				match = 0;
				break;
			}
		}
		if (match) {
			append_n(msg, &pos, "ak4 match=1", 11);
			ts_log_write(g_ctx, 0, msg, pos);
			pos = 0;
			append_n(msg, &pos, "AK4 DONE", 8);
			ts_log_write(g_ctx, 0, msg, pos);
			g_state = 1;
			return 0;
		}
	}
	append_n(msg, &pos, "ak4 wait rc=", 12);
	append_dec(msg, &pos, rc);
	ts_log_write(g_ctx, 0, msg, pos);
	if (g_ticks >= 40) {
		pos = 0;
		append_n(msg, &pos, "AK4 FAIL ticks=40", 17);
		ts_log_write(g_ctx, 0, msg, pos);
		g_state = 2;
	}
	return 0;
}

__attribute__((export_name("app_evt")))
int app_evt(int v)
{
	(void)v;
	return 0;
}

__attribute__((export_name("health_ping")))
int health_ping(void)
{
	return 0;
}
