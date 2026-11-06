"""Descriptive scientific QA, never a learned evaluator or human adjudication."""
from collections import Counter,defaultdict
import html
import json
import math
import os
from pathlib import Path
import re
import statistics
from urllib.parse import quote

import cv2
import numpy as np
from PIL import Image

from src.data.claim_benchmark import canonical,sha,narrative,NEGATIVE,DAMAGE_TERMS
from src.data.benchmark_v2 import annotation_masks,localized_transform


def read_rgb(path):
    with Image.open(path) as image: return np.asarray(image.convert('RGB')).copy()


def tokens(text): return re.findall(r'\b\w+\b',(text or '').lower(),flags=re.UNICODE)


def narrative_audit(claims):
    nonempty=[c for c in claims if c['narrative_text']]
    stats={}
    for condition in sorted({c['condition'] for c in claims},key=lambda s:int(s[1:])):
        rows=[c for c in claims if c['condition']==condition]
        lengths=[len(tokens(c['narrative_text'])) for c in rows]
        chars=[len(c['narrative_text'] or '') for c in rows]
        stats[condition]={'claims':len(rows),'unique_nonempty':len({c['narrative_text'] for c in rows if c['narrative_text']}),
                          'missing':sum(c['narrative_text'] is None for c in rows),
                          'mean_tokens':statistics.mean(lengths),'std_tokens_population':statistics.pstdev(lengths),
                          'mean_chars':statistics.mean(chars),'std_chars_population':statistics.pstdev(chars),
                          'template_ids':dict(Counter(c['provenance']['narrative_template_id'] for c in rows)),
                          'punctuation':dict(Counter(ch for c in rows for ch in (c['narrative_text'] or '') if not ch.isalnum() and not ch.isspace()))}
    associations={}
    for field in ('condition','expected_label'):
        classes=Counter(c[field] for c in nonempty);features=defaultdict(Counter)
        for c in nonempty:
            words=tokens(c['narrative_text']);ngrams=set(words)|{' '.join(words[i:i+2]) for i in range(len(words)-1)}
            for term in ngrams: features[term][c[field]]+=1
        rows=[]
        for term,counts in sorted(features.items()):
            support=sum(counts.values())
            if support<3: continue
            for target,count in counts.items():
                precision=count/support; prevalence=classes[target]/len(nonempty)
                if precision>=.8 or precision/prevalence>=2:
                    rows.append({'term':term,'target':target,'documents':support,'target_documents':count,
                                 'precision':precision,'lift':precision/prevalence,'exclusive':count==support})
        associations[field]=sorted(rows,key=lambda r:(-r['precision'],-r['documents'],r['term'],r['target']))
    by_label={}
    punctuation=defaultdict(lambda:{'conditions':Counter(),'labels':Counter()})
    for label in sorted({c['expected_label'] for c in claims}):
        rows=[c for c in claims if c['expected_label']==label]
        lengths=[len(tokens(c['narrative_text'])) for c in rows]
        by_label[label]={'claims':len(rows),'missing':sum(c['narrative_text'] is None for c in rows),
                         'mean_tokens':statistics.mean(lengths),'std_tokens_population':statistics.pstdev(lengths)}
    for c in claims:
        marks={ch for ch in (c['narrative_text'] or '') if not ch.isalnum() and not ch.isspace()}
        for mark in marks:
            punctuation[mark]['conditions'][c['condition']]+=1
            punctuation[mark]['labels'][c['expected_label']]+=1
    punctuation={mark:{'conditions':dict(v['conditions']),'labels':dict(v['labels']),
                       'exclusive_label':len(v['labels'])==1,'exclusive_condition':len(v['conditions'])==1}
                 for mark,v in sorted(punctuation.items())}
    unique=len({c['narrative_text'] for c in nonempty})
    return {'claims':len(claims),'nonempty':len(nonempty),'unique_nonempty':unique,
            'duplicate_percent_nonempty':100*(len(nonempty)-unique)/len(nonempty) if nonempty else 0,
            'missing':len(claims)-len(nonempty),'by_condition':stats,'by_label':by_label,'punctuation_associations':punctuation,'associations':associations,
            'literal_label_or_condition_mentions':[c['claim_id'] for c in nonempty if re.search(r'\b(?:C(?:10|[0-9])|SUPPORTED|SUSPICIOUS|INSUFFICIENT|OOD|fraude|sospechoso|manipulad[ao]|insuficiente|contradicción)\b',c['narrative_text'],flags=re.IGNORECASE)],
            'method':'Descriptive document-frequency unigram/bigram associations; min support 3, precision>=0.8 OR lift>=2; no fitting, no inferential p-values; dependent variants',
            'human_review':'NOT PERFORMED'}


