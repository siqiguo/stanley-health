#!/usr/bin/env python3
"""Minimal OAuth callback receiver for the private Huawei Health integration."""

import hmac
import json
import os
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from socketserver import ThreadingMixIn
from urllib.parse import parse_qs, urlparse


DATA_DIR = Path(os.environ.get("HUAWEI_HEALTH_DATA_DIR", "/var/lib/huawei-health"))
CALLBACK_FILE = DATA_DIR / "oauth-callback.json"
EXPECTED_STATE_FILE = DATA_DIR / "oauth-state"


class Handler(BaseHTTPRequestHandler):
    server_version = "StanleyHealthCallback/1.1"

    def _send(self, status: int, body: str, content_type: str = "text/html; charset=utf-8", *, head=False):
        payload = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.end_headers()
        if not head:
            self.wfile.write(payload)

    def _static_response(self, path: str, *, head=False) -> bool:
        if path == "/health/status":
            self._send(200, '{"status":"ok"}', "application/json", head=head)
            return True
        if path == "/health/privacy":
            self._send(200, """<!doctype html><meta charset='utf-8'><title>家庭健康数据助手隐私说明</title>
<h1>家庭健康数据助手隐私说明</h1>
<p>本服务仅供账户所有者本人使用，用于在其明确授权后读取华为运动健康数据，并在家庭私有环境中生成个人趋势摘要。</p>
<p>服务遵循最小权限原则，不出售、不公开、不向无关第三方分享健康数据。用户可随时在华为运动健康中撤销授权，并要求删除本地数据。</p>
<p>联系邮箱：health@siqiguo.me</p>""", head=head)
            return True
        return False

    def do_HEAD(self):
        parsed = urlparse(self.path)
        if self._static_response(parsed.path, head=True):
            return
        if parsed.path == "/health/oauth/callback":
            self._send(200, "", head=True)
            return
        self._send(404, "Not Found", "text/plain; charset=utf-8", head=True)

    def do_GET(self):
        parsed = urlparse(self.path)
        if self._static_response(parsed.path):
            return
        if parsed.path != "/health/oauth/callback":
            self._send(404, "Not Found", "text/plain; charset=utf-8")
            return

        params = parse_qs(parsed.query, keep_blank_values=True)
        received_state = (params.get("state") or [None])[0]
        if EXPECTED_STATE_FILE.exists():
            expected_state = EXPECTED_STATE_FILE.read_text(encoding="utf-8").strip()
            if not received_state or not hmac.compare_digest(received_state, expected_state):
                self._send(400, """<!doctype html><meta charset='utf-8'><title>授权校验失败</title>
<h1>授权校验失败</h1><p>state 参数不匹配，请重新发起授权。</p>""")
                return

        record = {
            "received_at": int(time.time()),
            "code": (params.get("code") or [None])[0],
            "state": received_state,
            "error": (params.get("error") or [None])[0],
            "error_description": (params.get("error_description") or [None])[0],
        }
        DATA_DIR.mkdir(parents=True, exist_ok=True, mode=0o700)
        tmp = CALLBACK_FILE.with_suffix(".tmp")
        tmp.write_text(json.dumps(record, ensure_ascii=False), encoding="utf-8")
        os.chmod(tmp, 0o600)
        tmp.replace(CALLBACK_FILE)

        if record["code"]:
            self._send(200, """<!doctype html><meta charset='utf-8'><title>授权成功</title>
<h1>华为健康授权已返回</h1><p>可以关闭此页面并返回对话。授权码已安全保存，页面不会显示敏感内容。</p>""")
        else:
            self._send(400, """<!doctype html><meta charset='utf-8'><title>授权未完成</title>
<h1>授权未完成</h1><p>请返回对话查看下一步说明。</p>""")

    def log_message(self, fmt, *args):
        # Query strings may contain authorization codes, so never log them.
        print(f"{self.client_address[0]} - {self.command} {urlparse(self.path).path}")


class ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True


if __name__ == "__main__":
    ThreadingHTTPServer(("127.0.0.1", 8091), Handler).serve_forever()

