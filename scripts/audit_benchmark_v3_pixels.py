"""Verify every C3/C4/C5 image in candidate v3; human realism stays unreviewed."""
from pathlib import Path
import json,sys,yaml,cv2
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src.data.benchmark_qa import manipulation_audit,table
from src.data.benchmark_v3 import paired_narrative
from src.data.claim_benchmark import canonical
if __name__=='__main__':
    cv2.setNumThreads(1)
    bundle=ROOT/'data/manifests/benchmark_v3'
    claims=[json.loads(line) for line in (bundle/'manifest.jsonl').read_text().splitlines()]
    audit=json.loads((bundle/'dataset_audit.json').read_text());sources={s['source_image_id']:s for s in audit['sources']}
    results=manipulation_audit(ROOT,claims,sources,yaml.safe_load((ROOT/'configs/benchmark_v3.yaml').read_text()),paired_narrative)
    names={'C3':'C3_FORENSIC_AUDIT','C4':'C4_INPAINT_AUDIT','C5':'C5_COMBINED_AUDIT'}
    for condition,rows in results.items():
        (ROOT/(names[condition]+'_V3.md')).write_text(f'# {condition} pixel audit — v3\n\nTodas las filas verificadas contra archivos reales y operador regenerado.\nSmall area: <0.5%; large area: >20%; alertas, no decisiones automáticas de realismo.\nRevisión humana: NOT PERFORMED.\n\n'+table(rows,list(rows[0])))
        base=ROOT/(names[condition]+'.md');text=base.read_text().split('\n## Ampliación v3')[0]
        base.write_text(text+f'\n## Ampliación v3\n\n{len(rows)} casos revisados automáticamente; tabla completa en {names[condition]}_V3.md.\n')
        if not all(r['mask_nonempty'] and r['dimensions_match'] and r['changed_pixels']>0 and r['outside_mask_changed_pixels']==0 and r['reproducible'] and r['mask_sha_matches'] for r in rows):raise ValueError(f'{condition}: integrity failure')
        if condition=='C4' and not all(r['mask_matches_annotation'] for r in rows):raise ValueError('C4 annotation mask mismatch')
        if condition=='C5' and not all(r['semantic_contradiction_annotation_supported'] and r['visual_manipulation_verified'] for r in rows):raise ValueError('C5 independent checks failed')
    (ROOT/'qa_v3_pixels.json').write_bytes(canonical(results))
    print(json.dumps({k:{'rows':len(v),'small_area_flags':sum(r['small_area_flag'] for r in v),'all_reproducible':all(r['reproducible'] for r in v)} for k,v in results.items()},indent=2))
