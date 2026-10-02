"""Canonical controlled-claim benchmark. No training or specialist inference."""
from __future__ import annotations

from collections import Counter, defaultdict
import hashlib
import io
import json
import math
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageFilter, __version__ as pillow_version
import yaml

from src.data.duplicate_audit import image_fingerprints, group_sources
from src.data.hitl_supervisely import parse_hitl_supervisely
from src.data.split import assign_splits
from src.schemas.claim import ClaimRecord, ClaimProvenance, ClaimTransformation, Split
from src.schemas.packet import EvidencePacket, SCHEMA_VERSION

DAMAGE_TERMS = {
    'dent': 'abolladuras', 'crack': 'grietas', 'scratch': 'rayones',
    'flaking': 'desprendimientos de pintura', 'broken_part': 'piezas rotas',
    'paint_chip': 'pequeños desconchados de pintura', 'missing_part': 'piezas faltantes',
    'corrosion': 'corrosión',
}
POSITIVE = ('El vehículo presenta {damage}.', 'La fotografía del vehículo permite observar {damage}.',
            'La imagen del vehículo muestra {damage}.')
NEGATIVE = ('El vehículo no presenta {damage}.', 'En el vehículo no hay {damage}.',
            'El vehículo está libre de {damage}.')
ACTIVE = {'C0', 'C1', 'C6', 'C7', 'C8', 'C9'}


def canonical(value) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)+'\n').encode()


