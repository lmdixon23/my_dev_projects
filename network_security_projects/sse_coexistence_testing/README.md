# SSE Coexistence Testing Project

## Overview

This project sets up a test environment to simulate coexistence between a Security Service Edge (SSE) solution and a Global Secure Access (GSA) environment using Terraform and a basic firewall simulation with pfSense.

The project provisions an AWS infrastructure using Terraform and runs traffic tests to validate that the SSE solution allows or blocks traffic based on firewall rules.

## Prerequisites

- AWS CLI and AWS account with necessary permissions
- Terraform installed
- Python 3.x installed
- Basic understanding of security service edge (SSE) solutions

## Project Structure

- **terraform/**: Contains Terraform scripts for provisioning AWS infrastructure.
- **sse_simulation/**: Contains scripts and test cases for simulating firewall rules and traffic.
- **docs/**: Contains project documentation and test results.

## Setup Guide

1. Clone the repository.
   ```bash
   git clone https://github.com/your-username/sse_coexistence_testing.git
   cd sse_coexistence_testing/terraform
   ```

## Firewall Setup

This project uses **UFW (Uncomplicated Firewall)** on the EC2 instance to simulate basic firewall rules. The `firewall_setup.sh` script installs Apache to simulate a web server and configures UFW to allow traffic on port 22 (SSH) and port 80 (HTTP).

### Running the Firewall Setup

1. SSH into your EC2 instance.
2. Run the following command to execute the firewall setup script:
   ```bash
   ./firewall_setup.sh
   ```