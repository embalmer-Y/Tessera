# SPDX-License-Identifier: Apache-2.0
"""llm_probe · LLM 端点探针域（DEC-80——owner 指令：按 URL+KEY 自动检测合法性/连通性/
支持模型/模型可用性；参考 CCR〔claude-code-router〕provider 校验思路）。

设计事实（2026-10-24 实测 router.shengsuanyun.com/api/v1 回填）：
  - 双协议路由并存：OpenAI 兼容（Bearer + /models + /chat/completions）与
    Anthropic 兼容（x-api-key + /models + /messages）可同时应答；
  - **/models 可不鉴权**（坏 key 亦 200）——「能拉模型表」≠「key 有效」，
    key 有效性必须经鉴权面（/messages 类 POST）以 401/403 判定；
  - 部分路由 max_tokens 下限 16（8 → 400 参数错——此类 400 恰证明连通+鉴权
    通过且到达模型层校验）；
  - reasoning 模型小 token 预算可能全部消耗在推理（文本空）——可用性判定以
    200 + usage 为准，文本仅作参考。

凭据红线：报告全程不含 key；探测建议只给 env 变量名。key 由调用方提供
（MCP 面经 key_env 环境变量名解析——密钥值不经工具参数与审计流）。
"""
from __future__ import annotations

import json
import ssl
import time
from dataclasses import asdict, dataclass, field
from typing import Any
from urllib.parse import urlsplit

import httpx

#: 冒烟 token 预算：16 = 实测路由下限（8 报 400——见模块 docstring）
SMOKE_MAX_TOKENS = 16
SMOKE_TIMEOUT_S = 30.0
_ANTHROPIC_VERSION = "2023-06-01"


# ---------- URL 合法性 ----------
def validate_url(url: str) -> list[str]:
    """静态校验（不发网络请求）。返回问题清单——空 = 合法。"""
    issues: list[str] = []
    if not url or not url.strip():
        return ["URL 为空"]
    if any(c in url for c in " \t\r\n"):
        issues.append("URL 含空白/换行符（拒绝——防请求拆分注入）")
        return issues
    parts = urlsplit(url)
    if parts.scheme not in ("http", "https"):
        issues.append(f"协议须为 http/https（当前 {parts.scheme or '缺失'}）")
    if not parts.hostname:
        issues.append("缺少主机名")
    if ".." in parts.path:
        issues.append("路径含 .. 片段")
    if not parts.path or parts.path == "/":
        issues.append("提示：路径为空——多数兼容端点需带版本段（如 /v1 或 /api/v1）")
    return issues


# ---------- 报告模型 ----------
@dataclass
class LlmProbeReport:
    url: str
    url_valid: bool
    issues: list[str] = field(default_factory=list)
    reachability: dict[str, Any] = field(default_factory=dict)
    protocols: dict[str, bool] = field(default_factory=dict)
    models: dict[str, Any] = field(default_factory=dict)
    key_valid: dict[str, Any] = field(default_factory=dict)
    model_check: dict[str, Any] = field(default_factory=dict)
    suggestion: dict[str, Any] = field(default_factory=dict)
    overall_ok: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# ---------- 内部工具 ----------
def _headers_openai(key: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}


def _headers_anthropic(key: str) -> dict[str, str]:
    return {"x-api-key": key, "anthropic-version": _ANTHROPIC_VERSION,
            "Content-Type": "application/json"}


def _classify_exc(exc: Exception) -> dict[str, str]:
    """网络异常分类（httpx 异常族 → 人类可读类别 + 处置提示）。"""
    if isinstance(exc, (httpx.ConnectTimeout, httpx.ReadTimeout, httpx.WriteTimeout,
                        httpx.PoolTimeout)):
        return {"error_class": "超时",
                "hint": "端点无响应——检查 URL 端口/防火墙，或经代理（HTTPS_PROXY）"}
    if isinstance(exc, httpx.ConnectError):
        return {"error_class": "连接失败（DNS 解析失败或拒连）",
                "hint": "核对域名与端口；网络受限时配置代理后重试"}
    if isinstance(exc, ssl.SSLError) or "ssl" in str(getattr(exc, "__cause__", "")).lower():
        return {"error_class": "TLS 握手失败",
                "hint": "证书链/协议版本问题——检查系统 CA 或端点证书"}
    return {"error_class": f"{type(exc).__name__}", "hint": str(exc)[:120]}


def _parse_models(payload: Any) -> list[str]:
    """模型 id 提取（兼容三形态：Anthropic {id} / OpenAI {id} / 路由扩展 {api_name}）。"""
    if not isinstance(payload, dict):
        return []
    out: list[str] = []
    for item in payload.get("data") or []:
        if isinstance(item, dict):
            mid = item.get("id") or item.get("api_name") or item.get("name") or ""
            if mid:
                out.append(str(mid))
        elif isinstance(item, str):
            out.append(item)
    return out


