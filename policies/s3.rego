package main

deny contains msg if {
    resource := input.resource.aws_s3_bucket[_]

    not resource.server_side_encryption_configuration

    msg := sprintf(
        "S3-001: S3 bucket '%v' missing encryption configuration",
        [resource.bucket]
    )
}