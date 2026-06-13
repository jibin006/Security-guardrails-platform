package main

deny contains msg if {
    key := input.resource.aws_iam_access_key[_]
    key.user == "root"
    msg := sprintf(
        "IAM-002: Root user access key '%v' must be deleted",
        [key.id]
    )
}