def c2_audit(claims,sources):
    rows=[]
    for c in claims:
        if c['condition']!='C2': continue
        source=sources[c['source_image_id']]; donor=sources[c['transformation']['donor_source_image_ids'][0]]
        asserted=set(c.get('metadata',{}).get('asserted_damage_classes',source['damage_classes']));available=set(donor['damage_classes']);shared=asserted&available
        category='likely compatible' if asserted<=available else 'likely contradiction' if not shared else 'ambiguous'
        distance=(int(source['dhash128'],16)^int(donor['dhash128'],16)).bit_count()
        rows.append({'claim_id':c['claim_id'],'source_image_id':c['source_image_id'],'donor_source_image_id':donor['source_image_id'],
                     'classification':category,'asserted_classes':sorted(asserted),'donor_classes':sorted(available),
                     'shared_classes':sorted(shared),'unconfirmed_classes':sorted(asserted-available),
                     'damage_location_compatibility':'UNKNOWN: no anatomical locations in narratives/damage-only annotations',
                     'dhash_distance':distance,'too_similar_flag':distance<=6,'narrative_plausible_flag':bool(shared),
                     'label_unchanged':c['expected_label']})
    return rows


def manipulation_audit(root,claims,sources,config,narrative_resolver=None):
    reports={key:[] for key in ('C3','C4','C5')}
    for c in claims:
        condition=c['condition']
        if condition not in reports: continue
        source=sources[c['source_image_id']];original=read_rgb(root/source['image_path']);actual=read_rgb(root/c['image_path'])
        p=c['transformation']['parameters']
        with Image.open(root/p['mask_path']) as image: mask=np.asarray(image.convert('L'))>0
        changed=np.any(original!=actual,axis=2)
        recreated,_=localized_transform(root,source,condition,config)
        rows=annotation_masks(root,source);union=np.maximum.reduce([m for _,m in rows])>0
        fraction=float(changed.mean());delta=np.abs(actual.astype(float)-original.astype(float)).mean(axis=2)
        record={'claim_id':c['claim_id'],'source_image_id':c['source_image_id'],
                'mask_nonempty':bool(mask.any()),'dimensions_match':original.shape==actual.shape and mask.shape==original.shape[:2],
                'changed_pixels':int(changed.sum()),'changed_percent':100*fraction,'mask_percent':100*float(mask.mean()),
                'outside_mask_changed_pixels':int((changed&~mask).sum()),
                'reproducible':bool(recreated is not None and np.array_equal(actual,recreated[0]) and np.array_equal(mask,recreated[1]>0)),
                'mask_sha_matches':sha((root/p['mask_path']).read_bytes())==p['mask_sha256'],
                'mean_absolute_rgb_change_in_mask':float(delta[mask].mean()),
                'small_area_flag':fraction<.005,'large_area_flag':fraction>.20,'human_realism_review':'NOT PERFORMED'}
        if condition in ('C3','C5'):
            sx,sy,ex,ey=p['source_box'];dx,dy,fx,fy=p['destination_box'];h,w=mask.shape
            record.update(source_and_destination_in_bounds=0<=sx<ex<=w and 0<=sy<ey<=h and 0<=dx<fx<=w and 0<=dy<fy<=h,
                          valid_source_and_donor=c['source_image_id'] in sources and not c['transformation']['donor_source_image_ids'],
                          source_copy_matches=bool(np.array_equal(actual[dy:fy,dx:fx],original[sy:ey,sx:ex])),
                          original_damage_preserved=bool(np.array_equal(original[union],actual[union])),
                          patch_size=[ex-sx,ey-sy],patch_width_at_360px_display=(ex-sx)*360/w)
        if condition=='C4':
            selected=dict(rows)[p['annotation_object_index']]>0
            border=cv2.dilate(mask.astype(np.uint8),np.ones((3,3),np.uint8))-cv2.erode(mask.astype(np.uint8),np.ones((3,3),np.uint8))
            def gradient(rgb):
                gray=cv2.cvtColor(rgb,cv2.COLOR_RGB2GRAY).astype(float)
                return np.hypot(cv2.Sobel(gray,cv2.CV_64F,1,0),cv2.Sobel(gray,cv2.CV_64F,0,1))
            before=float(gradient(original)[border>0].mean());after=float(gradient(actual)[border>0].mean())
            record.update(mask_matches_annotation=bool(np.array_equal(mask,selected)),boundary_gradient_before=before,boundary_gradient_after=after,
                          possible_boundary_artifact_flag=after>2*max(before,1),damage_removal_verified=False)
        if condition=='C5':
            denied=p['denied_annotated_class']
            if narrative_resolver is None:
                _,template,expected_target=narrative(source,config['seed'])
                expected_text=NEGATIVE[int(template.rsplit('-',1)[1])].format(damage=DAMAGE_TERMS[expected_target])
            else:
                expected_text,template,expected_target=narrative_resolver(source,config['seed'],True)
            denial_matches=c['narrative_text']==expected_text and denied==expected_target
            record.update(denied_class=denied,narrative_denial_matches=denial_matches,semantic_contradiction_annotation_supported=denial_matches and denied in source['damage_classes'] and record['original_damage_preserved'],
                          visual_manipulation_verified=bool(changed.any() and record['source_copy_matches'] and record['reproducible']))
        reports[condition].append(record)
    return reports


