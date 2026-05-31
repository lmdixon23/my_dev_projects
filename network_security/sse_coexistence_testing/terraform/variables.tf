variable "aws_region" {
  description = "The AWS region to deploy the infrastructure."
  type        = string
  default     = "us-west-2"
}

variable "availability_zone" {
  description = "Availability zone for the public subnet. Defaults to <region>a."
  type        = string
  default     = "us-west-2a"
}

variable "instance_type" {
  description = "The EC2 instance type."
  type        = string
  default     = "t3.micro"
}

variable "ssh_cidr_blocks" {
  description = "Source CIDRs allowed to SSH into the test client. Must NOT be 0.0.0.0/0. Set to your administrative IP, e.g. [\"203.0.113.4/32\"]."
  type        = list(string)
  # No default: forcing the operator to set this on each run prevents
  # the original sin of leaving SSH open to the world.
}

variable "http_cidr_blocks" {
  description = "Source CIDRs allowed to reach HTTP/80 on the test client."
  type        = list(string)
  default     = ["0.0.0.0/0"]
}

variable "key_name" {
  description = "Name of an existing EC2 key pair in the target region. Required to SSH in. Do NOT commit the private key to the repo."
  type        = string
}

variable "project_name" {
  description = "Tag prefix applied to every resource for cost tracking and cleanup."
  type        = string
  default     = "sse-coex"
}
