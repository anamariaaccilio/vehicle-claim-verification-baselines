"""Build/check QA revision without changing v2 or training any models."""
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src.data.benchmark_v3 import build,check
import cv2
cv2.setNumThreads(1)  # Parallelize independent sources instead of tiny CV kernels.
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--config',type=Path,default=ROOT/'configs/benchmark_v3.yaml')
    p.add_argument('--output',type=Path,default=ROOT/'data/manifests/benchmark_v3')
    p.add_argument('--check',action='store_true');p.add_argument('--verify-images',action='store_true')
    a=p.parse_args();print(json.dumps(check(ROOT,a.config,a.output,a.verify_images) if a.check else build(ROOT,a.config,a.output),indent=2))
