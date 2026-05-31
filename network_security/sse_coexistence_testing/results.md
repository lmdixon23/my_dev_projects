# Results — SSE Coexistence Testing

This file records the most recent run of `test_traffic.py` against the deployed test client. Re-run the harness after every Terraform change to keep this current.

## Latest run

_Not yet populated. After deploying with `terraform apply` and running:_

```bash
python sse_simulation/test_traffic.py --host <public_ip_or_dns>
```

_paste the harness output below._

## Template

```
Test results for <host>:
  [PASS] http/80 reachable                       HTTP 200; first 80B body
  [PASS] ssh/22 reachable from this host         port open
  [PASS] tcp/23 closed                           closed (expected)
  [PASS] tcp/3389 closed                         closed (expected)
  [PASS] tcp/8080 closed                         closed (expected)
```

## Interpretation

- All `PASS` -> the deployed configuration matches what `terraform/main.tf` declares and what `firewall_setup.sh` configures.
- A `FAIL` on `ssh/22 reachable` is expected if you run the harness from a machine whose IP is not in `ssh_cidr_blocks` — that's the point.
- A `FAIL` on any "closed" port means a service is exposed that shouldn't be; inspect the security group and `firewall_setup.sh` immediately.
