terraform {
  required_version = ">= 1.6"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
  default_tags {
    tags = {
      Project = var.project_name
      Owner   = "lmdixon23"
    }
  }
}

# ---- AMI lookup -------------------------------------------------------- #
# Look up the latest Ubuntu 22.04 LTS AMI in the chosen region instead of
# hardcoding an AMI ID that goes stale every release cycle.
data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"] # Canonical

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

# ---- Networking -------------------------------------------------------- #
resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  tags = { Name = "${var.project_name}-vpc" }
}

resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id
  tags   = { Name = "${var.project_name}-igw" }
}

resource "aws_subnet" "public" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.1.0/24"
  availability_zone       = var.availability_zone
  map_public_ip_on_launch = true
  tags                    = { Name = "${var.project_name}-public-subnet" }
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }

  tags = { Name = "${var.project_name}-public-rt" }
}

resource "aws_route_table_association" "public" {
  subnet_id      = aws_subnet.public.id
  route_table_id = aws_route_table.public.id
}

# ---- Security group ---------------------------------------------------- #
# Validation guard: ssh_cidr_blocks must NEVER be the public internet.
resource "null_resource" "ssh_cidr_guard" {
  lifecycle {
    precondition {
      condition = !contains(var.ssh_cidr_blocks, "0.0.0.0/0")
      error_message = "ssh_cidr_blocks must not contain 0.0.0.0/0. Set it to your administrative IP."
    }
  }
}

resource "aws_security_group" "allow_ssh_http" {
  name        = "${var.project_name}-allow-ssh-http"
  description = "Allow SSH from operator and HTTP from configured sources"
  vpc_id      = aws_vpc.main.id

  ingress {
    description = "SSH from operator-specified CIDRs only"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = var.ssh_cidr_blocks
  }

  ingress {
    description = "HTTP from configured sources"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = var.http_cidr_blocks
  }

  egress {
    description = "All egress allowed"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Name = "${var.project_name}-sg" }
}

# ---- EC2 test client --------------------------------------------------- #
resource "aws_instance" "test_client" {
  ami                    = data.aws_ami.ubuntu.id
  instance_type          = var.instance_type
  subnet_id              = aws_subnet.public.id
  vpc_security_group_ids = [aws_security_group.allow_ssh_http.id]
  key_name               = var.key_name

  user_data = file("${path.module}/../sse_simulation/firewall_setup.sh")

  metadata_options {
    # Require IMDSv2 — the basic AWS-CIS hardening control. The old
    # config didn't set this so the instance was vulnerable to the
    # standard IMDSv1 SSRF -> credential-theft chain.
    http_tokens = "required"
  }

  root_block_device {
    encrypted = true
  }

  tags = { Name = "${var.project_name}-test-client" }
}
