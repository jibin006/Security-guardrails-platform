import yaml
import sys
from datetime import date

def validate_suppressions(suppression_file):
    with open(suppression_file) as f:
        data = yaml.safe_load(f)

    suppressions = data.get("suppressions", [])
    required_fields = ["id", "owner", "reason", "expiry", "approver", "ticket"]
    
    errors = []
    valid = {}

    print(f"\n[SUPPRESSION] Validating {len(suppressions)} suppression(s)\n")

    for supp in suppressions:
        supp_id = supp.get("id", "UNKNOWN")
        
        # Check required fields
        missing = [f for f in required_fields if not supp.get(f)]
        if missing:
            errors.append(f"{supp_id}: Missing required fields: {missing}")
            continue

        # Check expiry
        try:
            expiry = date.fromisoformat(supp["expiry"])
        except ValueError:
            errors.append(f"{supp_id}: Invalid expiry date format. Use YYYY-MM-DD")
            continue

        if expiry < date.today():
            errors.append(
                f"{supp_id}: Suppression expired on {supp['expiry']}. "
                f"Renew or remove suppression entry."
            )
            continue

        # Valid suppression
        days_remaining = (expiry - date.today()).days
        print(f"  [VALID] {supp_id}")
        print(f"    Owner:    {supp['owner']}")
        print(f"    Approver: {supp['approver']}")
        print(f"    Expires:  {supp['expiry']} ({days_remaining} days remaining)")
        print(f"    Reason:   {supp['reason'][:60].strip()}...")
        print()
        
        valid[supp_id] = supp

    if errors:
        print("\n[FAIL] Suppression validation errors:\n")
        for err in errors:
            print(f"  ERROR: {err}")
        sys.exit(1)

    print(f"[PASS] All suppressions valid")
    return valid


if __name__ == "__main__":
    valid = validate_suppressions("suppressions/suppressions.yaml")
    
    import json
    with open("findings/valid_suppressions.json", "w") as f:
        json.dump(list(valid.keys()), f)

def load_suppressions():
    try:
        with open("findings/valid_suppressions.json") as f:
            content = f.read().strip()

            if not content:
                print("[WARN] valid_suppressions.json is empty")
                return []

            return json.loads(content)

    except FileNotFoundError:
        print("[WARN] valid_suppressions.json not found")
        return []        