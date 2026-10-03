"""Scientific-QA revision: strict full-source ingestion, paired narratives, C8 controls.

All v1/v2 artifacts remain frozen. QA findings are not adjudicated labels.
"""
from collections import Counter,defaultdict
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path

import numpy as np
from PIL import Image, __version__ as pillow_version
import cv2
import yaml

from src.data import claim_benchmark as base
from src.data import benchmark_v2 as previous
from src.data.hitl_supervisely import parse_hitl_supervisely
from src.data.duplicate_audit import image_fingerprints,group_sources
from src.schemas.claim import ClaimRecord,ClaimTransformation
from src.schemas.packet import EvidencePacket

POSITIVE=('El vehículo presenta {damage}.','El vehículo no está libre de {damage}.',
          'Es correcto afirmar que el vehículo presenta {damage}.',
          'No es correcto afirmar que el vehículo no presenta {damage}.')
NEGATIVE=('El vehículo no presenta {damage}.','El vehículo está libre de {damage}.',
          'No es correcto afirmar que el vehículo presenta {damage}.',
          'Es correcto afirmar que el vehículo no presenta {damage}.')


PREFIXES=('', 'En la imagen, ', 'Según la evidencia visual, ', 'En la fotografía del vehículo, ',
          'Sobre el estado visible, ', 'Respecto al daño mostrado, ', 'En esta descripción, ', 'En la evidencia presentada, ')
SUFFIXES=('', ' Se describe el estado visible.', ' La observación se refiere al vehículo.',
          ' Esta descripción corresponde al daño observado.')


def audit_full(root,config):
    dataset=root/config['dataset_dir']
    images=sorted(p for p in dataset.glob('*/img/*') if p.is_file());annotations=sorted(dataset.glob('*/ann/*.json'))
    accepted=[];invalid=[];counts=Counter();seen=set()
    for path in annotations:
        try:
            records=parse_hitl_supervisely(dataset,relative_to=root,annotation_paths=[path])
            record=records[0]
            if record.source_image_id in seen:raise ValueError('Ambiguous duplicated source ID')
            seen.add(record.source_image_id)
            if not record.annotations:raise ValueError('No annotated damage; cannot construct supported control')
            source={'source_image_id':record.source_image_id,'image_path':record.path,'annotation_reference':path.relative_to(root).as_posix(),
                    'annotation_sha256':base.sha(path.read_bytes()),'annotation_count':len(record.annotations),
                    'damage_classes':sorted(record.damage_classes),**image_fingerprints(root/record.path)}
            accepted.append(source);counts.update(a.damage_class for a in record.annotations)
        except (ValueError,KeyError,TypeError,OSError,IndexError) as exc:
            invalid.append({'annotation_reference':path.relative_to(root).as_posix(),'reason':str(exc),'error_type':type(exc).__name__})
    missing=[p.relative_to(root).as_posix() for p in images if not (p.parent.parent/'ann'/(p.name+'.json')).exists()]
    accepted.sort(key=lambda s:s['source_image_id'])
    return {'dataset':'humansintheloop/car-parts-and-car-damages','dataset_version':2,'local_path':config['dataset_dir'],
            'images_available':len(images),'annotation_files':len(annotations),'images':len(accepted),
            'annotations':sum(s['annotation_count'] for s in accepted),'class_instances':dict(sorted(counts.items())),
            'excluded_sources':invalid,'images_without_annotation_file':missing,'sources':accepted,
            'duplicates':group_sources(accepted,config['near_duplicate_hamming_threshold']),
            'integrity_scope':'Each original annotation independently checked with canonical strict reader; rejected raw retained unchanged'}


def paired_narrative(source,seed,contradiction=False):
    classes=source['damage_classes']
    target=classes[base.stable_index(source['source_image_id'],seed,'contradiction',len(classes))]
    index=base.stable_index(source['source_image_id'],seed,'paired-narrative-v3',len(POSITIVE))
    prefix_index=base.stable_index(source['source_image_id'],seed,'narrative-prefix-v3',len(PREFIXES))
    suffix_index=base.stable_index(source['source_image_id'],seed,'narrative-suffix-v3',len(SUFFIXES))
    sentence=(NEGATIVE if contradiction else POSITIVE)[index].format(damage=base.DAMAGE_TERMS[target])
    if PREFIXES[prefix_index]:sentence=sentence[0].lower()+sentence[1:]
    text=PREFIXES[prefix_index]+sentence+SUFFIXES[suffix_index]
    return text,f'paired-v3-{index}-style-{prefix_index}-{suffix_index}',target


