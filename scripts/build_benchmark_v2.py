"""Build/check all authorized controlled conditions; no model execution."""
import argparse
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src.data.benchmark_v2 import build,check

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config',type=Path,default=ROOT/'configs/benchmark_v2.yaml')
    parser.add_argument('--output',type=Path,default=ROOT/'data/manifests/benchmark_v2')
    parser.add_argument('--check',action='store_true')
    parser.add_argument('--verify-images',action='store_true')
    args=parser.parse_args()
    result=check(ROOT,args.config,args.output,args.verify_images) if args.check else build(ROOT,args.config,args.output)
    print(json.dumps(result,indent=2))
if __name__=='__main__': main()
