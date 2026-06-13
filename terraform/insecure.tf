resource "aws_s3_bucket" "demo" {
  bucket = "my-demo-bucket"
}

# Intentional violation for demo purposes
variable "access_key" {
  default = "AKIAIOSFODNN7EXAMPLE"
}