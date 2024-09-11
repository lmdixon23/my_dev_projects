import requests

def test_http_access(public_ip):
    try:
        response = requests.get(f'http://{public_ip}')
        if response.status_code == 200:
            print(f"HTTP access test passed for {public_ip}.")
        else:
            print(f"HTTP access test failed for {public_ip}. Status code: {response.status_code}")
    except Exception as e:
        print(f"Failed to access {public_ip}: {e}")

if __name__ == "__main__":
    test_client_ip = "3.143.203.174"  # Replace with the instance's public IP
    test_http_access(test_client_ip)