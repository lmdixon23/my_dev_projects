"""Run network-reachability tests against a deployed test client.

Usage:
    python test_traffic.py --host <public_ip_or_dns>
    python test_traffic.py --host <host> --ssh-cidr 203.0.113.4/32

The script verifies the README's stated expectations:
  * HTTP/80   should be reachable from anywhere.
  * SSH/22    should be reachable only from `--ssh-cidr` (we can't
              actually prove negative reachability from here, but we
              can check that port 22 is at least open to *us* when
              the operator IP is in the allowlist).
  * Other TCP should be closed (we probe a small handful as a sanity check).

Exit codes:
    0  every test produced the expected result
    1  at least one unexpected result
"""

from __future__ import annotations

import argparse
import socket
import sys
from dataclasses import dataclass
from typing import Iterable, List, Optional

import httpx


@dataclass
class TestResult:
    name: str
    ok: bool
    detail: str


def http_reachable(host: str, timeout: float = 5.0) -> TestResult:
    try:
        r = httpx.get(f"http://{host}", timeout=timeout)
        ok = r.status_code == 200
        return TestResult(
            "http/80 reachable",
            ok,
            f"HTTP {r.status_code}; first {len(r.text[:80])}B body",
        )
    except Exception as exc:  # noqa: BLE001 - want to surface error class
        return TestResult("http/80 reachable", False, f"{type(exc).__name__}: {exc}")


def tcp_port_open(host: str, port: int, timeout: float = 3.0) -> bool:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    try:
        sock.connect((host, port))
        return True
    except (socket.timeout, ConnectionRefusedError, OSError):
        return False
    finally:
        sock.close()


def ssh_reachable(host: str, timeout: float = 3.0) -> TestResult:
    # We don't authenticate — just confirm the port is open from our perspective.
    open_ = tcp_port_open(host, 22, timeout)
    return TestResult(
        "ssh/22 reachable from this host",
        open_,
        "port open" if open_ else "port filtered (expected if your IP is not in ssh_cidr_blocks)",
    )


def other_ports_closed(host: str, ports: Iterable[int] = (23, 3389, 8080)) -> List[TestResult]:
    out = []
    for p in ports:
        is_open = tcp_port_open(host, p, timeout=2.0)
        out.append(TestResult(
            f"tcp/{p} closed",
            not is_open,
            "closed (expected)" if not is_open else "OPEN (UNEXPECTED)",
        ))
    return out


def run_all(host: str) -> List[TestResult]:
    results: List[TestResult] = []
    results.append(http_reachable(host))
    results.append(ssh_reachable(host))
    results.extend(other_ports_closed(host))
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--host", required=True, help="Public IP or DNS of the test client.")
    args = parser.parse_args()

    results = run_all(args.host)
    print(f"Test results for {args.host}:")
    for r in results:
        marker = "PASS" if r.ok else "FAIL"
        print(f"  [{marker}] {r.name:40s} {r.detail}")
    return 0 if all(r.ok for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())