def table(rows,keys):
    return '| '+' | '.join(keys)+' |\n| '+' | '.join('---' for _ in keys)+' |\n'+'\n'.join('| '+' | '.join(str(row.get(key,'')).replace('|','/').replace('\n',' ') for key in keys)+' |' for row in rows)+'\n'


_REASON_OPTIONS=[
    ('C2_sustitucion_identificable','C2: sustitución identificable (clases/contexto no compatibles)'),
    ('C2_compatible','C2: compatible con el relato, no concluyente por sí solo'),
    ('C2_no_identificable','C2: no identificable solo con imagen y texto disponibles'),
    ('C345_integra_cumple','C3/C4/C5: edición íntegra y cumple la transformación prevista'),
    ('C345_cumple_no_realista','C3/C4/C5: cumple la transformación pero no resulta realista'),
    ('C345_no_verificable','C3/C4/C5: no se puede verificar la edición o la máscara'),
    ('otro','Otro (detallar en observaciones)'),
]
"""Motivos propuestos para discusión con la asesora; no son automáticos ni
obligatorios. El revisor puede dejarlo vacío y usar solo observaciones."""


def build_audit_index(c2_rows=(),pixel_rows_by_condition=None):
    """claim_id -> señales automáticas (alertas de QA), nunca juicio de validez.
    c2_rows: salida de c2_audit. pixel_rows_by_condition: {'C3':[...],'C4':[...],'C5':[...]}
    (p.ej. cargado de qa_v3_pixels.json ya calculado, sin recomputar sobre imágenes)."""
    index={}
    for row in c2_rows: index[row['claim_id']]=row
    for rows in (pixel_rows_by_condition or {}).values():
        for row in rows: index[row['claim_id']]=row
    return index


