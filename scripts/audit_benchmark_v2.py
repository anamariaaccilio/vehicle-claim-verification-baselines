"""Generate reproducible local visual QA and scientific diagnostics for frozen v2."""
import json
from pathlib import Path
import sys
import yaml
ROOT=Path(__file__).resolve().parents[1]
REPORTS=ROOT/'reports'      # salida regenerable, fuera de git (ver .gitignore)
DATA_QA=ROOT/'data/qa'      # mediciones que el demo y otros scripts leen
sys.path.insert(0,str(ROOT))
from src.data.benchmark_qa import run_qa
import cv2
cv2.setNumThreads(1)
if __name__=='__main__':
    result=run_qa(ROOT,ROOT/'data/manifests/benchmark_v2',yaml.safe_load((ROOT/'configs/benchmark_v2.yaml').read_text()),REPORTS,DATA_QA)
    print(json.dumps({'c2':len(result['c2']),'narrative_unique':result['narrative']['unique_nonempty'],'gallery':'reports/benchmark_v2_qa.html'}))
