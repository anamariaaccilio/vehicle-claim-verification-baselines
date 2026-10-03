"""Summarize measured QA for frozen v2 and candidate v3; never adjudicate labels."""
from collections import Counter
from pathlib import Path
import heapq,itertools,json,sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src.data.benchmark_qa import narrative_audit,write_narrative_report,table,c2_audit,gallery
from src.data.claim_benchmark import canonical,sha


def main():
    bundle=ROOT/'data/manifests/benchmark_v3'
    claims=[json.loads(line) for line in (bundle/'manifest.jsonl').read_text().splitlines()]
    audit=json.loads((bundle/'dataset_audit.json').read_text());sources={s['source_image_id']:s for s in audit['sources']}
    splits=json.loads((bundle/'splits.json').read_text());validation=json.loads((bundle/'validation.json').read_text())
    exclusions=json.loads((bundle/'exclusions.json').read_text());old=json.loads((ROOT/'qa_measurements.json').read_text())
    narrative=narrative_audit(claims)
    write_narrative_report(old['narrative'],ROOT/'NARRATIVE_SHORTCUT_AUDIT.md','v2 original')
    write_narrative_report(narrative,ROOT/'NARRATIVE_SHORTCUT_AUDIT_V3.md','v3 candidate')
    with (ROOT/'NARRATIVE_SHORTCUT_AUDIT.md').open('a') as stream:
        stream.write('\n## Corrección versionada v3\n\nSe preservó v2. v3 usa el mismo target de daño para C0/C1/C5 y cuatro formas emparejadas: afirmación, litotes, afirmación modal y doble negación, combinadas con ocho prefijos y cuatro cierres neutrales elegidos por hash/seed independientemente de la etiqueta. Así, negaciones aparecen también en controles SUPPORTED y no solo en SUSPICIOUS. No se usa test para ajustar frecuencias o seleccionar plantillas.\n')
        stream.write(f"\nV3: {narrative['nonempty']} narrativas no vacías; {narrative['unique_nonempty']} distintas; {narrative['duplicate_percent_nonempty']:.3f}% de duplicados. Ver NARRATIVE_SHORTCUT_AUDIT_V3.md para todas las asociaciones.\n")
        stream.write('\nLa repetición de controles sobre la misma fuente es intencional; las plantillas entre fuentes y asociaciones residuales siguen siendo limitaciones. No se afirma eliminar todos los shortcuts. El vocabulario disponible de ocho clases y la gramática controlada limita la diversidad; hacen falta narrativas adjudicadas y controles más naturales. Además, C1/C5 siguen negando daños presentes: falta un control de ausencia semántica compatible adjudicado. Balancear la palabra no no elimina ese atajo semántico; ausencia de anotación no autoriza inventar ausencia de daño.\n')
    c2=c2_audit(claims,sources)
    (ROOT/'C2_SEMANTIC_AUDIT_V3.md').write_text('# C2 semantic audit — v3 candidate\n\nMisma heurística de v2, ahora sobre la única clase explícitamente narrada en metadata.asserted_damage_classes. No anotado no implica ausente; etiquetas no modificadas. Ubicación anatómica UNKNOWN.\n\n'+str(dict(Counter(r['classification'] for r in c2)))+'\n\n'+table(c2,list(c2[0])))
    controls=[c for c in claims if c['condition']=='C8']
    rows=[{'claim_id':c['claim_id'],'source_image_id':c['source_image_id'],'subtype':c['transformation']['parameters']['subtype'],
           'label':c['expected_label'],'all_damage_regions_retained':c['transformation']['parameters'].get('all_damage_regions_retained','JPEG: no crop'),
           'parameters':c['transformation']['parameters']} for c in controls]
    (ROOT/'C8_BENIGN_CONTROLS_AUDIT.md').write_text('# C8 benign controls — v3 candidate\n\nV2 permanece con JPEG. V3 registra C8_JPEG, C8_RESIZE y C8_CROP en transformation.parameters.subtype, manteniendo condición C8 y SUPPORTED.\nJPEG95: PSNR>=35. Resize: escala1.25, Lanczos, sin recorte. Crop: máximo5% de cada borde, restringido para conservar TODOS los píxeles de máscaras de daño anotadas; si no hay margen, no se genera y se registra exclusión. La geometría original se interpreta con scale/translation registrados.\n\n'+str(dict(Counter(r['subtype'] for r in rows)))+'\n\n'+table(rows,['claim_id','source_image_id','subtype','label','all_damage_regions_retained','parameters']))
    c9=[{'source_image_id':c['source_image_id'],'status':'ACCEPTED',**c['transformation']['parameters']} for c in claims if c['condition']=='C9']
    c9 += [{'source_image_id':e['source_image_id'],'status':'EXCLUDED',**e['parameters']} for e in exclusions if e['condition']=='C9']
    old_c9={r['source_image_id']:r['status'] for r in old['c9']};new_c9={r['source_image_id']:r['status'] for r in c9}
    assert all(new_c9[k]==v for k,v in old_c9.items())
    (ROOT/'C9_DEGRADATION_AUDIT_V3.md').write_text('# C9 — v3, mismo criterio\n\nRadio0.15*min(width,height), varianza Laplaciana<=1.0. Cada aceptación/exclusión se explica por comparar su valor contra1.0; parámetros no ajustados con test. Los 7 aceptados y 17 excluidos originales de v2 conservan su resultado.\n\n'+str(dict(Counter(r['status'] for r in c9)))+'\n\n'+table(c9,['source_image_id','status','radius_pixels','laplacian_variance','maximum_laplacian_variance']))
    assert validation['families']['localized_rgb_inversion']==['test']
    c10_path=ROOT/'C10_OOD_AUDIT.md'
    base_c10=c10_path.read_text().split('\n## V3 candidate')[0]
    c10_path.write_text(base_c10+f"\n## V3 candidate\n\n{validation['conditions'].get('C10',0)} casos; localized_rgb_inversion aparece únicamente en test, ausencia comprobada en train y validation. No se usa como cuarta clase de entrenamiento.\n")
    # Deterministic, deliberately small preview of v3; not a reviewed sample.
    examples=[]
    for condition in (f'C{i}' for i in range(11)):
        group=[c for c in claims if c['condition']==condition]
        if condition=='C8':
            for subtype in ('C8_JPEG','C8_RESIZE','C8_CROP'):examples.extend([c for c in group if c['transformation']['parameters']['subtype']==subtype][:3])
        else:examples.extend(group[:3])
    gallery(ROOT,examples,sources,ROOT/'benchmark_v3_qa_sample.html')
    gallery(ROOT,claims,sources,ROOT/'benchmark_v3_qa.html')
    parent={key:key for key in splits['groups']}
    def find(key):
        while parent[key]!=key:
            parent[key]=parent[parent[key]];key=parent[key]
        return key
    for c in claims:
        if c['condition']!='C2':continue
        a=find(splits['sources'][c['source_image_id']]['group_id'])
        b=find(splits['sources'][c['transformation']['donor_source_image_ids'][0]]['group_id'])
        parent[max(a,b)]=min(a,b)
    dependency_components={}
    for source_id,row in splits['sources'].items():
        dependency_components.setdefault(row['split'],set()).add(find(row['group_id']))
    summary={'reviewed_version':'v2 automated audit; v3 generated candidate, not human adjudicated',
             'v3_c2_dependency_components_per_split':{k:len(v) for k,v in dependency_components.items()},
             'v3_validation':validation,'v3_source_images':audit['images'],'v3_annotations':audit['annotations'],
             'v2_c2_counts':dict(Counter(r['classification'] for r in old['c2'])),
             'v3_c2_counts':dict(Counter(r['classification'] for r in c2)),
             'v2_c3_small':sum(r['small_area_flag'] for r in old['C3']),
             'v2_c4_small':sum(r['small_area_flag'] for r in old['C4']),
             'v2_c5_both_verified':sum(r['semantic_contradiction_annotation_supported'] and r['visual_manipulation_verified'] for r in old['C5']),
             'v3_narrative':narrative,'v3_c9_status':dict(Counter(r['status'] for r in c9)),
             'v3_exclusion_conditions':dict(Counter(e['condition'] for e in exclusions)),
             'v3_class_instances':audit['class_instances'],'v3_source_damage_prevalence':dict(Counter(label for s in audit['sources'] for label in s['damage_classes'])),
             'v3_claim_damage_prevalence':dict(Counter(label for c in claims for label in c['annotated_damage_classes'])),
             'v3_manifest_sha256':sha((bundle/'manifest.jsonl').read_bytes()),'ready_for_models':False}
    (ROOT/'qa_summary.json').write_bytes(canonical(summary))
    print(json.dumps({k:summary[k] for k in ('v3_source_images','v3_annotations','v3_c2_counts','v3_c9_status','v3_manifest_sha256','ready_for_models')},indent=2))

if __name__=='__main__':main()
