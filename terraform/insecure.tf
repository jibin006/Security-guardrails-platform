# S3 missing encryption (S3-001)
resource "aws_s3_bucket" "demo" {
  bucket = "my-demo-bucket"
}

# Hardcoded credential (SECRET-001 via detect-secrets)
variable "access_key" {
  default = "AKIAIOSFODNN7EXAMPLE"
}

# S3-002 — Public read access
resource "aws_s3_bucket" "public_bucket" {
  bucket = "my-public-bucket"
  acl    = "public-read"
}

# IAM-001 — Wildcard IAM policy
resource "aws_iam_policy" "wildcard_policy" {
  name = "dangerously-permissive-policy"
  policy = jsonencode({
    Statement = [
      {
        Effect   = "Allow"
        Action   = "*"
        Resource = "*"
      }
    ]
  })
}

# IAM-002 — Root access key
resource "aws_iam_access_key" "root_key" {
  id   = "AKIAROOTEXAMPLE12345"
  user = "root"
}

# SG-001 — SSH open to internet
resource "aws_security_group" "open_ssh" {
  name = "open-ssh-sg"
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# LOG-001 — No aws_cloudtrail resource intentionally omitted