def sha(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def write_verified(path: Path, content: bytes) -> None:
    if path.exists():
        if path.read_bytes() != content:
            raise ValueError(f'Refusing to overwrite changed artifact: {path}')
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as stream:
        stream.write(content)


def audit_dataset(root: Path, dataset_dir: str, threshold: int) -> dict:
    dataset = root / dataset_dir
    records = parse_hitl_supervisely(dataset, relative_to=root)
    images = sorted(p for p in dataset.glob('*/img/*') if p.is_file())
    annotations = sorted(dataset.glob('*/ann/*.json'))
    missing = [str(p.relative_to(root)) for p in images
               if not (p.parent.parent/'ann'/(p.name+'.json')).is_file()]
    # The strict reader has validated every annotation object/image pair.
    # Fail closed on orphan images rather than silently excluding them.
    if missing:
        raise ValueError(f'Images without annotations: {missing}')
    sources = []
    for record in records:
        image_path = Path(record.path)
        reference = (image_path.parent.parent/'ann'/(image_path.name+'.json')).as_posix()
        sources.append({'source_image_id': record.source_image_id, 'image_path': record.path,
                        'annotation_reference': reference,
                        'annotation_sha256': sha((root/reference).read_bytes()),
                        'annotation_count': len(record.annotations), 'damage_classes': sorted(record.damage_classes),
                        **image_fingerprints(root/record.path)})
    sources.sort(key=lambda item: item['source_image_id'])
    return {'dataset': 'humansintheloop/car-parts-and-car-damages', 'dataset_version': 2,
            'local_path': dataset_dir, 'images': len(images), 'annotation_files': len(annotations),
            'annotations': sum(len(record.annotations) for record in records),
            'class_instances': dict(sorted(Counter(ann.damage_class for record in records for ann in record.annotations).items())),
            'images_without_annotation_file': missing,
            'images_without_annotations': [record.source_image_id for record in records if not record.annotations],
            'invalid_annotations': 0, 'invalid_images': 0,
            'integrity_scope': 'All objects passed strict class/type/finite-coordinate/bounds/nonzero-area/exterior validation; all images decoded with matching dimensions',
            'sources': sources, 'duplicates': group_sources(sources, threshold)}


def frozen_splits(audit: dict, config: dict) -> dict:
    grouping = audit['duplicates']
    assignment = assign_splits(list(grouping['groups']), seed=config['seed'],
                               ratios={Split(key): value for key, value in config['split'].items()})
    return {'seed': config['seed'], 'ratios': config['split'],
            'method': 'Connected duplicate components first; canonical seed+group-ID hash second; claims last',
            'near_duplicate_threshold': config['near_duplicate_hamming_threshold'],
            'groups': grouping['groups'],
            'sources': {source: {'group_id': group, 'split': assignment[group].value}
                        for source, group in sorted(grouping['source_to_group'].items())}}


def stable_index(source_id: str, seed: int, namespace: str, length: int) -> int:
    return int(sha(f'{namespace}:{seed}:{source_id}'.encode()), 16) % length


def narrative(source: dict, seed: int) -> tuple[str, str, str]:
    classes = source['damage_classes']
    if not classes:
        raise ValueError('Cannot assert undamaged/compatible C0 from an unannotated image')
    words = [DAMAGE_TERMS[key] for key in classes]
    damage = words[0] if len(words) == 1 else ', '.join(words[:-1]) + ' y ' + words[-1]
    index = stable_index(source['source_image_id'], seed, 'template', len(POSITIVE))
    target = classes[stable_index(source['source_image_id'], seed, 'contradiction', len(classes))]
    return POSITIVE[index].format(damage=damage), f'objective-{index}', target


def claim_id(source: dict, condition: str, config: dict) -> str:
    identity = {'generator_version': config['generator_version'], 'source_image_id': source['source_image_id'],
                'source_sha256': source['file_sha256'], 'condition': condition, 'config': config}
    return 'clm_' + sha(canonical(identity))[:24]


def visual_variant(root: Path, source: dict, condition: str, identifier: str, config: dict):
    with Image.open(root/source['image_path']) as image:
        original = image.convert('RGB')
        buffer = io.BytesIO()
        if condition == 'C8':
            original.save(buffer, format='JPEG', quality=config['jpeg_quality'], subsampling=0,
                          optimize=False, progressive=False)
            content = buffer.getvalue()
            with Image.open(io.BytesIO(content)) as decoded:
                delta = np.asarray(original, dtype=np.float64) - np.asarray(decoded.convert('RGB'), dtype=np.float64)
            mse = float(np.mean(delta**2))
            # Finite sentinel for identical images; documented as a lower bound.
            psnr = 100.0 if mse == 0 else 10 * math.log10(255**2/mse)
            parameters = {'quality': config['jpeg_quality'], 'subsampling': 0,
                          'resize': False, 'crop': False, 'psnr_db': round(psnr, 8),
                          'minimum_psnr_db': config['jpeg_min_psnr_db']}
            if psnr < config['jpeg_min_psnr_db']:
                return None, parameters
            suffix, operation = '.jpg', 'jpeg_recompression'
        else:
            radius = config['blur_radius_fraction'] * min(original.size)
            blurred = original.filter(ImageFilter.GaussianBlur(radius=radius))
            blurred.save(buffer, format='PNG', compress_level=9)
            content = buffer.getvalue()
            gray = cv2.cvtColor(np.asarray(blurred), cv2.COLOR_RGB2GRAY)
            variance = float(cv2.Laplacian(gray, cv2.CV_64F).var())
            parameters = {'radius_fraction': config['blur_radius_fraction'], 'radius_pixels': radius,
                          'laplacian_variance': round(variance, 8),
                          'maximum_laplacian_variance': config['blur_max_laplacian_variance']}
            if variance > config['blur_max_laplacian_variance']:
                return None, parameters
            suffix, operation = '.png', 'gaussian_blur'
    relative = f'data/processed/benchmark_v1/{identifier}{suffix}'
    write_verified(root/relative, content)
    return {'image_path': relative, 'operation': operation, 'image_sha256': sha(content)}, parameters


def generate_claims(root: Path, audit: dict, splits: dict, config: dict, registry: dict):
    if set(config['conditions']) - ACTIVE or 'C0' not in config['conditions']:
        raise ValueError('Requested condition is not implemented, or C0 is missing')
    claims, exclusions = [], []
    for source in audit['sources']:
        source_id = source['source_image_id']
        base_narrative, template, denied_class = narrative(source, config['seed'])
        provenance = ClaimProvenance(dataset=audit['dataset'], dataset_version=audit['dataset_version'],
            source_group_id=splits['sources'][source_id]['group_id'], source_image_path=source['image_path'],
            source_image_sha256=source['file_sha256'], annotation_sha256=source['annotation_sha256'],
            generator_version=config['generator_version'], seed=config['seed'], narrative_template_id=template)
        parent = claim_id(source, 'C0', config)
        for condition in config['conditions']:
            identifier = claim_id(source, condition, config)
            image_path, text = source['image_path'], base_narrative
            operation, parameters, image_sha = 'identity', {}, source['file_sha256']
            if condition == 'C1':
                index = int(template.rsplit('-', 1)[1])
                text = NEGATIVE[index].format(damage=DAMAGE_TERMS[denied_class])
                operation, parameters = 'narrative_contradiction', {'denied_annotated_class': denied_class}
            elif condition == 'C6':
                text, operation = None, 'remove_narrative'
            elif condition == 'C7':
                image_path, image_sha, operation = None, None, 'remove_image'
            elif condition in ('C8', 'C9'):
                variant, parameters = visual_variant(root, source, condition, identifier, config)
                if variant is None:
                    exclusions.append({'source_image_id': source_id, 'condition': condition,
                                       'reason': 'Prespecified quality gate failed; no label/claim emitted', 'parameters': parameters})
                    continue
                image_path, operation, image_sha = variant['image_path'], variant['operation'], variant['image_sha256']
            claims.append(ClaimRecord(schema_version="0.2.0", claim_id=identifier, source_image_id=source_id,
                image_path=image_path, narrative_text=text, expected_label=registry[condition]['expected_label'],
                condition=condition, split=splits['sources'][source_id]['split'],
                annotation_reference=source['annotation_reference'], annotated_damage_classes=source['damage_classes'],
                parent_claim_id=None if condition == 'C0' else parent, provenance=provenance,
                transformation=ClaimTransformation(operation=operation, parameters=parameters, seed=config['seed'], image_sha256=image_sha)))
    return claims, exclusions


def validate_claims(claims: list[ClaimRecord], audit: dict, splits: dict, config: dict, registry: dict) -> dict:
    def require(ok, message):
        if not ok:
            raise ValueError(message)
    require(bool(claims), 'Empty claim manifest')
    by_id = {claim.claim_id: claim for claim in claims}
    require(len(by_id) == len(claims), 'Duplicate claim IDs')
    sources = {source['source_image_id']: source for source in audit['sources']}
    require(audit['duplicates'] == group_sources(audit['sources'], config['near_duplicate_hamming_threshold']), 'Duplicate grouping differs from recorded fingerprints')
    require(splits == frozen_splits(audit, config), 'Frozen split artifact disagrees with grouped source allocation')
    image_splits = defaultdict(set)
    source_splits = defaultdict(set)
    parent_splits = defaultdict(set)
    group_splits = defaultdict(set)
    for claim in claims:
        require(claim.source_image_id in sources, 'Unknown source_image_id')
        source = sources[claim.source_image_id]
        condition = claim.condition
        require(condition in config['conditions'] and condition in ACTIVE, 'Condition not implemented/enabled')
        require(claim.claim_id == claim_id(source, condition, config), 'Unstable/tampered claim ID')
        require(claim.expected_label.value == registry[condition]['expected_label'], 'Condition label mismatch')
        require(claim.split.value == splits['sources'][claim.source_image_id]['split'], 'Source split leakage')
        require(claim.provenance.source_group_id == splits['sources'][claim.source_image_id]['group_id'], 'Group provenance mismatch')
        require(claim.annotation_reference == source['annotation_reference'], 'Annotation reference mismatch')
        require(claim.annotated_damage_classes == source['damage_classes'], 'Ground-truth damage classes mismatch')
        require(claim.provenance.source_image_sha256 == source['file_sha256'], 'Source SHA mismatch')
        require(claim.provenance.source_image_path == source['image_path'], 'Source path mismatch')
        require(claim.provenance.annotation_sha256 == source['annotation_sha256'], 'Annotation SHA mismatch')
        require(claim.provenance.seed == config['seed'] == claim.transformation.seed, 'Seed mismatch')
        require(claim.provenance.dataset == audit['dataset'] and claim.provenance.dataset_version == audit['dataset_version'], 'Dataset provenance mismatch')
        require(claim.provenance.generator_version == config['generator_version'], 'Generator version mismatch')
        base_text, template, denied = narrative(source, config['seed'])
        require(claim.provenance.narrative_template_id == template, 'Template provenance mismatch')
        parent = by_id.get(claim_id(source, 'C0', config))
        require(parent is not None, 'Missing C0 parent')
        if condition != 'C0':
            require(claim.parent_claim_id == parent.claim_id and claim.split == parent.split, 'Variant parent leakage/mismatch')
        expected_text = None if condition == 'C6' else base_text
        if condition == 'C1':
            expected_text = NEGATIVE[int(template.rsplit('-', 1)[1])].format(damage=DAMAGE_TERMS[denied])
            require(claim.transformation.parameters == {'denied_annotated_class': denied}, 'C1 must deny an annotated damage')
        require(claim.narrative_text == expected_text, 'Narrative semantic invariant failed')
        expected_operations = {'C0':'identity','C1':'narrative_contradiction','C6':'remove_narrative',
                               'C7':'remove_image','C8':'jpeg_recompression','C9':'gaussian_blur'}
        require(claim.transformation.operation == expected_operations[condition], 'Wrong transformation')
        require(not claim.transformation.donor_source_image_ids, 'Donor conditions are not implemented in v1')
        if condition in ('C0','C1','C6'):
            require(claim.image_path == source['image_path'] and claim.transformation.image_sha256 == source['file_sha256'], 'Original image invariant failed')
        if condition in ('C0','C6','C7'):
            require(claim.transformation.parameters == {}, 'Unexpected transformation parameters')
        if condition == 'C7':
            require(claim.image_path is None and claim.transformation.image_sha256 is None, 'C7 must have missing image')
        if condition in ('C8','C9'):
            suffix = '.jpg' if condition == 'C8' else '.png'
            require(claim.image_path == f'data/processed/benchmark_v1/{claim.claim_id}{suffix}', 'Derived image path mismatch')
            require(bool(claim.transformation.image_sha256), 'Missing derived image SHA')
            params = claim.transformation.parameters
            if condition == 'C8':
                require(params.get('quality') == config['jpeg_quality'] and params.get('minimum_psnr_db') == config['jpeg_min_psnr_db']
                        and params.get('psnr_db', -1) >= config['jpeg_min_psnr_db'] and params.get('resize') is False
                        and params.get('crop') is False and params.get('subsampling') == 0, 'C8 benign quality gate failed')
            else:
                require(params.get('radius_fraction') == config['blur_radius_fraction']
                        and params.get('radius_pixels') == config['blur_radius_fraction']*min(source['width'], source['height'])
                        and params.get('maximum_laplacian_variance') == config['blur_max_laplacian_variance']
                        and 0 <= params.get('laplacian_variance', -1) <= config['blur_max_laplacian_variance'], 'C9 insufficient-quality gate failed')
        source_splits[claim.source_image_id].add(claim.split.value)
        parent_splits[parent.claim_id].add(claim.split.value)
        group_splits[claim.provenance.source_group_id].add(claim.split.value)
        if claim.transformation.image_sha256:
            image_splits[claim.transformation.image_sha256].add(claim.split.value)
    for name, mapping in [('source',source_splits),('parent claim',parent_splits),('group',group_splits),('image SHA',image_splits)]:
        require(all(len(values) == 1 for values in mapping.values()), f'{name} cross-split leakage')
    require(set(source_splits) == set(sources), 'Source omitted from benchmark')
    mandatory = set(config['conditions']) & {'C0','C1','C6','C7'}
    for source in sources.values():
        require(all(claim_id(source, condition, config) in by_id for condition in mandatory), 'Mandatory source condition missing')
    for pair in audit['duplicates']['pairs']:
        require(splits['sources'][pair['source_a']]['split'] == splits['sources'][pair['source_b']]['split'], 'Duplicate/near-duplicate cross-split leakage')
    return {'result':'PASS', 'claims':len(claims), 'conditions':dict(sorted(Counter(claim.condition for claim in claims).items())),
            'claims_per_split':dict(sorted(Counter(claim.split.value for claim in claims).items())),
            'sources_per_split':{split.value:sum(split.value in values for values in source_splits.values()) for split in Split},
            'groups_per_split':{split.value:sum(split.value in values for values in group_splits.values()) for split in Split},
            'overlap':{'train/validation':[], 'train/test':[], 'validation/test':[]},
            'parent_claim_leakage':False, 'exact_image_cross_split_leakage':False,
            'near_duplicate_cross_split_leakage':False}


def build_benchmark(root: Path, config_path: Path, output: Path) -> dict:
    config = yaml.safe_load(config_path.read_text())
    registry = yaml.safe_load((root/config['conditions_config']).read_text())['conditions']
    audit = audit_dataset(root, config['dataset_dir'], config['near_duplicate_hamming_threshold'])
    splits = frozen_splits(audit, config)  # Before producing ANY derived claim/image.
    claims, exclusions = generate_claims(root, audit, splits, config, registry)
    validation = validate_claims(claims, audit, splits, config, registry)
    packets = [EvidencePacket(schema_version="0.2.0", claim=claim) for claim in claims]
    artifacts = {'manifest.jsonl':b''.join(canonical(claim.model_dump(mode='json')) for claim in claims),
                 'evidence_packets.jsonl':b''.join(canonical(packet.model_dump(mode='json')) for packet in packets),
                 'splits.json':canonical(splits), 'dataset_audit.json':canonical(audit),
                 'validation.json':canonical(validation), 'exclusions.json':canonical(exclusions)}
    metadata = {'benchmark_version':config['benchmark_version'], 'generator_version':config['generator_version'],
                'schema_version':'0.2.0', 'config_sha256':sha(config_path.read_bytes()),
                'conditions_sha256':sha((root/config['conditions_config']).read_bytes()),
                'acquisition_receipt_sha256':sha((root/config['acquisition_receipt']).read_bytes()),
                'artifacts_sha256':{name:sha(content) for name, content in artifacts.items()},
                'runtime':{'Pillow':pillow_version,'numpy':np.__version__,'opencv':cv2.__version__},
                'scope':'Real vehicle-damage imagery + controlled/synthetic claim scenarios; small benchmark v1, not insurer records'}
    artifacts['metadata.json'] = canonical(metadata)
    for name, content in artifacts.items():
        write_verified(output/name, content)
    return {**validation, 'manifest_sha256':sha(artifacts['manifest.jsonl']), 'exclusions':exclusions}


def validate_bundle(root: Path, output: Path, config_path: Path, verify_images: bool = False) -> dict:
    metadata = json.loads((output/'metadata.json').read_text())
    for name, expected in metadata['artifacts_sha256'].items():
        if sha((output/name).read_bytes()) != expected:
            raise ValueError(f'Artifact hash mismatch: {name}')
    config = yaml.safe_load(config_path.read_text())
    if sha(config_path.read_bytes()) != metadata['config_sha256']:
        raise ValueError('Configuration changed after freeze')
    registry_path = root/config['conditions_config']
    if sha(registry_path.read_bytes()) != metadata['conditions_sha256']:
        raise ValueError('Condition registry changed after freeze')
    if sha((root/config['acquisition_receipt']).read_bytes()) != metadata['acquisition_receipt_sha256']:
        raise ValueError('Acquisition receipt changed after freeze')
    registry = yaml.safe_load(registry_path.read_text())['conditions']
    claims = [ClaimRecord.model_validate_json(line) for line in (output/'manifest.jsonl').read_text().splitlines()]
    packets = [EvidencePacket.model_validate_json(line) for line in (output/'evidence_packets.jsonl').read_text().splitlines()]
    audit = json.loads((output/'dataset_audit.json').read_text())
    splits = json.loads((output/'splits.json').read_text())
    report = validate_claims(claims, audit, splits, config, registry)
    if len(packets) != len(claims):
        raise ValueError('Packet/claim cardinality mismatch')
    for claim, packet in zip(claims, packets):
        if packet.claim != claim or any(getattr(packet, name) is not None for name in ('narrative','visual','image_quality','forensic')):
            raise ValueError('Packet must preserve claim and unavailable specialist outputs')
    if verify_images:
        observed = audit_dataset(root, config['dataset_dir'], config['near_duplicate_hamming_threshold'])
        if observed != audit:
            raise ValueError('Actual dataset/duplicate audit differs from frozen source audit')
        regenerated, exclusions = generate_claims(root, observed, splits, config, registry)
        if regenerated != claims or exclusions != json.loads((output/'exclusions.json').read_text()):
            raise ValueError('Regeneration differs from frozen manifest')
        for claim in claims:
            if claim.image_path and sha((root/claim.image_path).read_bytes()) != claim.transformation.image_sha256:
                raise ValueError(f'Actual image content mismatch: {claim.claim_id}')
    return report
