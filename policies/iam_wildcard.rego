package main

deny contains msg if {
    policy := input.resource.aws_iam_policy[_]

    statement := policy.policy.Statement[_]

    statement.Action == "*"

    msg := sprintf(
        "IAM-001: IAM policy '%v' contains wildcard action",
        [policy.name]
    )
}