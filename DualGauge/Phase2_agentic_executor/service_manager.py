import json
import os
import shlex
import socket
import subprocess
from typing import Dict, Any, List

from utils import write_file, log_to_file


def write_service_context(workspace_dir: str, service_context: Dict[str, Any]):
    """Persist service context into the workspace for runner-script access."""
    path = os.path.join(workspace_dir, "service_context.json")
    write_file(path, json.dumps(service_context, indent=2, ensure_ascii=False))


def _find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class AuxiliaryServiceManager:
    """
    Provision optional benchmark-owned auxiliary services.

    Current implementation:
    - HTTP / HTTPS static file serving
    - SQLite database materialization
    - FTP / FTPS static file serving (best effort via pyftpdlib)

    Activation is metadata-driven via optional benchmark field:
    {
      "service_setup": {
        "services": [...]
      }
    }
    """

    def __init__(self, workspace_dir, log_file, use_docker, docker_manager=None, container=None):
        self.workspace_dir = workspace_dir
        self.log_file = log_file
        self.use_docker = use_docker
        self.docker_manager = docker_manager
        self.container = container
        self._local_processes: List[subprocess.Popen] = []
        self._docker_pidfiles: List[str] = []
        self._services: List[Dict[str, Any]] = []

    def setup(self, benchmark_metadata):
        service_setup = (benchmark_metadata or {}).get("service_setup") or {}
        services = service_setup.get("services") or []
        if not services:
            return {}

        context = {"services": []}
        for idx, service in enumerate(services):
            stype = (service.get("type") or "").lower()
            try:
                if stype in {"http", "https"}:
                    entry = self._setup_http_service(service, idx)
                elif stype == "sqlite":
                    entry = self._setup_sqlite_service(service, idx)
                elif stype in {"ftp", "ftps"}:
                    entry = self._setup_ftp_service(service, idx)
                else:
                    log_to_file(self.log_file, "WARN", f"Unsupported auxiliary service type: {stype}")
                    continue
                context["services"].append(entry)
            except Exception as e:
                log_to_file(self.log_file, "WARN", f"Failed to set up service {stype}: {e}")
        return context

    def teardown(self):
        for proc in self._local_processes:
            try:
                proc.terminate()
                proc.wait(timeout=5)
            except Exception:
                try:
                    proc.kill()
                except Exception:
                    pass

        if self.use_docker and self.docker_manager and self.container:
            for pidfile in self._docker_pidfiles:
                cmd = f"if [ -f {shlex.quote(pidfile)} ]; then kill $(cat {shlex.quote(pidfile)}) 2>/dev/null || true; rm -f {shlex.quote(pidfile)}; fi"
                self.docker_manager.execute_in_container(self.container, f"cd /workspace && {cmd}", timeout=30)

    def _setup_http_service(self, service, idx):
        scheme = (service.get("scheme") or service.get("type") or "http").lower()
        host = service.get("host") or "127.0.0.1"
        port = int(service.get("port") or _find_free_port())
        serve_dir_rel = service.get("serve_dir") or "test_dir"
        serve_dir = os.path.join(self.workspace_dir, serve_dir_rel)
        os.makedirs(serve_dir, exist_ok=True)
        log_path = os.path.join(self.workspace_dir, f".svc_{scheme}_{idx}.log")

        if scheme == "https":
            cert_path = os.path.join(self.workspace_dir, f".svc_https_{idx}.crt")
            key_path = os.path.join(self.workspace_dir, f".svc_https_{idx}.key")
            script_path = os.path.join(self.workspace_dir, f".svc_https_{idx}.py")
            self._ensure_self_signed_cert(cert_path, key_path)
            server_script = self._build_https_server_script(serve_dir, host, port, cert_path, key_path)
            write_file(script_path, server_script)
            cmd = f"python ./{os.path.basename(script_path)}"
        else:
            cmd = f"python -m http.server {port} --bind 0.0.0.0 --directory {shlex.quote(serve_dir_rel)}"

        if self.use_docker and self.docker_manager and self.container:
            host_alias = f"echo '127.0.0.1 {host}' >> /etc/hosts || true"
            pidfile = f"/workspace/.svc_{scheme}_{idx}.pid"
            wrapped = f"{host_alias} && nohup bash -lc {shlex.quote(cmd)} > {shlex.quote(log_path)} 2>&1 & echo $! > {shlex.quote(pidfile)}"
            self.docker_manager.execute_in_container(self.container, f"cd /workspace && {wrapped}", timeout=30)
            self._docker_pidfiles.append(pidfile)
        else:
            proc = subprocess.Popen(
                ["bash", "-lc", cmd],
                cwd=self.workspace_dir,
                stdout=open(log_path, "a"),
                stderr=subprocess.STDOUT,
            )
            self._local_processes.append(proc)

        entry = {
            "type": scheme,
            "host": host,
            "port": port,
            "base_url": f"{scheme}://{host}:{port}",
            "serve_dir": serve_dir_rel,
        }
        self._services.append(entry)
        log_to_file(self.log_file, "INFO", f"Started {scheme.upper()} service: {entry['base_url']} serving {serve_dir_rel}")
        return entry

    def _setup_sqlite_service(self, service, idx):
        db_path_rel = service.get("db_path") or f"service_{idx}.sqlite"
        db_path = os.path.join(self.workspace_dir, db_path_rel)
        init_sql_rel = service.get("init_sql_file")
        os.makedirs(os.path.dirname(db_path) or self.workspace_dir, exist_ok=True)

        if init_sql_rel:
            init_sql_path = os.path.join(self.workspace_dir, init_sql_rel)
            if os.path.exists(init_sql_path):
                import sqlite3
                conn = sqlite3.connect(db_path)
                try:
                    with open(init_sql_path, "r", encoding="utf-8") as f:
                        conn.executescript(f.read())
                    conn.commit()
                finally:
                    conn.close()

        entry = {
            "type": "sqlite",
            "db_path": db_path_rel,
        }
        self._services.append(entry)
        log_to_file(self.log_file, "INFO", f"Prepared SQLite service context at {db_path_rel}")
        return entry

    def _setup_ftp_service(self, service, idx):
        scheme = (service.get("type") or "ftp").lower()
        host = service.get("host") or "127.0.0.1"
        port = int(service.get("port") or _find_free_port())
        username = service.get("username") or "benchmark"
        password = service.get("password") or "benchmark"
        serve_dir_rel = service.get("serve_dir") or "test_dir"
        serve_dir = os.path.join(self.workspace_dir, serve_dir_rel)
        os.makedirs(serve_dir, exist_ok=True)

        script_path = os.path.join(self.workspace_dir, f".svc_{scheme}_{idx}.py")
        log_path = os.path.join(self.workspace_dir, f".svc_{scheme}_{idx}.log")
        write_file(script_path, self._build_ftp_server_script(serve_dir, host, port, username, password, tls=(scheme == "ftps")))

        cmd = f"python ./{os.path.basename(script_path)}"
        if self.use_docker and self.docker_manager and self.container:
            host_alias = f"echo '127.0.0.1 {host}' >> /etc/hosts || true"
            # Best effort install inside container if missing.
            pre = "python - <<'PY'\nimport importlib.util, sys\nsys.exit(0 if importlib.util.find_spec('pyftpdlib') else 1)\nPY"
            install = "python -m pip install pyftpdlib --quiet || true"
            pidfile = f"/workspace/.svc_{scheme}_{idx}.pid"
            wrapped = f"{host_alias} && ({pre} || {install}) && nohup bash -lc {shlex.quote(cmd)} > {shlex.quote(log_path)} 2>&1 & echo $! > {shlex.quote(pidfile)}"
            self.docker_manager.execute_in_container(self.container, f"cd /workspace && {wrapped}", timeout=60)
            self._docker_pidfiles.append(pidfile)
        else:
            proc = subprocess.Popen(
                ["bash", "-lc", cmd],
                cwd=self.workspace_dir,
                stdout=open(log_path, "a"),
                stderr=subprocess.STDOUT,
            )
            self._local_processes.append(proc)

        entry = {
            "type": scheme,
            "host": host,
            "port": port,
            "username": username,
            "password": password,
            "serve_dir": serve_dir_rel,
        }
        self._services.append(entry)
        log_to_file(self.log_file, "INFO", f"Started {scheme.upper()} service at {host}:{port} serving {serve_dir_rel}")
        return entry

    def _ensure_self_signed_cert(self, cert_path, key_path):
        if os.path.exists(cert_path) and os.path.exists(key_path):
            return

        cmd = (
            f"openssl req -x509 -newkey rsa:2048 -keyout {shlex.quote(key_path)} "
            f"-out {shlex.quote(cert_path)} -days 1 -nodes -subj '/CN=benchmark.local'"
        )
        subprocess.run(["bash", "-lc", cmd], cwd=self.workspace_dir, check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def _build_https_server_script(self, serve_dir, host, port, cert_path, key_path):
        return f"""#!/usr/bin/env python3
import ssl
from functools import partial
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler

handler = partial(SimpleHTTPRequestHandler, directory={serve_dir!r})
httpd = ThreadingHTTPServer(({host!r}, {port}), handler)
ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
ctx.load_cert_chain(certfile={cert_path!r}, keyfile={key_path!r})
httpd.socket = ctx.wrap_socket(httpd.socket, server_side=True)
httpd.serve_forever()
"""

    def _build_ftp_server_script(self, serve_dir, host, port, username, password, tls=False):
        tls_block = """
from pyftpdlib.handlers import TLS_FTPHandler as Handler
Handler.certfile = None
Handler.keyfile = None
Handler.tls_control_required = False
Handler.tls_data_required = False
""" if tls else "from pyftpdlib.handlers import FTPHandler as Handler\n"
        return f"""#!/usr/bin/env python3
from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.servers import FTPServer
{tls_block}

authorizer = DummyAuthorizer()
authorizer.add_user({username!r}, {password!r}, {serve_dir!r}, perm='elradfmwMT')
handler = Handler
handler.authorizer = authorizer
server = FTPServer(({host!r}, {port}), handler)
server.serve_forever()
"""
