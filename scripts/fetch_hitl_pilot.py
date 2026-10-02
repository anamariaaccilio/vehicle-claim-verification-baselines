"""Fetch only the versioned public pilot receipt; no Kaggle credentials needed."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import urllib.request
import zipfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--receipt', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    receipt = json.loads(args.receipt.read_text())
    for item in receipt['files']:
        relative = Path(item['path'])
        if relative.is_absolute() or '..' in relative.parts:
            raise ValueError('Unsafe receipt path')
        target = args.output / relative
        if target.exists():
            content = target.read_bytes()
        else:
            if not item['url'].startswith('https://www.kaggle.com/api/v1/datasets/download/'):
                raise ValueError('Expected public Kaggle dataset URL')
            with urllib.request.urlopen(item['url'], timeout=60) as response:
                content = response.read(item['bytes'] + 1024 * 1024)
            if zipfile.is_zipfile(io.BytesIO(content)):
                with zipfile.ZipFile(io.BytesIO(content)) as archive:
                    entries = archive.infolist()
                    if len(entries) != 1 or entries[0].filename != relative.name or entries[0].file_size != item['bytes']:
                        raise ValueError('Unexpected single-file archive')
                    content = archive.read(entries[0])
        if len(content) != item['bytes'] or hashlib.sha256(content).hexdigest() != item['sha256']:
            raise ValueError(f'Integrity mismatch: {relative}; existing files are never overwritten')
        if not target.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open('xb') as stream:
                stream.write(content)
    print(f"Verified {len(receipt['files'])} files against SHA256 receipt")


if __name__ == '__main__':
    main()
