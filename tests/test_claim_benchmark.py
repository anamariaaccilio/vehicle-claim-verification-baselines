"""Canonical manifest checks run without raw data; generation uses tiny fixtures."""
import copy
import json
from pathlib import Path
import subprocess

import numpy as np
from PIL import Image
import pytest
import yaml
from pydantic import ValidationError

from src.data.claim_benchmark import (
    build_benchmark, canonical, frozen_splits, validate_bundle, validate_claims,
)
from src.data.duplicate_audit import group_sources, image_fingerprints
from src.schemas.claim import ClaimRecord, Split
from src.schemas.evidence import DecisionLabel, HITL_TO_CANONICAL
from src.schemas.packet import EvidencePacket

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT/'data/manifests/benchmark_v1'
CONFIG = ROOT/'configs/benchmark_v1.yaml'


@pytest.fixture
def frozen():
    claims = [ClaimRecord.model_validate_json(line) for line in (OUTPUT/'manifest.jsonl').read_text().splitlines()]
    audit = json.loads((OUTPUT/'dataset_audit.json').read_text())
    splits = json.loads((OUTPUT/'splits.json').read_text())
    config = yaml.safe_load(CONFIG.read_text())
    registry = yaml.safe_load((ROOT/config['conditions_config']).read_text())['conditions']
    return claims, audit, splits, config, registry


def test_real_manifest_schema_ids_and_sources(frozen):
    claims, audit, *_ = frozen
    assert len({c.claim_id for c in claims}) == len(claims)
    assert {c.source_image_id for c in claims} == {s['source_image_id'] for s in audit['sources']}
    assert all(c.condition and c.provenance.synthetic_claim and c.annotation_reference for c in claims)
    assert all(c.image_path is None or not Path(c.image_path).is_absolute() for c in claims)
    assert validate_bundle(ROOT, OUTPUT, CONFIG)['result'] == 'PASS'


def test_claim_and_packet_roundtrip_and_no_fabricated_specialists(frozen):
    for claim in frozen[0]:
        assert ClaimRecord.model_validate_json(claim.model_dump_json()) == claim
        packet = EvidencePacket(claim=claim)
        restored = EvidencePacket.model_validate_json(packet.model_dump_json())
        assert restored == packet
        assert all(getattr(restored, k) is None for k in ('narrative','visual','forensic','image_quality'))


def test_variants_preserve_source_parent_split_and_provenance(frozen):
    claims = frozen[0]
    parents = {c.source_image_id:c for c in claims if c.condition == 'C0'}
    for claim in claims:
        parent = parents[claim.source_image_id]
        assert claim.provenance == parent.provenance
        assert claim.annotation_reference == parent.annotation_reference
        assert claim.split == parent.split
        assert claim.transformation.seed == parent.transformation.seed
        assert claim.parent_claim_id == (None if claim.condition == 'C0' else parent.claim_id)


def test_c0_semantic_invariants_and_missing_modalities(frozen):
    for claim in frozen[0]:
        if claim.condition == 'C0':
            assert claim.narrative_text and claim.image_path
            assert claim.annotated_damage_classes
            assert claim.transformation.image_sha256 == claim.provenance.source_image_sha256
            assert claim.expected_label == DecisionLabel.SUPPORTED
        elif claim.condition == 'C1':
            assert claim.transformation.parameters['denied_annotated_class'] in claim.annotated_damage_classes
        elif claim.condition == 'C6':
            assert claim.narrative_text is None and claim.image_path
        elif claim.condition == 'C7':
            assert claim.image_path is None and claim.narrative_text


def test_condition_registry_preserves_user_taxonomy(frozen):
    claims, _, _, _, registry = frozen
    assert set(registry) == {f'C{i}' for i in range(11)}
    assert registry['C10']['expected_label'] == 'OOD'
    assert registry['C8']['expected_label'] == 'SUPPORTED'
    assert registry['C9']['expected_label'] == 'INSUFFICIENT'
    assert all(c.expected_label.value == registry[c.condition]['expected_label'] for c in claims)
    assert not any(c.condition in ('C2','C3','C4','C5','C10') for c in claims)


def test_frozen_split_is_deterministic_and_source_grouped(frozen):
    claims, audit, splits, config, _ = frozen
    assert frozen_splits(audit, config) == splits
    reverse = copy.deepcopy(audit)
    reverse['sources'].reverse()
    assert frozen_splits(reverse, config) == splits
    for group, members in splits['groups'].items():
        assert len({splits['sources'][member]['split'] for member in members}) == 1
    assert validate_claims(*frozen)['overlap'] == {'train/validation':[], 'train/test':[], 'validation/test':[]}


@pytest.mark.parametrize('tamper', ['id','source','split','label','parent','narrative','provenance','c1_target'])
def test_auditor_rejects_semantic_and_leakage_corruption(frozen, tamper):
    claims, audit, splits, config, registry = frozen
    claims = [c.model_copy(deep=True) for c in claims]
    claim = next(c for c in claims if c.condition == 'C1')
    if tamper == 'id': claim.claim_id = 'invented'
    if tamper == 'source': claim.source_image_id = 'unknown'
    if tamper == 'split': claim.split = Split.TEST if claim.split != Split.TEST else Split.TRAIN
    if tamper == 'label': claim.expected_label = DecisionLabel.SUPPORTED
    if tamper == 'parent': claim.parent_claim_id = 'invented'
    if tamper == 'narrative': claim.narrative_text = 'Placa y propietario inventados'
    if tamper == 'provenance': claim.provenance.annotation_sha256 = '0'*64
    if tamper == 'c1_target': claim.transformation.parameters['denied_annotated_class'] = 'invented'
    with pytest.raises(ValueError):
        validate_claims(claims, audit, splits, config, registry)


