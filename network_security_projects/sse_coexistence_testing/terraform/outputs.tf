output "vpc_id" {
  description = "The ID of the VPC."
  value       = aws_vpc.main_vpc.id
}

output "instance_public_ip" {
  description = "The public IP of the test client instance."
  value       = aws_instance.test_client.public_ip
}