def benign_control(root,source,subtype,config):
    with Image.open(root/source['image_path']) as image:original=image.convert('RGB')
    width,height=original.size
    if subtype=='C8_RESIZE':
        new=(round(width*config['resize_scale']),round(height*config['resize_scale']))
        result=original.resize(new,Image.Resampling.LANCZOS)
        params={'subtype':subtype,'scale_x':new[0]/width,'scale_y':new[1]/height,'original_size':[width,height],
                'output_size':list(new),'interpolation':'Pillow LANCZOS','all_damage_regions_retained':True}
    elif subtype=='C8_CROP':
        masks=previous.annotation_masks(root,source);union=np.maximum.reduce([m for _,m in masks])>0
        ys,xs=np.nonzero(union)
        # A fixed 5% maximum trims background only; preserve every annotated pixel.
        left=min(int(xs.min()),int(width*config['crop_margin_fraction']))
        top=min(int(ys.min()),int(height*config['crop_margin_fraction']))
        right=max(int(xs.max())+1,width-int(width*config['crop_margin_fraction']))
        bottom=max(int(ys.max())+1,height-int(height*config['crop_margin_fraction']))
        if (left,top,right,bottom)==(0,0,width,height):
            return None,{'subtype':subtype,'reason':'No safe background margin: damage touches all image borders'}
        result=original.crop((left,top,right,bottom))
        if np.count_nonzero(union[top:bottom,left:right])!=np.count_nonzero(union):raise ValueError('Crop removed annotated evidence')
        params={'subtype':subtype,'crop_box':[left,top,right,bottom],'maximum_margin_fraction':config['crop_margin_fraction'],
                'all_damage_regions_retained':True,'retained_damage_pixels':int(union.sum()),
                'original_size':[width,height],'output_size':list(result.size),'annotation_translation':[-left,-top]}
    else: raise ValueError('Unexpected benign subtype')
    return previous.png_bytes(np.asarray(result),config.get('png_compression_level',9)),params


def generate(root,audit,splits,config,registry):
    # Reuse existing real operators; isolated IDs include generator/config version.
    def one(source):
        return previous.generate(root,audit,splits,config,registry,source_subset=[source])
    claims=[];exclusions=[]
    # Source-ordered collection keeps byte output deterministic across workers.
    with ThreadPoolExecutor(max_workers=4) as executor:
        for number,(generated,rejected) in enumerate(executor.map(one,audit['sources']),1):
            claims.extend(generated);exclusions.extend(rejected)
            if number%100==0:print(f'{number}/{len(audit["sources"])} sources generated',flush=True)
    sources={s['source_image_id']:s for s in audit['sources']}
    for c in claims:
        text,template,target=paired_narrative(sources[c.source_image_id],config['seed'],c.condition in ('C1','C5'))
        c.narrative_text=None if c.condition=='C6' else text
        c.provenance.narrative_template_id=template
        c.metadata={'asserted_damage_classes':[target],'narrative_revision':'paired-v3; mitigation only, human review pending'}
        if c.condition=='C8':c.transformation.parameters['subtype']='C8_JPEG'
    parents={c.source_image_id:c for c in claims if c.condition=='C0'}
    for source in audit['sources']:
        parent=parents[source['source_image_id']]
        for subtype in ('C8_RESIZE','C8_CROP'):
            content,params=benign_control(root,source,subtype,config)
            if content is None:
                exclusions.append({'source_image_id':source['source_image_id'],'condition':'C8',**params});continue
            identifier=base.claim_id(source,'C8',{**config,'subtype':subtype})
            image_path=f'data/processed/benchmark_v3/{identifier}.png'
            base.write_verified(root/image_path,content)
            payload=parent.model_dump(mode='json')
            payload.update(claim_id=identifier,parent_claim_id=parent.claim_id,condition='C8',image_path=image_path,
                           transformation=ClaimTransformation(operation='benign_resize' if subtype=='C8_RESIZE' else 'benign_crop',
                                      seed=config['seed'],parameters=params,image_sha256=base.sha(content)).model_dump(mode='json'))
            claims.append(ClaimRecord.model_validate(payload))
    return sorted(claims,key=lambda c:(c.source_image_id,int(c.condition[1:]),c.transformation.parameters.get('subtype',''))),exclusions


