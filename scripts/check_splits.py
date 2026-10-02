"""Usage: python scripts/check_splits.py --manifest FILE --group-key KEY --split-key KEY."""
import argparse
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.data.split_audit import audit_rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--group-key", default="source_image_id")
    parser.add_argument("--split-key", default="split")
    args = parser.parse_args()
    try:
        raw = args.manifest.read_bytes()
        rows = [json.loads(line) for line in raw.decode("utf-8").splitlines() if line.strip()]
        audits = [audit_rows(rows, args.group_key, args.split_key)]
        # Only audit additional identifiers actually present; incomplete IDs fail closed.
        for key in ("claim_id", "incident_id", "vehicle_id", "policy_id"):
            if key != args.group_key and any(key in row for row in rows):
                audits.append(audit_rows(rows, key, args.split_key))
        report = {"manifest": str(args.manifest), "sha256": hashlib.sha256(raw).hexdigest(),
                  "audits": audits}
        print(json.dumps(report, indent=2))
        return int(any(a["result"] != "PASS" for a in audits))
    except (OSError, ValueError, TypeError, AttributeError) as exc:
        print(json.dumps({"result": "ERROR", "reason": str(exc)}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