def gallery(root,claims,sources,target,audit_index=None,extra_intro=''):
    audit_index=audit_index or {}
    def img(label,path):
        if path is None: return f'<figure><figcaption>{label}</figcaption><p>MODALIDAD AUSENTE</p></figure>'
        full=(root/path).resolve()
        if not full.is_file(): raise ValueError(f'Missing gallery asset: {path}')
        url=quote(os.path.relpath(full,target.parent).replace(os.sep,'/'),safe='/')
        return f'<figure><figcaption>{label}</figcaption><a href="{url}" target="_blank"><img loading="lazy" src="{url}" alt="{label}"></a></figure>'
    def audit_block(claim_id):
        flags=audit_index.get(claim_id)
        if not flags: return ''
        skip={'claim_id','source_image_id'}
        rows=''.join(f'<tr><td>{html.escape(str(k))}</td><td>{html.escape(str(v))}</td></tr>' for k,v in flags.items() if k not in skip)
        return (f'<details class="audit"><summary>Señales automáticas de QA (alertas, no deciden validez)</summary>'
                f'<table class="audit-flags">{rows}</table>'
                f'<p class="warn">No decidir únicamente por el porcentaje de área modificada.</p></details>')
    cards=[]
    for c in claims:
        source=sources[c['source_image_id']];p=c['transformation']['parameters'];donors=c['transformation']['donor_source_image_ids']
        pictures=img('Original',source['image_path'])+img('Imagen presentada al reclamo',c['image_path'])
        for donor in donors: pictures+=img('Donante '+html.escape(donor),sources[donor]['image_path'])
        if p.get('mask_path'): pictures+=img('Máscara de transformación',p['mask_path'])
        detail={key:c[key] for key in ('claim_id','source_image_id','condition','expected_label','narrative_text')}
        detail.update(split=c.get('split','unknown'),donor_source_image_ids=donors,transformation=c['transformation'])
        identifier=html.escape(c['claim_id']);split=html.escape(str(c.get('split','unknown')))
        reason_options=''.join(f'<option value="{value}">{html.escape(text)}</option>' for value,text in _REASON_OPTIONS)
        cards.append(f'''<article data-condition="{c['condition']}" data-id="{identifier}" data-source="{html.escape(c['source_image_id'])}" data-split="{split}">
<h2>{c['condition']} <span class="split-badge">{split}</span></h2><p>{identifier} · {html.escape(c['source_image_id'])}</p>
<p class="narrative">{html.escape(c['narrative_text'] or 'NARRATIVA AUSENTE')}</p><div class="images">{pictures}</div>
{audit_block(c['claim_id'])}
<details class="label-reveal"><summary>Mostrar etiqueta objetivo (abrir solo después de decidir)</summary><p>expected_label: <strong>{html.escape(c['expected_label'])}</strong></p></details>
<details><summary>Procedencia, parámetros y seed</summary><pre>{html.escape(json.dumps(detail,ensure_ascii=False,indent=2))}</pre></details>
<fieldset class="review-panel"><label>Revisión: <select class="review">
<option value="PENDIENTE">PENDIENTE DE REVISIÓN</option><option value="VALIDO">VÁLIDO</option><option value="AMBIGUO">AMBIGUO</option><option value="INVALIDO">INVÁLIDO</option>
</select></label>
<label>Motivo: <select class="reason"><option value="">(elegir)</option>{reason_options}</select></label>
<label class="obs">Observaciones: <input class="note" placeholder="Observación adicional" aria-label="Observación humana"></label>
</fieldset></article>''')
    content='''<!doctype html><html lang="es"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Benchmark — QA humana local</title><style>
body{font:16px system-ui;background:#f2f4f8;color:#17233a;margin:0}header{position:sticky;top:0;background:#17233a;color:white;padding:14px;z-index:2}
main{max-width:1500px;margin:auto;padding:16px}article{background:white;border:1px solid #ccd3df;padding:18px;margin:20px 0;border-radius:10px}
.images{display:flex;flex-wrap:wrap;gap:12px}.images figure{flex:1;min-width:270px;margin:0}.images img{width:100%;height:340px;object-fit:contain;background:#e8e8e8}
figcaption{font-weight:bold;padding:8px}pre{white-space:pre-wrap;overflow-wrap:anywhere}input,select,button{font:inherit;padding:8px;margin:5px}
.note{width:60%}.narrative{font-size:1.15em}article[hidden]{display:none}.split-badge{font-size:.6em;background:#e8e8e8;color:#17233a;border-radius:6px;padding:2px 8px;vertical-align:middle}
table.audit-flags{border-collapse:collapse;width:100%}table.audit-flags td{border:1px solid #ccd3df;padding:4px 8px;font-size:.9em}
.warn{color:#8a4b00;font-weight:bold}.review-panel{border:1px solid #ccd3df;border-radius:8px;padding:10px;margin-top:10px}
</style><header><strong>QA humana · generación ≠ realismo validado</strong>
<select id="condition"><option value="">Todas las condiciones</option>'''+''.join(f'<option>C{i}</option>' for i in range(11))+'''</select>
<select id="status"><option value="">Todos los estados</option><option value="PENDIENTE">Pendiente</option><option value="VALIDO">Válido</option><option value="AMBIGUO">Ambiguo</option><option value="INVALIDO">Inválido</option></select>
<input id="search" placeholder="Buscar claim / source">
<button id="export">Exportar revisión JSON</button>
<label style="color:inherit">Importar: <input id="import" type="file" accept="application/json"></label>
<span id="count"></span></header>
<main><p>Comparación original / imagen presentada, donante y máscara. Haga clic en una imagen para inspeccionarla a resolución completa.
Las selecciones se guardan en este navegador y se exportan/importan manualmente como archivo JSON; nunca modifican el manifest original ni cambian labels.
La etiqueta objetivo permanece oculta por defecto: ábrala solo después de registrar su juicio si quiere evitar sesgo de confirmación.</p>'''+extra_intro+''.join(cards)+'''</main><script>
const cards=[...document.querySelectorAll('article')], key='uafeg-qa-'+location.pathname;
let saved={};try{saved=JSON.parse(localStorage.getItem(key)||'{}')}catch(e){}
function persist(){try{localStorage.setItem(key,JSON.stringify(saved))}catch(e){}}
function applyReview(id,entry){const c=cards.find(x=>x.dataset.id===id);if(!c)return;const r=c.querySelector('.review'),m=c.querySelector('.reason'),n=c.querySelector('.note');
r.value=entry?.status||'PENDIENTE';m.value=entry?.reason||'';n.value=entry?.note||''}
for(const c of cards){const r=c.querySelector('.review'),m=c.querySelector('.reason'),n=c.querySelector('.note');
applyReview(c.dataset.id,saved[c.dataset.id]);
for(const el of [r,m,n])el.addEventListener('change',()=>{saved[c.dataset.id]={status:r.value,reason:m.value,note:n.value};persist()})}
function filter(){let n=0;for(const c of cards){const st=(saved[c.dataset.id]?.status)||'PENDIENTE';
c.hidden=!!((condition.value&&c.dataset.condition!==condition.value)||(status.value&&st!==status.value)||(search.value&&!c.textContent.toLowerCase().includes(search.value.toLowerCase())));
if(!c.hidden)n++}document.querySelector('#count').textContent=n+' reclamos'}
const condition=document.querySelector('#condition'),status=document.querySelector('#status'),search=document.querySelector('#search');
condition.onchange=filter;status.onchange=filter;search.oninput=filter;filter();
document.querySelector('#export').onclick=()=>{const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([JSON.stringify({gallery:location.pathname,manifest_sha256:manifestDigest,reviews:saved},null,2)],{type:'application/json'}));a.download='human_qa_reviews.json';a.click();URL.revokeObjectURL(a.href)};
document.querySelector('#import').onchange=(ev)=>{const file=ev.target.files[0];if(!file)return;const reader=new FileReader();
reader.onload=()=>{let data;try{data=JSON.parse(reader.result)}catch(e){alert('JSON inválido');return}
if(data.manifest_sha256&&data.manifest_sha256!==manifestDigest){alert('El archivo importado corresponde a otra selección/manifest (SHA256 distinto). No se importó nada.');return}
for(const [id,entry] of Object.entries(data.reviews||{})){saved[id]=entry;applyReview(id,entry)}persist();filter();alert('Revisión importada: '+Object.keys(data.reviews||{}).length+' casos.')};
reader.readAsText(file)};
</script></html>'''
    digest=sha(b''.join(canonical(c) for c in claims))
    content=content.replace('<main><p>',f'<main><p>Manifest/selección SHA256: <code>{digest}</code></p><p>',1)
    content=content.replace('const cards=',f'const manifestDigest={json.dumps(digest)};\nconst cards=',1)
    content=content.replace("key='uafeg-qa-'+location.pathname;","key='uafeg-qa-'+location.pathname+'-'+manifestDigest;")
    target.write_text(content,encoding='utf-8')


