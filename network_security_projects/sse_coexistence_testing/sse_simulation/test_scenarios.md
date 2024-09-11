# Test Scenarios for SSE Coexistence Testing

### 1. HTTP Traffic Test
- **Objective**: Verify that HTTP traffic can pass through the firewall (UFW) without any issues.
- **Steps**:
  1. Deploy the EC2 instance with a basic web server (Apache).
  2. Simulate traffic by accessing the server via its public IP using the Python script `test_traffic.py`.
  3. Check whether HTTP access is successful.
- **Expected Outcome**: HTTP access to the server should be allowed, and the test should pass.

### 2. Firewall Rules Test
- **Objective**: Ensure that UFW firewall (or the pfSense) blocks all ports except port 80.
- **Steps**:
  1. Use SSH to connect to the EC2 instance.
  2. Ensure the firewall is configured to allow only HTTP (port 80) traffic.
  3. Attempt to access other ports (e.g., port 22) and verify they are blocked.
- **Expected Outcome**: Access should be blocked on all ports except port 80.