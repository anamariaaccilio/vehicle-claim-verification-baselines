"""Build or verify the canonical controlled-claim benchmark; never train models."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.data.claim_benchmark import build_benchmark, validate_bundle


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, default=ROOT/'configs/benchmark_v1.yaml')
    parser.add_argument('--output', type=Path, default=ROOT/'data/manifests/benchmark_v1')
    parser.add_argument('--check', action='store_true')
    parser.add_argument('--verify-images', action='store_true', help='Requires acquired local raw data; rebuilds and verifies outputs')
    args = parser.parse_args()
    if args.check:
        result = validate_bundle(ROOT, args.output, args.config, verify_images=args.verify_images)
    else:
        result = build_benchmark(ROOT, args.config, args.output)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