def run_qa(root,bundle,config,output):
    claims=[json.loads(line) for line in (bundle/'manifest.jsonl').read_text().splitlines()]
    audit=json.loads((bundle/'dataset_audit.json').read_text());sources={s['source_image_id']:s for s in audit['sources']}
    output.mkdir(parents=True,exist_ok=True)
    c2=c2_audit(claims,sources);manipulations=manipulation_audit(root,claims,sources,config);narratives=narrative_audit(claims)
    intro='# C2 semantic audit — v2\n\nHeurística descriptiva basada en clases anotadas, NO adjudicación humana.\nTodas las clases narradas anotadas en donor: likely compatible; ninguna: likely contradiction; solapamiento parcial: ambiguous.\nAusencia de anotación no prueba ausencia visual. No hay ubicación anatómica narrada; compatibilidad de ubicación UNKNOWN.\nNo se cambian labels. Umbral de similitud dHash128<=6.\n\n'
    (output/'C2_SEMANTIC_AUDIT.md').write_text(intro+str(dict(Counter(r['classification'] for r in c2)))+'\n\n'+table(c2,list(c2[0])))
    names={'C3':'C3_FORENSIC_AUDIT.md','C4':'C4_INPAINT_AUDIT.md','C5':'C5_COMBINED_AUDIT.md'}
    for condition,rows in manipulations.items():
        intro=f'# {condition} audit — v2\n\nComprobación sobre imágenes y máscaras reales con regeneración. Revisión humana de realismo: NOT PERFORMED.\nÁrea alterada <0.5% marcada pequeña; >20% grande. Son alertas de QA, no umbrales de fraude/realismo.\nC4: gradiente de borde >2×original es alerta, no prueba de artefacto. C5 comprueba contradicción anotada y manipulación independientemente.\n\n'
        (output/names[condition]).write_text(intro+table(rows,list(rows[0])))
    write_narrative_report(narratives,output/'NARRATIVE_SHORTCUT_AUDIT.md','v2')
    gallery(root,claims,sources,output/'benchmark_v2_qa.html')
    c9=[{'source_image_id':c['source_image_id'],'status':'ACCEPTED',**c['transformation']['parameters']} for c in claims if c['condition']=='C9']
    c9 += [{'source_image_id':e['source_image_id'],'status':'EXCLUDED',**e['parameters']} for e in json.loads((bundle/'exclusions.json').read_text()) if e['condition']=='C9']
    (output/'C9_DEGRADATION_AUDIT.md').write_text('# C9 — criterio original preservado\n\nGaussian blur radius=0.15*min(width,height); aceptación si varianza Laplaciana<=1.0.\nSin ajuste del umbral ni reetiquetado de los 17 excluidos.\n\n'+table(c9,['source_image_id','status','radius_pixels','laplacian_variance','maximum_laplacian_variance']))
    families=defaultdict(set)
    for c in claims: families[c['transformation']['operation']].add(c['split'])
    assert families['localized_rgb_inversion']=={'test'}
    (output/'C10_OOD_AUDIT.md').write_text('# C10 — OOD procedimental\n\nFamilia exacta: inversión RGB localizada (255-RGB) dentro del menor polígono de daño rasterizado.\nTres registros, exclusivamente test; ninguno en train/validation. DecisionLabel permanece con tres clases.\nNo se entrenó ningún modelo; esto verifica reserva de familia, no generalización empírica.\n')
    result={'c2':c2,**manipulations,'narrative':narratives,'c9':c9,'families':{k:sorted(v) for k,v in families.items()},
            'manifest_sha256':sha((bundle/'manifest.jsonl').read_bytes())}
    (output/'qa_measurements.json').write_bytes(canonical(result))
    return result


