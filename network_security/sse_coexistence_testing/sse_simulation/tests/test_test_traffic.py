"""Tests for `test_traffic` itself.

These don't touch real network endpoints — they mock `socket.socket` and
the httpx client so the test result-building logic is covered without
flaky DNS / network behavior in CI.
"""

import socket
import unittest
from unittest import mock

import httpx

import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import test_traffic as tt  # noqa: E402


class TestHttpReachable(unittest.TestCase):
    def test_returns_ok_on_200(self):
        def handler(_request):
            return httpx.Response(200, text="welcome")
        with mock.patch("test_traffic.httpx.get") as g:
            g.side_effect = lambda url, timeout: httpx.Response(200, text="welcome")
            r = tt.http_reachable("1.2.3.4")
        self.assertTrue(r.ok)
        self.assertIn("HTTP 200", r.detail)

    def test_marks_failure_on_exception(self):
        with mock.patch("test_traffic.httpx.get", side_effect=httpx.ConnectError("boom")):
            r = tt.http_reachable("1.2.3.4")
        self.assertFalse(r.ok)
        self.assertIn("ConnectError", r.detail)


class TestTcpPortOpen(unittest.TestCase):
    def test_open_when_connect_succeeds(self):
        fake_sock = mock.MagicMock()
        fake_sock.connect.return_value = None
        with mock.patch("test_traffic.socket.socket", return_value=fake_sock):
            self.assertTrue(tt.tcp_port_open("1.2.3.4", 22))

    def test_closed_when_refused(self):
        fake_sock = mock.MagicMock()
        fake_sock.connect.side_effect = ConnectionRefusedError()
        with mock.patch("test_traffic.socket.socket", return_value=fake_sock):
            self.assertFalse(tt.tcp_port_open("1.2.3.4", 22))


class TestRunAllAggregatesResults(unittest.TestCase):
    def test_returns_one_result_per_probe(self):
        with mock.patch("test_traffic.http_reachable", return_value=tt.TestResult("http", True, "ok")), \
             mock.patch("test_traffic.ssh_reachable", return_value=tt.TestResult("ssh", True, "ok")), \
             mock.patch("test_traffic.other_ports_closed", return_value=[
                 tt.TestResult("tcp/23 closed", True, ""),
                 tt.TestResult("tcp/3389 closed", True, ""),
                 tt.TestResult("tcp/8080 closed", True, ""),
             ]):
            results = tt.run_all("1.2.3.4")
        self.assertEqual(len(results), 5)
        self.assertTrue(all(r.ok for r in results))


if __name__ == "__main__":
    unittest.main()
