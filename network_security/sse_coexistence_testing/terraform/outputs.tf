output "vpc_id" {
  description = "ID of the project VPC."
  value       = aws_vpc.main.id
}

output "instance_id" {
  description = "ID of the EC2 test-client instance."
  value       = aws_instance.test_client.id
}

output "instance_public_ip" {
  description = "Public IP of the EC2 test-client instance."
  value       = aws_instance.test_client.public_ip
}

output "instance_public_dns" {
  description = "Public DNS name of the EC2 test-client instance."
  value       = aws_instance.test_client.public_dns
}

output "ssh_command" {
  description = "Convenience SSH command (paths assume your private key is locally placed)."
  value       = "ssh -i ~/.ssh/${var.key_name}.pem ubuntu@${aws_instance.test_client.public_dns}"
}