def validate(claims,audit,splits,config,registry,exclusions):
    def need(ok,message):
        if not ok:raise ValueError(message)
    need(splits==base.frozen_splits(audit,config),'Split integrity failure')
    need(audit['duplicates']==group_sources(audit['sources'],config['near_duplicate_hamming_threshold']),'Duplicate group mismatch')
    need(len({c.claim_id for c in claims})==len(claims),'Duplicate claim IDs')
    sources={s['source_image_id']:s for s in audit['sources']};parents={c.source_image_id:c for c in claims if c.condition=='C0'}
    need(set(parents)==set(sources),'Missing supported control')
    images=defaultdict(set);families=defaultdict(set);coverage=set()
    for c in claims:
        need(c.source_image_id in sources,'Unknown source')
        source=sources[c.source_image_id];parent=parents[c.source_image_id];p=c.transformation.parameters
        subtype=p.get('subtype') if c.condition=='C8' else None
        expected_operations={'C0':'identity','C1':'narrative_contradiction','C2':'same_split_image_substitution',
                             'C3':'localized_copy_move','C4':'damage_mask_inpainting','C5':'localized_copy_move',
                             'C6':'remove_narrative','C7':'remove_image','C9':'gaussian_blur','C10':'localized_rgb_inversion'}
        expected_operation=({'C8_JPEG':'jpeg_recompression','C8_RESIZE':'benign_resize','C8_CROP':'benign_crop'}.get(subtype)
                            if c.condition=='C8' else expected_operations[c.condition])
        need(c.transformation.operation==expected_operation,'Unexpected transformation operation')
        need(c.schema_version=='0.3.0','Wrong schema version')
        need(c.provenance.dataset==audit['dataset'] and c.provenance.dataset_version==audit['dataset_version'],'Dataset provenance mismatch')
        coverage.add((c.source_image_id,c.condition,subtype))
        idconfig=({**config,'subtype':subtype} if subtype in ('C8_RESIZE','C8_CROP') else previous.base_config(config) if c.condition in base.ACTIVE else config)
        need(c.claim_id==base.claim_id(source,c.condition,idconfig),'Non-deterministic identifier')
        need(c.expected_label.value==registry[c.condition]['expected_label'],'Taxonomy mismatch')
        need(c.split.value==splits['sources'][c.source_image_id]['split'],'Source leakage')
        need(c.provenance.source_group_id==splits['sources'][c.source_image_id]['group_id'],'Group provenance mismatch')
        need(c.provenance.source_image_sha256==source['file_sha256'] and c.provenance.annotation_sha256==source['annotation_sha256'],'Source hashes mismatch')
        need(c.provenance.source_image_path==source['image_path'] and c.annotation_reference==source['annotation_reference'],'Source paths mismatch')
        need(c.provenance.generator_version==config['generator_version'] and c.transformation.seed==c.provenance.seed==config['seed'],'Generator/seed mismatch')
        need(c.parent_claim_id==(None if c.condition=='C0' else parent.claim_id),'Parent mismatch')
        need(c.provenance==parent.provenance and c.annotated_damage_classes==source['damage_classes'],'Variant provenance mismatch')
        text,template,target=paired_narrative(source,config['seed'],c.condition in ('C1','C5'))
        need(c.narrative_text==(None if c.condition=='C6' else text) and c.provenance.narrative_template_id==template,'Paired narrative mismatch')
        need(c.metadata.get('asserted_damage_classes')==[target],'Narrative target mismatch')
        if c.condition in ('C1','C5'):need(p.get('denied_annotated_class')==target,'Contradiction unsupported')
        if c.condition in ('C0','C1','C6'):need(c.image_path==source['image_path'] and c.transformation.image_sha256==source['file_sha256'],'Original image mismatch')
        if c.condition=='C7':need(c.image_path is None and c.transformation.image_sha256 is None,'Missing modality invalid')
        if c.condition=='C2':
            donor=previous.donor_for(source,audit,splits,config['seed'])
            need(donor is not None and c.transformation.donor_source_image_ids==[donor['source_image_id']],'Donor selection/leakage')
            need(c.image_path==donor['image_path'] and c.transformation.image_sha256==donor['file_sha256'],'Donor content mismatch')
            need(p.get('donor_annotation_reference')==donor['annotation_reference'] and p.get('donor_annotation_sha256')==donor['annotation_sha256'],'Donor annotations mismatch')
        elif c.transformation.donor_source_image_ids:raise ValueError('Unexpected external donor')
        if c.condition in ('C3','C4','C5','C10'):
            need(p.get('changed_pixels',0)>0 and p.get('mask_pixels',0)>=p['changed_pixels'],'Invalid changed area')
            need(p.get('mask_path')==f'data/processed/benchmark_v2/{c.claim_id}.mask.png' and len(p.get('mask_sha256',''))==64,'Mask provenance missing')
            need(c.image_path==f'data/processed/benchmark_v2/{c.claim_id}.png','Manipulated image path mismatch')
            need(p.get('human_realism_review')=='NOT PERFORMED','Unverified human realism assertion')
        if c.condition=='C4':need(p.get('algorithm')=='OpenCV INPAINT_TELEA' and p.get('radius')==config['inpaint_radius'] and p.get('damage_removal_verified') is False,'Inpainting parameters mismatch')
        if c.condition=='C5':need(p.get('original_damage_pixels_preserved') is True,'Contradicted damage altered')
        if c.condition=='C8':
            need(subtype in ('C8_JPEG','C8_RESIZE','C8_CROP'),'Missing C8 subtype')
            if subtype=='C8_JPEG':need(p['psnr_db']>=config['jpeg_min_psnr_db'] and p['quality']==config['jpeg_quality'],'JPEG gate failed')
            else:need(p.get('all_damage_regions_retained') is True,'Relevant evidence cropped out')
        if c.condition=='C9':need(0<=p['laplacian_variance']<=config['blur_max_laplacian_variance'] and p['radius_fraction']==config['blur_radius_fraction'],'C9 gate changed')
        if c.condition=='C10':need(c.split.value=='test' and p['held_out_family']=='localized_rgb_inversion','OOD leak')
        if c.transformation.image_sha256:images[c.transformation.image_sha256].add(c.split.value)
        families[c.transformation.operation].add(c.split.value)
    need(all(len(v)==1 for v in images.values()),'Image SHA cross-split leakage')
    need(families.get('localized_rgb_inversion')=={'test'},'OOD family leak')
    excluded={(e['source_image_id'],e['condition'],e.get('subtype')) for e in exclusions}
    for source in sources:
        for condition in config['conditions']:
            if condition=='C10' and splits['sources'][source]['split']!='test':continue
            variants=('C8_JPEG','C8_RESIZE','C8_CROP') if condition=='C8' else (None,)
            for subtype in variants:
                need((source,condition,subtype) in coverage or (source,condition,subtype) in excluded or (subtype=='C8_JPEG' and (source,condition,None) in excluded),'Missing unexplained source variant')
    return {'result':'PASS','claims':len(claims),'conditions':dict(sorted(Counter(c.condition for c in claims).items(),key=lambda x:int(x[0][1:]))),
            'labels':dict(Counter(c.expected_label.value for c in claims)),
            'c8_subtypes':dict(Counter(c.transformation.parameters['subtype'] for c in claims if c.condition=='C8')),
            'claims_per_split':dict(Counter(c.split.value for c in claims)),
            'sources_per_split':dict(Counter(row['split'] for row in splits['sources'].values())),
            'groups_per_split':dict(Counter(splits['sources'][members[0]]['split'] for members in splits['groups'].values())),
            'overlap':{'train/validation':[],'train/test':[],'validation/test':[]},
            'families':{k:sorted(v) for k,v in sorted(families.items())},'exclusions':len(exclusions),'human_review':'NOT PERFORMED'}


