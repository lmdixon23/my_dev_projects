# SSE Coexistence Testing

## Overview

**SSE_Coexistence_Testing** provisions a hardened AWS test environment for verifying that Security Service Edge (SSE) controls coexist correctly with a basic firewall (UFW) and a Global Secure Access (GSA) style egress posture. Terraform brings up a VPC, public subnet, security group, and EC2 test client; cloud-init installs Apache and configures UFW to default-deny inbound traffic; a Python reachability harness then verifies the expected open / closed ports against the deployed host.

## Key Features

- **Hardened Terraform**: SSH ingress is constrained to operator-specified CIDRs (a precondition guard rejects `0.0.0.0/0`), the AMI is looked up dynamically rather than hardcoded, IMDSv2 is required, the EBS root volume is encrypted, and every resource is tagged with `Project = sse-coex` for cost tracking and cleanup.
- **Idempotent EC2 Bootstrap**: `firewall_setup.sh` runs under `set -euo pipefail`, installs and starts Apache, enables UFW with default-deny inbound, and allows only `22/tcp` + `80/tcp`. Safe to re-run.
- **Reachability Harness**: `test_traffic.py` probes HTTP/80, SSH/22, and a sample of attack-surface ports (23 / 3389 / 8080), exiting non-zero on any unexpected result. Works as a CI smoke test or a post-deploy check.
- **Real Unit Tests**: Mocked-socket and mocked-httpx tests cover the harness's result-building logic in CI without flaky network calls.
- **Documented Scenarios**: `sse_simulation/test_scenarios.md` enumerates the three reachability scenarios and the manual step required to prove negative reachability for SSH.
- **CI Integration**: A repo-level GitHub Actions workflow runs `terraform validate` on every push.

## Architecture

Three-layer separation: declarative infra (Terraform), in-instance bootstrap (bash + UFW), and post-deploy verification (Python harness + tests).

```
terraform/
  main.tf                  VPC, IGW, subnet, route table, security group, EC2
  variables.tf             Inputs incl. required ssh_cidr_blocks + key_name
  outputs.tf               instance_public_ip / public_dns / ssh_command
  terraform.tfvars.example Template for the operator's tfvars (not committed)
sse_simulation/
  firewall_setup.sh        Idempotent UFW + Apache bootstrap
  test_traffic.py          Reachability harness with exit codes
  test_scenarios.md        Scenario / probe / expected-outcome catalog
  requirements.txt
  tests/test_test_traffic.py  Mock-network tests for the harness
results.md                 Latest harness output goes here
```

## Example Usage

After running the project, you can observe the following sequence of operations:

- **Provision**: `terraform apply` brings up the VPC, subnet, SG, and EC2 instance using the latest Ubuntu 22.04 LTS AMI in the chosen region.
- **Bootstrap**: cloud-init runs `firewall_setup.sh` on the instance, installs Apache, and enables UFW with default-deny inbound + allow on 22/80.
- **Verify**: `test_traffic.py --host <ip>` confirms HTTP/80 is reachable, SSH/22 is reachable from the operator IP, and the sample of attack-surface ports is closed.
- **Iterate**: change a security-group rule, re-apply, re-run the harness; the diff in `results.md` is the audit trail.

## Getting Started

### Prerequisites

- **AWS account** with credentials available to the AWS CLI / Terraform (`aws configure` or environment variables).
- **Terraform 1.6+**.
- **An existing EC2 key pair** in the target region (see `terraform.tfvars.example` for the `aws ec2 create-key-pair` command). **Do not commit the resulting `.pem` to the repository.**
- **Python 3.10+** for the verification harness.

### Installation

Clone the repository and navigate to the project directory:

```bash
git clone https://github.com/lmdixon23/my_dev_projects.git
cd my_dev_projects/network_security/sse_coexistence_testing

# Set up the Python harness
pip install -r sse_simulation/requirements.txt

# Configure Terraform inputs
cd terraform
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars: set ssh_cidr_blocks to YOUR IP only, and key_name to your AWS key.
```

### Running

```bash
# 1. Provision
cd terraform
terraform init
terraform apply
PUBLIC_IP=$(terraform output -raw instance_public_ip)

# 2. Verify
cd ..
python sse_simulation/test_traffic.py --host "$PUBLIC_IP"

# 3. Teardown when done (avoid AWS charges)
cd terraform
terraform destroy
```

### Testing

```bash
# Harness unit tests (no AWS, no network)
python -m pytest sse_simulation/tests/

# Terraform syntax / type-checking (no AWS calls)
cd terraform
terraform init -backend=false
terraform validate
```

## Technical Specifications

- **IaC**: Terraform 1.6+ with the `hashicorp/aws` ~> 5.0 provider
- **Compute**: EC2 `t3.micro` (configurable), Ubuntu 22.04 LTS (looked up at apply-time)
- **Networking**: dedicated VPC (`10.0.0.0/16`), public subnet, IGW, default route
- **Security group**: SSH/22 restricted to operator CIDRs, HTTP/80 configurable (default open), egress unrestricted
- **Instance hardening**: IMDSv2 required, EBS root encrypted
- **Verification**: Python 3.10+ harness using `httpx` + stdlib `socket`
- **Test Coverage**: 5 tests across one file with mocked network primitives

## What This Project Demonstrates

- **Defense-in-depth at infra time**: explicit Terraform precondition rejecting `0.0.0.0/0` for SSH, IMDSv2 required, root EBS encrypted, and every resource tagged for cost/cleanup. These are the AWS-CIS "easy wins" that audits look for.
- **Dynamic AMI lookup** instead of hardcoded image IDs. The original config had a stale AMI that broke any deploy outside the original developer's session.
- **Verification as code**: the reachability harness is structured, testable, and exits non-zero on unexpected results — not a one-shot script with a hardcoded IP at the bottom.
- Clean separation between infra, bootstrap, and verification, with each layer independently runnable and testable.
- **Honest scoping**: both the README and `test_scenarios.md` document the manual step required to prove negative reachability for SSH (run the harness from a non-allowlisted host).

## Scope

- This is a test environment. A production SSE deployment would integrate with an identity provider, a real SSE vendor's gateway (Zscaler / Netskope / iboss), and forward proxy logging — none of which is in scope here.
- Single AZ, no autoscaling, no load balancer; the harness assumes one well-known public IP.
- No deep packet inspection or TLS termination — only L3/L4 reachability is verified.
- No CIS-Benchmark scanning step (e.g., `prowler`) is wired in; adding one is roughly 20 lines of CI.

## Future Enhancements

1. **Compliance Scan in CI**: Wire `prowler` or `checkov` into the GitHub workflow. Scope estimates ~20 lines; cheapest item and the highest-signal one for a security portfolio, so it leads.
2. **TLS + Domain Filtering**: Add `mod_ssl` to Apache, a free ACM cert, and a domain-based UFW rule using `ufw-extras` or `nft` patterns — moves verification past L3/L4 reachability.
3. **Multi-Region Drift Test**: Apply the existing Terraform module across two AWS regions and run the harness from each to detect region-specific routing surprises.
4. **Real SSE Vendor Integration**: Add a Terraform module that points the EC2 instance's egress at a Zscaler / Netskope ZIA forwarder and verify the bypass / steer rules. (Lowest priority — heaviest, and needs a paid vendor account; the project's value is the harness itself.)

Licensed under the [MIT License](https://github.com/lmdixon23/my_dev_projects/blob/main/LICENSE).