def write_narrative_report(result,path,version):
    text=f'# Narrative shortcut audit — {version}\n\n{result["method"]}\n\n'
    text+=f'No vacías: {result["nonempty"]}; únicas: {result["unique_nonempty"]}; duplicados: {result["duplicate_percent_nonempty"]:.3f}%; ausentes: {result["missing"]}.\n'
    text+='Duplicados = (filas no vacías - textos distintos)/filas no vacías. Ausencia reportada por separado.\nLongitudes de cada condición incluyen ausencia como cero. Desviación poblacional.\n\n'
    text+=table([{'condition':k,**v} for k,v in result['by_condition'].items()],['condition','claims','unique_nonempty','missing','mean_tokens','std_tokens_population','mean_chars','std_chars_population','template_ids','punctuation'])
    text+='\n## Longitud por etiqueta\n\n'+table([{'label':k,**v} for k,v in result['by_label'].items()],['label','claims','missing','mean_tokens','std_tokens_population'])
    text+='\n## Puntuación por documento\n\n'+table([{'character':k,**v} for k,v in result['punctuation_associations'].items()],['character','conditions','labels','exclusive_label','exclusive_condition'])
    text+=f'\nMenciones explícitas de condition/label/indicadores prefijados: {result["literal_label_or_condition_mentions"]}.\n'
    for field,rows in result['associations'].items(): text+=f'\n## Asociaciones con {field}\n\n'+table(rows,['term','target','documents','target_documents','precision','lift','exclusive'])
    text+='\nLas asociaciones son descriptivas, no p-valores ni observaciones independientes. No se ajustó un clasificador.\nLos metadatos de condición/label están excluidos del texto y nunca deben entrar como features.\n'
    path.write_text(text)
