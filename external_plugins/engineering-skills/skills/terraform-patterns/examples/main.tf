# main.tf — Terraform config with deliberate security issues
#
# This Terraform configuration contains common security anti-patterns
# for the terraform-patterns skill scanner to detect:
#   - Overly permissive CIDR blocks (0.0.0.0/0)
#   - Public S3 bucket
#   - Missing encryption (EBS, RDS, S3)
#   - Hardcoded credentials
#   - No logging or monitoring
#   - Overly broad IAM policies
#   - Missing tags
#   - Default VPC usage

terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "us-east-1"
  # SECURITY ISSUE: hardcoded credentials
  access_key = "AKIAIOSFODNN7EXAMPLE"
  secret_key = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
}

# SECURITY ISSUE: security group allows all inbound traffic
resource "aws_security_group" "web" {
  name        = "web-sg"
  description = "Web server security group"

  ingress {
    description = "SSH from anywhere"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]  # ISSUE: SSH open to the world
  }

  ingress {
    description = "HTTP"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "HTTPS"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "Database"
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]  # ISSUE: DB port open to the world
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# SECURITY ISSUE: public S3 bucket with no encryption
resource "aws_s3_bucket" "data" {
  bucket = "acme-corp-customer-data"
  # ISSUE: no tags
}

resource "aws_s3_bucket_public_access_block" "data" {
  bucket = aws_s3_bucket.data.id

  # ISSUE: public access not blocked
  block_public_acls       = false
  block_public_policy     = false
  ignore_public_acls      = false
  restrict_public_buckets = false
}

# ISSUE: no server-side encryption configured
# (missing: aws_s3_bucket_server_side_encryption_configuration)

# ISSUE: no versioning enabled
# (missing: aws_s3_bucket_versioning)

# ISSUE: no access logging
# (missing: aws_s3_bucket_logging)

# SECURITY ISSUE: EC2 instance with no encryption, public IP, no IMDSv2
resource "aws_instance" "web" {
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = "t3.large"

  vpc_security_group_ids = [aws_security_group.web.id]

  associate_public_ip_address = true  # ISSUE: public IP assigned

  # ISSUE: no encryption on root volume
  root_block_device {
    volume_size = 50
    volume_type = "gp3"
    encrypted   = false  # ISSUE: unencrypted EBS
  }

  # ISSUE: no IMDSv2 enforcement
  # (missing: metadata_options { http_tokens = "required" })

  # ISSUE: user data with inline secrets
  user_data = <<-EOF
    #!/bin/bash
    echo "DB_PASSWORD=pr0duct10n_s3cret" >> /etc/environment
    echo "API_KEY=sk-live-abc123def456" >> /etc/environment
  EOF

  # ISSUE: no tags
}

# SECURITY ISSUE: RDS with no encryption, public access, weak password
resource "aws_db_instance" "main" {
  identifier     = "acme-production-db"
  engine         = "postgres"
  engine_version = "15.4"
  instance_class = "db.t3.medium"

  allocated_storage = 100
  storage_type      = "gp3"

  db_name  = "acme_production"
  username = "admin"
  password = "admin123"  # ISSUE: weak hardcoded password

  publicly_accessible = true   # ISSUE: database publicly accessible
  storage_encrypted   = false  # ISSUE: storage not encrypted

  skip_final_snapshot       = true  # ISSUE: no final snapshot on deletion
  backup_retention_period   = 0     # ISSUE: no automated backups

  # ISSUE: no multi-AZ for production
  multi_az = false

  # ISSUE: no tags
}

# SECURITY ISSUE: overly permissive IAM policy
resource "aws_iam_role" "app" {
  name = "acme-app-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "ec2.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy" "app" {
  name = "acme-app-policy"
  role = aws_iam_role.app.id

  # ISSUE: wildcard permissions — grants full access to everything
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = "*"
      Resource = "*"
    }]
  })
}
