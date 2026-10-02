"""C0-C10 contract, donor leakage, held-out family, and actual pixel operations."""
import copy
import json
from pathlib import Path

import numpy as np
import pytest
from PIL import Image
from pydantic import ValidationError

from src.data.benchmark_v2 import (check, load_config, validate, donor_for,
                                  localized_transform, annotation_masks)
from src.schemas.claim import ClaimRecord
from src.schemas.evidence import DecisionLabel
from src.schemas.packet import EvidencePacket

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'data/manifests/benchmark_v2'
CONFIG=ROOT/'configs/benchmark_v2.yaml'

@pytest.fixture
def frozen():
    config,registry=load_config(ROOT,CONFIG)
    claims=[ClaimRecord.model_validate_json(line) for line in (OUT/'manifest.jsonl').read_text().splitlines()]
    audit=json.loads((OUT/'dataset_audit.json').read_text())
    splits=json.loads((OUT/'splits.json').read_text())
    return claims,audit,splits,config,registry


def test_frozen_complete_manifest_and_packets(frozen):
    claims,*_=frozen
    assert check(ROOT,CONFIG,OUT)['result']=='PASS'
    assert {c.condition for c in claims}=={f'C{i}' for i in range(11)}
    assert len({c.claim_id for c in claims})==len(claims)
    for c in claims:
        assert ClaimRecord.model_validate_json(c.model_dump_json())==c
        packet=EvidencePacket(claim=c)
        assert EvidencePacket.model_validate_json(packet.model_dump_json())==packet
        assert all(getattr(packet,k) is None for k in ('narrative','visual','forensic','image_quality'))


def test_source_splits_preserved_and_donors_independent_same_split(frozen):
    claims,audit,splits,config,_=frozen
    assert splits==json.loads((ROOT/'data/manifests/benchmark_v1/splits.json').read_text())
    sources={s['source_image_id']:s for s in audit['sources']}
    for c in claims:
        if c.condition!='C2': continue
        donor=donor_for(sources[c.source_image_id],audit,splits,config['seed'])
        donor_id=donor['source_image_id']
        assert c.transformation.donor_source_image_ids==[donor_id]
        assert splits['sources'][donor_id]['split']==c.split.value
        assert splits['sources'][donor_id]['group_id']!=c.provenance.source_group_id
        assert donor_for(sources[c.source_image_id],{**audit,'sources':list(reversed(audit['sources']))},splits,config['seed'])==donor


def test_ood_is_test_only_and_not_a_supervised_decision_label(frozen):
    claims=frozen[0]
    ood=[c for c in claims if c.condition=='C10']
    assert ood and all(c.split.value=='test' and c.expected_label.value=='OOD' for c in ood)
    assert 'OOD' not in {v.value for v in DecisionLabel}
    assert all(c.condition=='C10' for c in claims if c.transformation.operation=='localized_rgb_inversion')
    payload=ood[0].model_dump(mode='json')
    for field,value in [('split','train'),('condition','C0'),('schema_version','0.2.0')]:
        with pytest.raises(ValidationError): ClaimRecord.model_validate({**payload,field:value})


@pytest.mark.parametrize('field',['donor','parent','split','mask','label','operation','narrative','annotation'])
def test_tampered_new_conditions_rejected(frozen,field):
    claims,audit,splits,config,registry=frozen
    claims=copy.deepcopy(claims)
    c=next(c for c in claims if c.condition==('C2' if field=='donor' else 'C5'))
    if field=='donor': c.transformation.donor_source_image_ids=['unknown']
    if field=='parent': c.parent_claim_id='unknown'
    if field=='split': c.split=next(x.split for x in claims if x.split!=c.split)
    if field=='mask': c.transformation.parameters['mask_path']='wrong.png'
    if field=='label': c.expected_label=DecisionLabel.SUPPORTED
    if field=='operation': c.transformation.operation='localized_rgb_inversion'
    if field=='narrative': c.narrative_text='Invented owner and vehicle plate'
    if field=='annotation': c.annotation_reference='wrong.json'
    with pytest.raises(ValueError): validate(claims,audit,splits,config,registry)


@pytest.fixture
def pixels(tmp_path):
    original=np.random.default_rng(42).integers(0,256,(100,120,3),dtype=np.uint8)
    Image.fromarray(original).save(tmp_path/'original.png')
    ann={'objects':[{'points':{'exterior':[[40,40],[55,40],[55,55],[40,55]]}}]}
    (tmp_path/'ann.json').write_text(json.dumps(ann))
    source={'source_image_id':'fixture','image_path':'original.png','annotation_reference':'ann.json','height':100,'width':120}
    config={'copy_patch_size':24,'inpaint_radius':3,'seed':42}
    return tmp_path,source,config,original


@pytest.mark.parametrize('condition',['C3','C4','C5','C10'])
def test_actual_localized_pixels_and_determinism(pixels,condition):
    root,source,config,original=pixels
    before={p.name:p.read_bytes() for p in root.iterdir()}
    result,parameters=localized_transform(root,source,condition,config)
    second,parameters2=localized_transform(root,source,condition,config)
    output,mask,operation=result
    assert np.array_equal(output,second[0]) and np.array_equal(mask,second[1]) and parameters==parameters2
    changed=np.any(original!=output,axis=2)
    assert changed.any() and not changed[mask==0].any()
    assert parameters['changed_pixels']==int(changed.sum())
    if condition in ('C3','C5'):
        union=np.maximum.reduce([m for _,m in annotation_masks(root,source)])
        assert np.array_equal(output[union>0],original[union>0])
        sx,sy,ex,ey=parameters['source_box']; dx,dy,fx,fy=parameters['destination_box']
        assert np.array_equal(output[dy:fy,dx:fx],original[sy:ey,sx:ex])
    if condition=='C10': assert np.array_equal(output[mask>0],255-original[mask>0])
    if condition=='C4': assert parameters['damage_removal_verified'] is False
    assert {p.name:p.read_bytes() for p in root.iterdir()}==before


def test_no_donor_never_borrows_from_other_split():
    source={'source_image_id':'a'}
    audit={'sources':[source,{'source_image_id':'b'}]}
    splits={'sources':{'a':{'split':'train','group_id':'a'},'b':{'split':'test','group_id':'b'}}}
    assert donor_for(source,audit,splits,42) is None


def test_missing_required_variant_is_rejected(frozen):
    claims,audit,splits,config,registry=frozen
    target=next(c.claim_id for c in claims if c.condition=='C4')
    with pytest.raises(ValueError,match='Missing required'):
        validate([c for c in claims if c.claim_id!=target],audit,splits,config,registry)
