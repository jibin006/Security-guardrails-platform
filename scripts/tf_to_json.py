import json

# Simulates parsed Terraform for Conftest
terraform_config = {
    "resource": {
        "aws_s3_bucket": {
            "demo": {
                "bucket": "my-demo-bucket"
            }
        }
    }
}

with open("terraform/plan.json", "w") as f:
    json.dump(terraform_config, f, indent=2)

print("Terraform config converted to JSON")