def _pick_smoke_model(models: list[str], requested: str | None) -> str | None:
    if requested:
        return requested
    if not models:
        return None
    for frag in ("flash", "mini", "haiku", "lite"):   # 成本敏感优先
        for m in models:
            if frag in m.lower():
                return m
    return models[0]


def _extract_text(protocol: str, payload: dict[str, Any]) -> str:
    if protocol == "anthropic":
        blocks = payload.get("content") or []
        return "".join(b.get("text", "") for b in blocks
                       if isinstance(b, dict) and b.get("type") == "text")
    choice = (payload.get("choices") or [{}])[0]
    msg = choice.get("message") or {}
    return msg.get("content") or ""


# ---------- 主探针 ----------
def probe(url: str, key: str, *, model: str | None = None,
          timeout_s: float = 20.0, max_models_sample: int = 15,
          transport: httpx.BaseTransport | None = None) -> LlmProbeReport:
    """端到端探测。transport 供测试注入（httpx.MockTransport）——生产缺省真实网络
    （trust_env=True：尊重 HTTPS_PROXY/HTTP_PROXY 环境代理）。"""
    issues = validate_url(url)
    rep = LlmProbeReport(url=url, url_valid=not [i for i in issues if not i.startswith("提示")],
                         issues=issues)
    if not rep.url_valid:
        return rep

    with httpx.Client(timeout=timeout_s, transport=transport) as client:
        # ---- ① 连通性 + 协议检测 + 模型列表（/models 双头探测） ----
        models: list[str] = []
        protocols: dict[str, bool] = {"openai": False, "anthropic": False}
        reach: dict[str, Any] = {"ok": False}
        for proto, headers in (("openai", _headers_openai(key)),
                               ("anthropic", _headers_anthropic(key))):
            try:
                r = client.get(f"{url.rstrip('/')}/models", headers=headers)
                reach["ok"] = True
                reach["http_status"] = r.status_code
                if r.status_code in (200, 401, 403):
                    try:
                        ids = _parse_models(r.json())
                    except (json.JSONDecodeError, ValueError):
                        ids = []
                    if ids or r.status_code == 200:
                        protocols[proto] = True
                        models.extend(m for m in ids if m not in models)
            except Exception as exc:  # noqa: BLE001 —— 分类后如实入报告
                if not reach["ok"]:
                    reach = {"ok": False, **_classify_exc(exc)}
        rep.protocols = protocols
        rep.reachability = reach
        rep.models = {
            "count": len(models),
            "sample": models[:max_models_sample],
            "note": "/models 或不鉴权——模型表可达不代表 key 有效（key 经鉴权面判定）"
                    if models else "未取得模型表（端点无 /models 或形态未知）",
        }
        if not reach["ok"]:
            return rep

        # ---- ② key 有效性 + 模型可用性（鉴权面最小调用——合一） ----
        proto = "anthropic" if protocols.get("anthropic") else "openai"
        path = "/messages" if proto == "anthropic" else "/chat/completions"
        headers = _headers_anthropic(key) if proto == "anthropic" else _headers_openai(key)
        target = _pick_smoke_model(models, model)
        payload = {"model": target or "", "max_tokens": SMOKE_MAX_TOKENS,
                   "messages": [{"role": "user", "content": "ping"}]}
        key_valid: dict[str, Any] = {"checked": False}
        model_check: dict[str, Any] = {"model": target, "ok": False}
        try:
            t0 = time.monotonic()
            r = client.post(f"{url.rstrip('/')}{path}", headers=headers,
                            content=json.dumps(payload))
            latency_ms = round((time.monotonic() - t0) * 1000)
            body: dict[str, Any] = {}
            try:
                body = r.json()
            except (json.JSONDecodeError, ValueError):
                body = {"raw": r.text[:200]}
            err = body.get("error") or {}
            err_msg = str(err.get("message") or body.get("message") or "")[:160]

            if r.status_code in (401, 403):
                key_valid = {"checked": True, "ok": False,
                             "detail": f"HTTP {r.status_code}：key 无效或无权限（{err_msg}）"}
                model_check = {"model": target, "ok": False, "detail": "未测——key 无效"}
            else:
                # 200/400/404/429/5xx —— 鉴权已通过（401 才是 key 问题）
                key_valid = {"checked": True, "ok": True,
                             "detail": f"鉴权面 HTTP {r.status_code} 通过（401 才判 key 无效）"}
                if r.status_code == 200:
                    model_check = {
                        "model": body.get("model") or target,
                        "ok": True, "http_status": 200, "latency_ms": latency_ms,
                        "usage": body.get("usage") or {},
                        "text": _extract_text(proto, body)[:120],
                        "note": "文本为空 ≠ 不可用——reasoning 模型小 token 预算可全耗于推理",
                    }
                elif r.status_code == 404:
                    model_check = {"model": target, "ok": False, "http_status": 404,
                                   "detail": "模型不存在或路径不匹配（核对该端点模型清单）"}
                elif r.status_code == 400 and (
                        "model" in err_msg.lower()
                        or "invalid_request" in str(err.get("type", "")).lower()):
                    model_check = {"model": target, "ok": False, "http_status": 400,
                                   "detail": f"请求被拒（{err_msg}）——多为模型名无效"}
                elif r.status_code == 429:
                    model_check = {"model": target, "ok": None, "http_status": 429,
                                   "detail": "限流/配额——连通与鉴权正常，可用性无法本次判定"}
                else:
                    model_check = {"model": target, "ok": False, "http_status": r.status_code,
                                   "detail": err_msg or "非预期状态"}
        except Exception as exc:  # noqa: BLE001
            key_valid = {"checked": False,
                         "detail": f"鉴权面调用失败：{type(exc).__name__}: {exc}"[:160]}
            model_check = {"model": target, "ok": False}
        rep.key_valid = key_valid
        rep.model_check = model_check

        # ---- ③ 配置建议（无 key 值——只有 env 名） ----
        if protocols.get("anthropic"):
            # anthropic SDK 在 base 后自拼 /v1/messages——base 已含 /v1 时须剥（实测 2026-10-24：
            # /api/v1 形态经 SDK = /api/v1/v1/messages → 路由 404；/api 形态 200）
            _sdk_base = url.rstrip("/")
            if _sdk_base.endswith("/v1"):
                _sdk_base = _sdk_base[: -len("/v1")]
            rep.suggestion = {
                "provider_prefix": "anthropic",
                "base_url": url,
                "sdk_base_url": _sdk_base,
                "model_string": f"anthropic:{target}" if target else None,
                "env": {"base": "ANTHROPIC_BASE_URL", "key": "ANTHROPIC_API_KEY"},
                "note": "Anthropic 兼容（Tessera 正典形态）——模型串入 config.toml"
                        " default_model；env.sh 用 sdk_base_url（SDK 自拼 /v1/messages，"
                        "已含 /v1 的探测地址须剥尾段——实测 /api/v1 → SDK base /api）",
            }
        elif protocols.get("openai"):
            rep.suggestion = {
                "provider_prefix": "openai",
                "base_url": url,
                "model_string": f"openai:{target}" if target else None,
                "env": {"base": "OPENAI_BASE_URL", "key": "OPENAI_API_KEY"},
            }
        rep.overall_ok = bool(rep.url_valid and reach.get("ok")
                              and key_valid.get("ok") and model_check.get("ok"))
    return rep


