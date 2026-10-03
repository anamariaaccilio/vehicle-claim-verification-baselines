"""Acquire the complete public damage subset by ZIP ranges, no credentials.

The misleading folder names are resolved using meta.json taxonomy, not names.
Images and annotations only: redundant segmentation raster exports are not needed.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor,as_completed
import hashlib
import io
import json
from pathlib import Path
import struct
import time
import urllib.request
import zipfile
import zlib

URL='https://www.kaggle.com/api/v1/datasets/download/humansintheloop/car-parts-and-car-damages?datasetVersionNumber=2'
ROOT=Path(__file__).resolve().parents[1]

class RemoteZip(io.RawIOBase):
    def __init__(self):
        request=urllib.request.Request(URL,headers={'Range':'bytes=-65536'})
        with urllib.request.urlopen(request,timeout=60) as response:
            if response.status!=206: raise ValueError('Server does not support selective range download')
            self.url=response.geturl()  # Ephemeral signed redirect; never persisted or logged.
            self.size=int(response.headers['Content-Range'].split('/')[-1]);self.tail=response.read();self.position=0
    def seekable(self): return True
    def readable(self): return True
    def tell(self): return self.position
    def seek(self,offset,whence=0):
        self.position=offset if whence==0 else self.position+offset if whence==1 else self.size+offset
        return self.position
    def read(self,n=-1):
        n=self.size-self.position if n<0 else min(n,self.size-self.position)
        if n<=0:return b''
        if self.position>=self.size-len(self.tail):
            start=self.position-(self.size-len(self.tail));data=self.tail[start:start+n]
        else: data=self.range(self.position,self.position+n-1)
        self.position+=len(data);return data
    def range(self,start,end):
        for attempt in range(3):
            try:
                request=urllib.request.Request(self.url,headers={'Range':f'bytes={start}-{end}'})
                with urllib.request.urlopen(request,timeout=60) as response:
                    if response.status!=206 or not response.headers.get('Content-Range','').startswith(f'bytes {start}-'):
                        raise ValueError('Server returned an unexpected byte range')
                    content=response.read(end-start+2)
                    if len(content)!=end-start+1:raise ValueError('Incomplete or excessive range')
                    return content
            except Exception:
                if attempt==2:raise
                time.sleep(attempt+1)
    def entry(self,item):
        # ZIP64 extras are allowed; next header gives exact bounded entry length.
        raw=self.range(item['offset'],item['end']-1)
        if raw[:4]!=b'PK\x03\x04':raise ValueError('Invalid local ZIP header')
        name_len,extra_len=struct.unpack_from('<HH',raw,26)
        name=raw[30:30+name_len].decode('utf-8')
        if name!=item['path']:raise ValueError('ZIP name mismatch')
        start=30+name_len+extra_len;compressed=raw[start:start+item['compressed']]
        content=zlib.decompress(compressed,-15) if item['method']==8 else compressed if item['method']==0 else None
        if content is None or len(content)!=item['bytes'] or zlib.crc32(content)!=item['crc']:raise ValueError('ZIP CRC/length failure')
        return content


def acquire(output,receipt,workers=6):
    remote=RemoteZip()
    with zipfile.ZipFile(remote) as archive:
        infos=sorted(archive.infolist(),key=lambda i:i.header_offset)
        rows=[{'path':i.filename,'bytes':i.file_size,'compressed':i.compress_size,'offset':i.header_offset,
               'end':infos[n+1].header_offset if n+1<len(infos) else archive.start_dir,'crc':i.CRC,'method':i.compress_type}
              for n,i in enumerate(infos)]
    from sys import path
    path.insert(0,str(ROOT))
    from src.schemas.evidence import HITL_TO_CANONICAL
    metadata={item['path']:json.loads(remote.entry(item)) for item in rows if item['path'].count('/')==1 and item['path'].endswith('/meta.json')}
    damage_roots=[name.split('/')[0] for name,doc in metadata.items() if {c['title'] for c in doc['classes']}==set(HITL_TO_CANONICAL)]
    if len(damage_roots)!=1:raise ValueError('Ambiguous/missing damage taxonomy')
    prefix=damage_roots[0]+'/'
    selected=[item for item in rows if item['path'].startswith(prefix) and ('/img/' in item['path'] or '/ann/' in item['path'] or item['path']==prefix+'meta.json')]
    print(json.dumps({'archive_files':len(rows),'archive_bytes':remote.size,'damage_root':prefix,'selected_files':len(selected),
                      'selected_bytes':sum(i['bytes'] for i in selected),'images':sum('/img/' in i['path'] for i in selected)}),flush=True)
    output.mkdir(parents=True,exist_ok=True)
    def fetch(item):
        relative=Path(item['path'])
        if relative.is_absolute() or '..' in relative.parts:raise ValueError('Unsafe archive path')
        if item['bytes']>50_000_000:raise ValueError('Unexpected single-file size')
        target=output/relative
        content=target.read_bytes() if target.exists() else remote.entry(item)
        if len(content)!=item['bytes'] or zlib.crc32(content)!=item['crc']:raise ValueError(f'Integrity mismatch: {relative}')
        digest=hashlib.sha256(content).hexdigest()
        if not target.exists():
            target.parent.mkdir(parents=True,exist_ok=True)
            with target.open('xb') as stream:stream.write(content)
        return {'path':relative.as_posix(),'bytes':len(content),'sha256':digest,'archive_crc32':item['crc']}
    files=[];errors=[]
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures={executor.submit(fetch,item):item for item in selected}
        for index,future in enumerate(as_completed(futures),1):
            try:files.append(future.result())
            except Exception as exc:errors.append({'path':futures[future]['path'],'error':type(exc).__name__})
            if index%100==0:print(f'{index}/{len(selected)} checked; errors={len(errors)}',flush=True)
    if errors:
        (output/'acquisition_errors.json').write_text(json.dumps(errors,indent=2))
        raise ValueError(f'{len(errors)} acquisition errors; preserved successes; rerun is resumable')
    record={'dataset':'humansintheloop/car-parts-and-car-damages','version':2,'url':URL,'license':'CC0-1.0 as declared by author',
            'license_source':'https://humansintheloop.org/resources/datasets/car-parts-and-car-damages-dataset/',
            'selection':'Complete image+annotation pairs of root selected by exact damage taxonomy; redundant raster exports not downloaded',
            'archive_bytes':remote.size,'archive_files':len(rows),'remote_index_sha256':hashlib.sha256(json.dumps(rows,sort_keys=True).encode()).hexdigest(),
            'archive_image_counts':{prefix:sum('/img/' in row['path'] and row['path'].startswith(prefix+'/') for row in rows) for prefix in sorted(metadata_key.split('/')[0] for metadata_key in metadata)},
            'files':sorted(files,key=lambda f:f['path'])}
    content=json.dumps(record,ensure_ascii=False,indent=2)+'\n'
    if receipt.exists() and receipt.read_text()!=content:raise ValueError('Refusing to overwrite a different frozen receipt')
    receipt.write_text(content)
    (output/'remote_index.json').write_text(json.dumps(rows,sort_keys=True))
    print(f'PASS: {len(files)} files; receipt {receipt}',flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=ROOT/'data/raw/hitl_full_v2')
    parser.add_argument('--receipt',type=Path,default=ROOT/'data/hitl_full_receipt.json')
    parser.add_argument('--workers',type=int,default=6)
    args=parser.parse_args();acquire(args.output,args.receipt,args.workers)
