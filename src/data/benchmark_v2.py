"""Controlled C0-C10 extension. Frozen v1 remains readable and reproducible.

Targets are experimental interventions, never insurer/fraud ground truth.
C10 is a held-out manipulation family, not a fourth supervised decision class.
"""
from collections import Counter, defaultdict
import io
import json
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, __version__ as pillow_version
import yaml

from src.data import claim_benchmark as base
from src.schemas.claim import ClaimRecord, ClaimTransformation
from src.schemas.packet import EvidencePacket

EXTRA = ('C2', 'C3', 'C4', 'C5', 'C10')


def load_config(root, path):
    config = yaml.safe_load(path.read_text())
    registry = yaml.safe_load((root/config['conditions_config']).read_text())['conditions']
    if set(config['conditions']) != {f'C{i}' for i in range(11)}:
        raise ValueError('v2 must declare the complete authorized taxonomy')
    return config, registry


def base_config(config):
    return {**config, 'conditions': [c for c in config['conditions'] if c in base.ACTIVE]}


def png_bytes(array):
    buffer = io.BytesIO()
    Image.fromarray(array).save(buffer, format='PNG', compress_level=9)
    return buffer.getvalue()


def annotation_masks(root, source):
    doc = json.loads((root/source['annotation_reference']).read_text())
    masks = []
    for index, obj in enumerate(doc['objects']):
        mask = np.zeros((source['height'], source['width']), np.uint8)
        points = np.rint(obj['points']['exterior']).astype(np.int32)
        cv2.fillPoly(mask, [points], 255)
        masks.append((index, mask))
    if not masks:
        raise ValueError('No annotated damage mask')
    return masks