def build(root,config_path,output):
    config=yaml.safe_load(config_path.read_text());registry=yaml.safe_load((root/config['conditions_config']).read_text())['conditions']
    audit=audit_full(root,config)
    splits=base.frozen_splits(audit,config)
    print(f'Validated {audit["images"]} sources, rejected {len(audit["excluded_sources"])}; generating',flush=True)
    claims,exclusions=generate(root,audit,splits,config,registry)
    validation=validate(claims,audit,splits,config,registry,exclusions)
    artifacts={'manifest.jsonl':b''.join(base.canonical(c.model_dump(mode='json')) for c in claims),
               'evidence_packets.jsonl':b''.join(base.canonical(EvidencePacket(claim=c).model_dump(mode='json')) for c in claims),
               'dataset_audit.json':base.canonical(audit),'splits.json':base.canonical(splits),
               'exclusions.json':base.canonical(exclusions),'validation.json':base.canonical(validation)}
    metadata={'benchmark_version':config['benchmark_version'],'generator_version':config['generator_version'],'schema_version':'0.3.0',
              'config_sha256':base.sha(config_path.read_bytes()),'conditions_sha256':base.sha((root/config['conditions_config']).read_bytes()),
              'acquisition_receipt_sha256':base.sha((root/config['acquisition_receipt']).read_bytes()),
              'artifacts_sha256':{n:base.sha(v) for n,v in artifacts.items()},
              'runtime':{'Pillow':pillow_version,'numpy':np.__version__,'opencv':cv2.__version__},
              'readiness':'PENDING_SCIENTIFIC_QA; generation and leakage checks are not human adjudication'}
    for name,content in {**artifacts,'metadata.json':base.canonical(metadata)}.items():base.write_verified(output/name,content)
    return validation