def render_report(rep: LlmProbeReport) -> str:
    """人读形态（CLI 缺省输出——逐项 ✓/✗ + 处置提示）。"""
    def _mark(v: Any) -> str:
        if v is True:
            return "✓"
        if v is None:
            return "◐"
        return "✗"

    lines = [f"LLM 端点探测：{rep.url}"]
    issue_txt = "；".join(rep.issues) if rep.issues else "OK"
    lines.append(f"  URL 合法性    {_mark(rep.url_valid)}  {issue_txt}")
    r = rep.reachability
    lines.append(f"  连通性        {_mark(r.get('ok'))}  "
                 + (f"HTTP {r.get('http_status')}" if r.get("ok") else
                    f"{r.get('error_class', '未知')}——{r.get('hint', '')}"))
    if rep.protocols:
        ps = " + ".join(k for k, v in rep.protocols.items() if v) or "未识别"
        lines.append(f"  协议          {_mark(any(rep.protocols.values()))}  {ps}")
    m = rep.models
    if m:
        sample = "、".join(m.get("sample", [])[:5])
        lines.append(f"  模型列表      {_mark(m.get('count', 0) > 0)}  共 {m.get('count', 0)} 个"
                     + (f"（样本：{sample}…）" if sample else ""))
    k = rep.key_valid
    if k.get("checked"):
        lines.append(f"  KEY 有效性    {_mark(k.get('ok'))}  {k.get('detail', '')}")
    c = rep.model_check
    if c.get("model"):
        extra = f"{c.get('latency_ms', '?')}ms" if c.get("ok") else c.get("detail", "")
        lines.append(f"  模型可用性    {_mark(c.get('ok'))}  {c.get('model')}（{extra}）")
    s = rep.suggestion
    if s:
        sdk_note = ((f"（SDK base={s['sdk_base_url']}——剥 /v1 尾段）")
                    if s.get("sdk_base_url") and s["sdk_base_url"] != s["base_url"] else "")
        model_str = s.get("model_string") or "待定"
        lines.append(f"  配置建议      provider={s['provider_prefix']} · "
                     f"base_url={s['base_url']}{sdk_note} · 模型串={model_str} · "
                     f"env：{s['env']['base']} / {s['env']['key']}")
    lines.append(f"  总判定        {_mark(rep.overall_ok)}")
    return "\n".join(lines)
