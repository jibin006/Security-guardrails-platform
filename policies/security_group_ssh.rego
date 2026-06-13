package main

deny contains msg if {
    sg := input.resource.aws_security_group[_]

    ingress := sg.ingress[_]

    ingress.from_port == 22
    ingress.to_port == 22

    ingress.cidr_blocks[_] == "0.0.0.0/0"

    msg := sprintf(
        "SG-001: Security Group '%v' exposes SSH to the internet",
        [sg.name]
    )
}