def localized_transform(root, source, condition, config):
    with Image.open(root/source['image_path']) as image:
        original = np.asarray(image.convert('RGB')).copy()
    masks = annotation_masks(root, source)
    # Fixed geometry rule; never learned from test/validation statistics.
    index, selected = min(masks, key=lambda pair: (np.count_nonzero(pair[1]), pair[0]))
    union = np.maximum.reduce([mask for _, mask in masks])
    params = {'annotation_object_index': index, 'mask_selection': 'smallest rasterized damage polygon; index tie-break',
              'human_realism_review': 'NOT PERFORMED'}
    if condition in ('C3', 'C5'):
        # Copy a small window centered on an annotated pixel. Destination must
        # not intersect ANY original damage: C5's denied damage remains intact.
        ys, xs = np.nonzero(selected)
        center = len(xs)//2
        size = config['copy_patch_size']
        height, width = selected.shape
        size = min(size, height, width)
        sx = max(0, min(int(xs[center])-size//2, width-size))
        sy = max(0, min(int(ys[center])-size//2, height-size))
        candidates = [(x,y) for y in range(0,height-size+1,size)
                      for x in range(0,width-size+1,size)
                      if not union[y:y+size,x:x+size].any()
                      and (x+size<=sx or sx+size<=x or y+size<=sy or sy+size<=y)]
        if not candidates:
            return None, {'reason':'No copy destination outside all original damage masks'}
        offset = base.stable_index(source['source_image_id'], config['seed'], 'copy-destination', len(candidates))
        dx,dy = candidates[offset]
        mask = np.zeros_like(selected)
        mask[dy:dy+size,dx:dx+size] = 255
        result = original.copy()
        result[dy:dy+size,dx:dx+size] = original[sy:sy+size,sx:sx+size]
        params.update(source_box=[sx,sy,sx+size,sy+size], destination_box=[dx,dy,dx+size,dy+size],
                      original_damage_pixels_preserved=True)
        operation = 'localized_copy_move'
    elif condition == 'C4':
        mask = selected
        result = cv2.inpaint(original, mask, config['inpaint_radius'], cv2.INPAINT_TELEA)
        params.update(algorithm='OpenCV INPAINT_TELEA', radius=config['inpaint_radius'],
                      damage_removal_verified=False)
        operation = 'damage_mask_inpainting'
    elif condition == 'C10':
        # Photometric tampering is reserved entirely for test. Unlike benign
        # JPEG, local inversion deliberately changes the evidence appearance.
        mask = selected
        result = original.copy()
        result[mask > 0] = 255-original[mask > 0]
        params.update(held_out_family='localized_rgb_inversion', allowed_split='test')
        operation = 'localized_rgb_inversion'
    else:
        raise ValueError('Unsupported localized transformation')
    changed = np.any(original != result, axis=2)
    if not changed.any() or np.any(changed & (mask == 0)):
        raise ValueError('Transformation must change pixels only inside its declared mask')
    params.update(changed_pixels=int(changed.sum()), mask_pixels=int(np.count_nonzero(mask)),
                  changed_fraction=float(changed.mean()))
    return (result, mask, operation), params


def donor_for(source, audit, splits, seed):
    # Same split AND a different duplicate component; no assumption that absent
    # damage annotations establish an undamaged vehicle or semantic negation.
    own = splits['sources'][source['source_image_id']]
    candidates = sorted((s for s in audit['sources']
                         if splits['sources'][s['source_image_id']]['split'] == own['split']
                         and splits['sources'][s['source_image_id']]['group_id'] != own['group_id']),
                        key=lambda s:s['source_image_id'])
    if not candidates:
        return None
    return candidates[base.stable_index(source['source_image_id'],seed,'image-substitution',len(candidates))]


def generate(root, audit, splits, config, registry):
    claims, exclusions = base.generate_claims(root, audit, splits, base_config(config), registry)
    for claim in claims:
        claim.schema_version = '0.3.0'
    parents = {c.source_image_id:c for c in claims if c.condition == 'C0'}
    for source in audit['sources']:
        parent = parents[source['source_image_id']]
        for condition in EXTRA:
            if condition == 'C10' and parent.split.value != 'test':
                continue  # By design; never a training/validation family.
            identifier = base.claim_id(source, condition, config)
            donors = []
            text = parent.narrative_text
            if condition == 'C2':
                donor = donor_for(source,audit,splits,config['seed'])
                if donor is None:
                    exclusions.append({'source_image_id':source['source_image_id'],'condition':condition,
                                       'reason':'No independent donor in the same split'})
                    continue
                donors = [donor['source_image_id']]
                path, image_sha = donor['image_path'], donor['file_sha256']
                operation = 'same_split_image_substitution'
                params = {'donor_annotation_reference':donor['annotation_reference'],
                          'donor_annotation_sha256':donor['annotation_sha256'],
                          'donor_image_sha256':image_sha,
                          'semantics':'known controlled expediente substitution; visual contradiction not guaranteed'}
            else:
                result, params = localized_transform(root, source, condition, config)
                if result is None:
                    exclusions.append({'source_image_id':source['source_image_id'],'condition':condition,**params})
                    continue
                pixels, mask, operation = result
                path = f'data/processed/benchmark_v2/{identifier}.png'
                mask_path = f'data/processed/benchmark_v2/{identifier}.mask.png'
                content, mask_content = png_bytes(pixels), png_bytes(mask)
                base.write_verified(root/path, content)
                base.write_verified(root/mask_path, mask_content)
                image_sha = base.sha(content)
                params.update(mask_path=mask_path,mask_sha256=base.sha(mask_content))
                if condition == 'C5':
                    _, template, denied = base.narrative(source,config['seed'])
                    text = base.NEGATIVE[int(template.rsplit('-',1)[1])].format(damage=base.DAMAGE_TERMS[denied])
                    params['denied_annotated_class'] = denied
            payload = parent.model_dump(mode='json')
            payload.update(claim_id=identifier,condition=condition,parent_claim_id=parent.claim_id,
                           image_path=path,narrative_text=text,expected_label=registry[condition]['expected_label'],
                           transformation=ClaimTransformation(operation=operation,parameters=params,seed=config['seed'],
                                              image_sha256=image_sha,donor_source_image_ids=donors).model_dump(mode='json'))
            claims.append(ClaimRecord.model_validate(payload))
    return sorted(claims,key=lambda c:(c.source_image_id,int(c.condition[1:]))), exclusions


def validate(claims,audit,splits,config,registry):
    def require(ok,message):
        if not ok: raise ValueError(message)
    basic = [c for c in claims if c.condition in base.ACTIVE]
    base.validate_claims(basic,audit,splits,base_config(config),registry)
    require(len({c.claim_id for c in claims}) == len(claims),'Duplicate claim ID')
    sources = {s['source_image_id']:s for s in audit['sources']}
    parents = {c.source_image_id:c for c in basic if c.condition == 'C0'}
    images = defaultdict(set)
    families = defaultdict(set)
    for c in claims:
        require(c.source_image_id in sources,'Unknown source')
        require(c.schema_version == '0.3.0','Expected versioned schema')
        require(c.expected_label.value == registry[c.condition]['expected_label'],'Taxonomy label mismatch')
        parent = parents[c.source_image_id]
        require(c.split == parent.split and c.provenance == parent.provenance,'Provenance/split mismatch')
        require(c.annotation_reference == parent.annotation_reference and c.annotated_damage_classes == parent.annotated_damage_classes,'Annotation provenance mismatch')
        require(c.transformation.seed == config['seed'],'Seed mismatch')
        if c.transformation.image_sha256:
            images[c.transformation.image_sha256].add(c.split.value)
        families[c.transformation.operation].add(c.split.value)
        if c.condition not in EXTRA: continue
        source = sources[c.source_image_id]
        require(c.claim_id == base.claim_id(source,c.condition,config),'Unstable variant ID')
        require(c.parent_claim_id == parent.claim_id,'Invalid parent')
        p = c.transformation.parameters
        if c.condition == 'C2':
            donor = donor_for(source,audit,splits,config['seed'])
            require(donor is not None,'Donor unavailable')
            require(c.transformation.operation == 'same_split_image_substitution','Wrong substitution')
            require(c.transformation.donor_source_image_ids == [donor['source_image_id']],'Donor selection/split violation')
            require(c.image_path == donor['image_path'] and c.transformation.image_sha256 == donor['file_sha256'],'Donor image mismatch')
            require(p.get('donor_annotation_reference') == donor['annotation_reference'] and p.get('donor_annotation_sha256') == donor['annotation_sha256'] and p.get('donor_image_sha256') == donor['file_sha256'],'Donor provenance mismatch')
        else:
            operations = {'C3':'localized_copy_move','C4':'damage_mask_inpainting','C5':'localized_copy_move','C10':'localized_rgb_inversion'}
            require(c.transformation.operation == operations[c.condition],'Incorrect manipulation family')
            require(not c.transformation.donor_source_image_ids,'Unexpected external donor')
            require(c.image_path == f'data/processed/benchmark_v2/{c.claim_id}.png','Derived path mismatch')
            require(p.get('mask_path') == f'data/processed/benchmark_v2/{c.claim_id}.mask.png','Missing mask provenance')
            require(len(p.get('mask_sha256','')) == 64 and c.transformation.image_sha256,'Missing image/mask hashes')
            require(0 < p.get('changed_pixels',0) <= p.get('mask_pixels',0) <= source['width']*source['height'],'Invalid locality counts')
            require(p.get('human_realism_review') == 'NOT PERFORMED','Unsupported realism claim')
        expected_text = parent.narrative_text
        if c.condition == 'C5':
            _, template, denied = base.narrative(source,config['seed'])
            require(p.get('denied_annotated_class') == denied and p.get('original_damage_pixels_preserved') is True,'C5 contradiction not preserved')
            expected_text = base.NEGATIVE[int(template.rsplit('-',1)[1])].format(damage=base.DAMAGE_TERMS[denied])
        require(c.narrative_text == expected_text,'Variant narrative mismatch')
        if c.condition == 'C4':
            require(p.get('algorithm') == 'OpenCV INPAINT_TELEA' and p.get('radius') == config['inpaint_radius'] and p.get('damage_removal_verified') is False,'Inpainting protocol mismatch')
        if c.condition == 'C10':
            require(c.split.value == 'test' and p.get('held_out_family') == 'localized_rgb_inversion','OOD family leakage')
    require(all(len(v)==1 for v in images.values()),'Exact image cross-split leakage')
    require(families.get('localized_rgb_inversion') == {'test'},'Held-out family absent or leaked')
    require({c.condition for c in claims} == set(registry),'Incomplete condition coverage')
    coverage={(c.source_image_id,c.condition) for c in claims}
    for source_id, assignment in splits['sources'].items():
        for condition in ('C2','C3','C4','C5'):
            require((source_id,condition) in coverage,'Missing required source variant')
        require(((source_id,'C10') in coverage) == (assignment['split']=='test'),'Incomplete or leaked OOD source coverage')
    return {'result':'PASS','claims':len(claims),
            'conditions':dict(sorted(Counter(c.condition for c in claims).items(),key=lambda p:int(p[0][1:]))),
            'claims_per_split':dict(Counter(c.split.value for c in claims)),
            'sources_per_split':dict(Counter(v['split'] for v in splits['sources'].values())),
            'overlap':{'train/validation':[],'train/test':[],'validation/test':[]},
            'exact_image_cross_split_leakage':False,'donor_cross_split_leakage':False,
            'manipulation_families_per_split':{key:sorted(values) for key,values in sorted(families.items())},
            'ood_scope':'localized_rgb_inversion held out from train and validation; no model trained'}


def build(root,config_path,output):
    config,registry = load_config(root,config_path)
    audit = base.audit_dataset(root,config['dataset_dir'],config['near_duplicate_hamming_threshold'])
    splits = base.frozen_splits(audit,config)
    # Freeze the same source assignments as v1; new conditions cannot reshuffle.
    if splits != json.loads((root/'data/manifests/benchmark_v1/splits.json').read_text()):
        raise ValueError('Source splits changed from frozen v1')
    claims,exclusions = generate(root,audit,splits,config,registry)
    report = validate(claims,audit,splits,config,registry)
    artifacts = {'manifest.jsonl':b''.join(base.canonical(c.model_dump(mode='json')) for c in claims),
                 'evidence_packets.jsonl':b''.join(base.canonical(EvidencePacket(claim=c).model_dump(mode='json')) for c in claims),
                 'splits.json':base.canonical(splits),'dataset_audit.json':base.canonical(audit),
                 'validation.json':base.canonical(report),'exclusions.json':base.canonical(exclusions)}
    metadata={'benchmark_version':config['benchmark_version'],'generator_version':config['generator_version'],'schema_version':'0.3.0',
              'config_sha256':base.sha(config_path.read_bytes()),'conditions_sha256':base.sha((root/config['conditions_config']).read_bytes()),
              'acquisition_receipt_sha256':base.sha((root/config['acquisition_receipt']).read_bytes()),
              'artifacts_sha256':{name:base.sha(content) for name,content in artifacts.items()},
              'runtime':{'Pillow':pillow_version,'numpy':np.__version__,'opencv':cv2.__version__},
              'limitations':['synthetic claims, not insurer records','no human realism review','C2 substitution can be visually indistinguishable',
                             'C4 inpainting operation verified, successful damage removal not certified','C10 procedural holdout only; no training yet']}
    artifacts['metadata.json']=base.canonical(metadata)
    for name,content in artifacts.items(): base.write_verified(output/name,content)
    return {**report,'manifest_sha256':base.sha(artifacts['manifest.jsonl']),'excluded':len(exclusions)}


def check(root,config_path,output,verify_images=False):
    config,registry=load_config(root,config_path)
    metadata=json.loads((output/'metadata.json').read_text())
    for name,expected in metadata['artifacts_sha256'].items():
        if base.sha((output/name).read_bytes())!=expected: raise ValueError(f'Artifact hash mismatch: {name}')
    for path,key in [(config_path,'config_sha256'),(root/config['conditions_config'],'conditions_sha256'),
                     (root/config['acquisition_receipt'],'acquisition_receipt_sha256')]:
        if base.sha(path.read_bytes())!=metadata[key]: raise ValueError(f'Changed frozen input: {path}')
    claims=[ClaimRecord.model_validate_json(line) for line in (output/'manifest.jsonl').read_text().splitlines()]
    packets=[EvidencePacket.model_validate_json(line) for line in (output/'evidence_packets.jsonl').read_text().splitlines()]
    if len(claims)!=len(packets) or any(p != EvidencePacket(claim=c) for c,p in zip(claims,packets)):
        raise ValueError('Packet/claim mismatch or fabricated specialist output')
    audit=json.loads((output/'dataset_audit.json').read_text())
    splits=json.loads((output/'splits.json').read_text())
    if splits != json.loads((root/'data/manifests/benchmark_v1/splits.json').read_text()):
        raise ValueError('Source assignments changed from v1')
    report=validate(claims,audit,splits,config,registry)
    if report != json.loads((output/'validation.json').read_text()): raise ValueError('Validation report mismatch')
    if verify_images:
        actual=base.audit_dataset(root,config['dataset_dir'],config['near_duplicate_hamming_threshold'])
        if actual != audit: raise ValueError('Dataset fingerprint/duplicate audit changed')
        regenerated,exclusions=generate(root,actual,splits,config,registry)
        if regenerated != claims or exclusions != json.loads((output/'exclusions.json').read_text()):
            raise ValueError('Deterministic regeneration mismatch')
        for c in claims:
            if c.image_path and base.sha((root/c.image_path).read_bytes())!=c.transformation.image_sha256:
                raise ValueError('Image bytes changed')
            p=c.transformation.parameters
            if 'mask_path' in p and base.sha((root/p['mask_path']).read_bytes())!=p['mask_sha256']:
                raise ValueError('Mask bytes changed')
    return report