def test_schema_rejects_incomplete_condition_and_unknown_labels():
    with pytest.raises(ValidationError):
        ClaimRecord(claim_id='x', condition='C0')
    with pytest.raises(ValidationError):
        ClaimRecord(claim_id='x', expected_label='FRAUD_CONFIRMED')


def test_duplicates_and_near_duplicates_are_transitively_grouped():
    def source(identifier, dhash):
        return {'source_image_id':identifier, 'file_sha256':identifier, 'pixel_sha256':identifier, 'dhash128':f'{dhash:032x}'}
    sources = [source('a',0),source('b',7),source('c',63)]
    grouped = group_sources(sources, threshold=3)
    assert grouped['groups'] == {'a':['a','b','c']}
    assert group_sources(list(reversed(sources)), threshold=3) == grouped
    assert len(grouped['pairs']) == 2
    audit={'duplicates':grouped}
    split=frozen_splits(audit, {'seed':42,'near_duplicate_hamming_threshold':3,'split':{'train':.7,'validation':.15,'test':.15}})
    assert len({row['split'] for row in split['sources'].values()}) == 1


def test_pixel_duplicates_group_despite_different_encoding(tmp_path):
    original = Image.fromarray(np.random.default_rng(42).integers(0,255,(20,20,3),dtype=np.uint8))
    original.save(tmp_path/'a.png', compress_level=0)
    original.save(tmp_path/'b.png', compress_level=9)
    a = {'source_image_id':'a', **image_fingerprints(tmp_path/'a.png')}
    b = {'source_image_id':'b', **image_fingerprints(tmp_path/'b.png')}
    assert a['file_sha256'] != b['file_sha256']
    assert a['pixel_sha256'] == b['pixel_sha256']
    assert group_sources([a,b])['groups'] == {'a':['a','b']}


def test_small_generation_is_deterministic_and_preserves_raw(tmp_path):
    root = tmp_path
    dataset = root/'raw/hitl'
    (dataset/'File1/ann').mkdir(parents=True)
    (dataset/'File1/img').mkdir()
    (dataset/'meta.json').write_text(json.dumps({'classes':[{'title':key} for key in HITL_TO_CANONICAL]}))
    original = np.random.default_rng(42).integers(0,255,(40,60,3),dtype=np.uint8)
    for name in ('a','b'):
        Image.fromarray(original).save(dataset/f'File1/img/{name}.png')
        annotation={'size':{'width':60,'height':40},'objects':[{'classTitle':'Dent','geometryType':'polygon',
                     'points':{'exterior':[[1,1],[15,1],[15,15]],'interior':[]}}]}
        (dataset/f'File1/ann/{name}.png.json').write_text(json.dumps(annotation))
    raw_before = {str(p):p.read_bytes() for p in dataset.rglob('*') if p.is_file()}
    config=yaml.safe_load(CONFIG.read_text())
    config['dataset_dir']='raw/hitl'
    config['conditions_config']='conditions.yaml'
    config['acquisition_receipt']='receipt.json'
    (root/'conditions.yaml').write_bytes((ROOT/'configs/benchmark_conditions.yaml').read_bytes())
    (root/'receipt.json').write_text('{}')
    (root/'config.yaml').write_text(yaml.safe_dump(config))
    first=build_benchmark(root, root/'config.yaml', root/'first')
    second=build_benchmark(root, root/'config.yaml', root/'second')
    assert first==second
    assert {str(p):p.read_bytes() for p in dataset.rglob('*') if p.is_file()}==raw_before
    for path in (root/'first').iterdir():
        assert path.read_bytes() == (root/'second'/path.name).read_bytes()
    assert validate_bundle(root, root/'first', root/'config.yaml', verify_images=True)['result']=='PASS'
    split=json.loads((root/'first/splits.json').read_text())
    assert len({s['split'] for s in split['sources'].values()})==1


def test_frozen_hash_rejects_changed_manifest(tmp_path):
    for path in OUTPUT.iterdir():
        if path.is_file(): (tmp_path/path.name).write_bytes(path.read_bytes())
    with (tmp_path/'manifest.jsonl').open('ab') as stream: stream.write(b'\n')
    with pytest.raises(ValueError, match='hash mismatch'):
        validate_bundle(ROOT,tmp_path,CONFIG)


def test_no_raw_images_weights_secrets_or_cache_tracked():
    tracked = subprocess.check_output(['git','ls-files','-z'],cwd=ROOT).decode().split('\0')
    forbidden_dirs = {'.venv','__pycache__','.pytest_cache','.cache'}
    for item in filter(None,tracked):
        path=Path(item)
        assert not (forbidden_dirs & set(path.parts))
        assert not path.name.startswith('.env')
        assert not ('raw' in path.parts and path.name != '.gitkeep')
        assert path.suffix.lower() not in {'.png','.jpg','.jpeg','.pt','.pth','.ckpt','.onnx','.safetensors'}
