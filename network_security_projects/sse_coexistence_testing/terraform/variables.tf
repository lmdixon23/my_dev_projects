variable "aws_region" {
  description = "The AWS region to deploy the infrastructure."
  default     = "us-west-2"
}

variable "instance_type" {
  description = "The EC2 instance type."
  default     = "t2.micro"
}