def check(root,config_path,output,verify_images=False):
    config=yaml.safe_load(config_path.read_text());registry=yaml.safe_load((root/config['conditions_config']).read_text())['conditions']
    metadata=json.loads((output/'metadata.json').read_text())
    for name,digest in metadata['artifacts_sha256'].items():
        if base.sha((output/name).read_bytes())!=digest:raise ValueError(f'Artifact hash mismatch: {name}')
    for file,key in [(config_path,'config_sha256'),(root/config['conditions_config'],'conditions_sha256'),(root/config['acquisition_receipt'],'acquisition_receipt_sha256')]:
        if base.sha(file.read_bytes())!=metadata[key]:raise ValueError('Frozen input changed')
    claims=[ClaimRecord.model_validate_json(s) for s in (output/'manifest.jsonl').read_text().splitlines()]
    packets=[EvidencePacket.model_validate_json(s) for s in (output/'evidence_packets.jsonl').read_text().splitlines()]
    if packets!=[EvidencePacket(claim=c) for c in claims]:raise ValueError('Packet mismatch')
    audit=json.loads((output/'dataset_audit.json').read_text());splits=json.loads((output/'splits.json').read_text());exclusions=json.loads((output/'exclusions.json').read_text())
    report=validate(claims,audit,splits,config,registry,exclusions)
    if report!=json.loads((output/'validation.json').read_text()):raise ValueError('Validation report mismatch')
    if verify_images:
        if audit_full(root,config)!=audit:raise ValueError('Full dataset audit changed')
        rebuilt,rejected=generate(root,audit,splits,config,registry)
        if rebuilt!=claims or rejected!=exclusions:raise ValueError('Deterministic regeneration failed')
        for c in claims:
            if c.image_path and base.sha((root/c.image_path).read_bytes())!=c.transformation.image_sha256:raise ValueError('Image integrity failure')
            p=c.transformation.parameters
            if 'mask_path' in p and base.sha((root/p['mask_path']).read_bytes())!=p['mask_sha256']:raise ValueError('Mask integrity failure')
    return report
