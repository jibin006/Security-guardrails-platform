import json

# Simulates parsed Terraform plan for Conftest
# Mirrors all intentionally vulnerable resources in insecure.tf

terraform_config = {
    "resource": {

        # S3-001 — Missing encryption
        "aws_s3_bucket": {
            "demo": {
                "bucket": "my-demo-bucket"
            },
            # S3-002 — Public read access
            "public_bucket": {
                "bucket": "my-public-bucket",
                "acl": "public-read"
            }
        },

        # IAM-001 — Wildcard action in policy
        "aws_iam_policy": {
            "wildcard_policy": {
                "name": "dangerously-permissive-policy",
                "policy": {
                    "Statement": [
                        {
                            "Effect": "Allow",
                            "Action": "*",
                            "Resource": "*"
                        }
                    ]
                }
            }
        },

        # IAM-002 — Root access key
        "aws_iam_access_key": {
            "root_key": {
                "id": "AKIAROOTEXAMPLE12345",
                "user": "root"
            }
        },

        # SG-001 — SSH open to internet
        "aws_security_group": {
            "open_ssh": {
                "name": "open-ssh-sg",
                "ingress": [
                    {
                        "from_port": 22,
                        "to_port": 22,
                        "protocol": "tcp",
                        "cidr_blocks": ["0.0.0.0/0"]
                    }
                ]
            }
        }

        # LOG-001 fires because aws_cloudtrail is intentionally absent
    }
}

with open("terraform/plan.json", "w") as f:
    json.dump(terraform_config, f, indent=2)

print("Terraform plan.json generated")
print(f"Resources: {list(terraform_config['resource'].keys())}")