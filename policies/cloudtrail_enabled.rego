package main

deny contains msg if {
    not input.resource.aws_cloudtrail

    msg := "LOG-001: CloudTrail is not configured"
}