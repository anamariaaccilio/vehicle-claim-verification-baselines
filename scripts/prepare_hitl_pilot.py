"""Build an integration-only source manifest and split/duplicate audit."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from PIL import Image
import yaml
from src.data.hitl_supervisely import parse_hitl_supervisely
from src.data.split import apply_split
from src.data.split_audit import audit_rows
from src.schemas.claim import Split


def write_verified(path, content):
    if path.exists():
        if path.read_bytes() != content:
            raise ValueError(f'Refusing to overwrite different content: {path}')
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as stream:
        stream.write(content)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dataset-dir', required=True, type=Path)
    parser.add_argument('--manifest', required=True, type=Path)
    parser.add_argument('--audit', required=True, type=Path)
    parser.add_argument('--config', type=Path, default=Path(__file__).resolve().parents[1]/'configs/baseline.yaml')
    args = parser.parse_args()
    config = yaml.safe_load(args.config.read_text())
    records = parse_hitl_supervisely(args.dataset_dir, relative_to=Path.cwd())
    records = apply_split(records, seed=config['seed'], ratios={Split(k): v for k,v in config['split'].items()})
    rows, hashes = [], []
    for record in records:
        path = Path(record.path)
        with Image.open(path) as image:
            rgb = image.convert('RGB')
            pixel_hash = hashlib.sha256(str(rgb.size).encode() + b'\0' + rgb.tobytes()).hexdigest()
        file_hash = hashlib.sha256(path.read_bytes()).hexdigest()
        rows.append({'source_image_id': record.source_image_id, 'split': record.split.value,
                     'pixel_sha256': pixel_hash, 'file_sha256': file_hash})
        hashes.append({'path': record.path, 'file_sha256': file_hash, 'pixel_sha256': pixel_hash})
    audits = [audit_rows(rows, key) for key in ['source_image_id','file_sha256','pixel_sha256']]
    if any(audit['result'] != 'PASS' for audit in audits):
        raise ValueError('Cross-split source/image duplication detected; manifest was not written')
    content = ''.join(record.model_dump_json()+'\n' for record in records).encode()
    report = {'scope':'INTEGRATION PILOT ONLY; no claim benchmark or scientific test set',
              'seed':config['seed'], 'manifest':str(args.manifest),
              'manifest_sha256':hashlib.sha256(content).hexdigest(),
              'records':len(records), 'annotations':sum(len(r.annotations) for r in records),
              'class_instances':dict(sorted(Counter(ann.damage_class for r in records for ann in r.annotations).items())),
              'audits':audits, 'image_hashes':hashes,
              'limitations':['No near-duplicate audit yet', 'No real claim/incident/vehicle/policy IDs',
                             'Filename-based source IDs; shared car/incident independence not proven',
                             'Annotations are ground truth, never visual-specialist predictions']}
    write_verified(args.manifest, content)
    write_verified(args.audit, (json.dumps(report, indent=2)+'\n').encode())
    print(json.dumps({k:v for k,v in report.items() if k!='image_hashes'}, indent=2))


if __name__ == '__main__':
    main()
