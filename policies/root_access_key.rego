package main

deny contains msg if {
    user := input.resource.aws_iam_user[_]

    lower(user.name) == "root"

    msg := sprintf(
        "IAM-002: Root user access key usage detected for '%v'",
        [user.name]
    )
}