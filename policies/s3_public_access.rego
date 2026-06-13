package main

deny contains msg if {
    bucket := input.resource.aws_s3_bucket[_]

    bucket.acl == "public-read"

    msg := sprintf(
        "S3-002: S3 bucket '%v' allows public read access",
        [bucket.bucket]
    )
}