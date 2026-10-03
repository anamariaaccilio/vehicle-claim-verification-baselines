"""Scientific QA guards: descriptive inference, no mislabeled human review."""
import copy
from html.parser import HTMLParser
import json
from pathlib import Path

import numpy as np
from PIL import Image
import pytest

from src.data.benchmark_qa import c2_audit,narrative_audit,gallery
from src.data.benchmark_v3 import benign_control,paired_narrative,audit_full,check,validate
from src.schemas.evidence import HITL_TO_CANONICAL

ROOT=Path(__file__).resolve().parents[1]


def test_c2_heuristic_is_not_a_label_change():
    source={'source_image_id':'s','damage_classes':['dent'],'dhash128':'0'*32}
    claims=[{'condition':'C2','claim_id':'c','source_image_id':'s','expected_label':'SUSPICIOUS',
             'transformation':{'donor_source_image_ids':['d']}}]
    for classes,expected in [(['dent'],'likely compatible'),(['scratch'],'likely contradiction'),(['dent','scratch'],'likely compatible')]:
        donor={'source_image_id':'d','damage_classes':classes,'dhash128':'f'*32}
        before=copy.deepcopy(claims)
        row=c2_audit(claims,{'s':source,'d':donor})[0]
        assert row['classification']==expected and row['label_unchanged']=='SUSPICIOUS'
        assert 'UNKNOWN' in row['damage_location_compatibility']
        assert claims==before


def test_narrative_statistics_and_associations_use_document_frequency():
    rows=[{'claim_id':str(i),'condition':'C0' if i<3 else 'C1',
           'expected_label':'SUPPORTED' if i<3 else 'SUSPICIOUS',
           'narrative_text':'Daño daño.' if i<3 else 'Sin daño.',
           'provenance':{'narrative_template_id':'fixture'}} for i in range(6)]
    result=narrative_audit(rows)
    assert result['unique_nonempty']==2 and result['duplicate_percent_nonempty']==pytest.approx(100*4/6)
    token=next(r for r in result['associations']['expected_label'] if r['term']=='sin')
    assert token['documents']==3 and token['exclusive'] and token['target']=='SUSPICIOUS'
    assert result['by_condition']['C0']['std_tokens_population']==0


def test_paired_narratives_share_target_and_negation_occurs_on_both_sides():
    supported=[];contradicted=[]
    for i in range(100):
        source={'source_image_id':f's{i}','damage_classes':['dent','scratch']}
        positive,template,target=paired_narrative(source,42)
        negative,template2,target2=paired_narrative(source,42,True)
        assert target==target2 and template==template2 and positive!=negative
        assert paired_narrative(source,42)==paired_narrative(source,42)
        supported.append(positive);contradicted.append(negative)
    assert any(' no ' in x.lower() for x in supported)
    assert any(' no ' in x.lower() for x in contradicted)
    assert any(' no ' not in x.lower() for x in supported)
    assert any(' no ' not in x.lower() for x in contradicted)


@pytest.fixture
def annotated_pixels(tmp_path):
    image=np.random.default_rng(42).integers(0,256,(80,100,3),dtype=np.uint8)
    Image.fromarray(image).save(tmp_path/'source.png')
    (tmp_path/'ann.json').write_text(json.dumps({'objects':[{'points':{'exterior':[[20,20],[70,20],[70,60],[20,60]]}}]}))
    source={'source_image_id':'fixture','image_path':'source.png','annotation_reference':'ann.json','width':100,'height':80}
    return tmp_path,source,image


def test_resize_and_crop_reproducible_and_preserve_evidence(annotated_pixels):
    import io
    root,source,image=annotated_pixels
    config={'resize_scale':1.25,'crop_margin_fraction':.05}
    for subtype in ('C8_RESIZE','C8_CROP'):
        content,params=benign_control(root,source,subtype,config)
        assert (content,params)==benign_control(root,source,subtype,config)
        assert params['all_damage_regions_retained'] is True
        with Image.open(io.BytesIO(content)) as transformed:
            if subtype=='C8_RESIZE': assert transformed.size==(125,100)
            else:
                x,y,right,bottom=params['crop_box']
                assert x<=20 and y<=20 and right>70 and bottom>60
                assert np.array_equal(np.asarray(transformed),image[y:bottom,x:right])


def test_crop_refuses_to_remove_boundary_damage(annotated_pixels):
    root,source,_=annotated_pixels
    (root/'ann.json').write_text(json.dumps({'objects':[{'points':{'exterior':[[0,0],[99,0],[99,79],[0,79]]}}]}))
    content,params=benign_control(root,source,'C8_CROP',{'crop_margin_fraction':.05})
    assert content is None and 'No safe background' in params['reason']


def test_full_ingestion_quarantines_bad_annotation_without_changing_raw(tmp_path):
    dataset=tmp_path/'raw/dataset';(dataset/'File1/img').mkdir(parents=True);(dataset/'File1/ann').mkdir()
    (dataset/'meta.json').write_text(json.dumps({'classes':[{'title':k} for k in HITL_TO_CANONICAL]}))
    ann={'size':{'width':20,'height':20},'objects':[{'classTitle':'Dent','geometryType':'polygon','points':{'exterior':[[1,1],[10,1],[10,10]],'interior':[]}}]}
    for name in ('good','bad'):
        Image.fromarray(np.full((20,20,3),100,dtype=np.uint8)).save(dataset/f'File1/img/{name}.png')
        payload=copy.deepcopy(ann)
        if name=='bad':payload['objects'][0]['points']['exterior'][0]=[-1,0]
        (dataset/f'File1/ann/{name}.png.json').write_text(json.dumps(payload))
    before={str(p):p.read_bytes() for p in dataset.rglob('*') if p.is_file()}
    audit=audit_full(tmp_path,{'dataset_dir':'raw/dataset','near_duplicate_hamming_threshold':6})
    assert audit['images_available']==2 and audit['images']==1 and len(audit['excluded_sources'])==1
    assert before=={str(p):p.read_bytes() for p in dataset.rglob('*') if p.is_file()}


def test_gallery_escapes_text_and_contains_required_comparisons(annotated_pixels):
    root,source,_=annotated_pixels
    claim={'claim_id':'fixture','source_image_id':'fixture','condition':'C0','expected_label':'SUPPORTED',
           'narrative_text':'<script>alert(1)</script>','image_path':'source.png',
           'transformation':{'parameters':{},'seed':42,'donor_source_image_ids':[]}}
    output=root/'qa.html';gallery(root,[claim],{'fixture':source},output)
    text=output.read_text();assert '&lt;script&gt;' in text and '<script>alert(1)</script>' not in text
    assert 'Original' in text and 'Imagen presentada' in text and 'Exportar revisión JSON' in text
    assert 'PENDIENTE' in text and 'seed' in text


def test_frozen_v3_schema_and_semantic_tampering():
    import yaml
    from src.schemas.claim import ClaimRecord
    output=ROOT/'data/manifests/benchmark_v3';config_path=ROOT/'configs/benchmark_v3.yaml'
    assert output.is_dir(), 'The frozen v3 artifact is required, including in CI'
    report=check(ROOT,config_path,output)
    assert report['result']=='PASS'
    assert set(report['c8_subtypes'])=={'C8_JPEG','C8_RESIZE','C8_CROP'}
    claims=[ClaimRecord.model_validate_json(line) for line in (output/'manifest.jsonl').read_text().splitlines()]
    config=yaml.safe_load(config_path.read_text());registry=yaml.safe_load((ROOT/config['conditions_config']).read_text())['conditions']
    audit=json.loads((output/'dataset_audit.json').read_text());splits=json.loads((output/'splits.json').read_text());exclusions=json.loads((output/'exclusions.json').read_text())
    target=next(c for c in claims if c.condition=='C8' and c.transformation.parameters['subtype']=='C8_CROP')
    target.transformation.parameters['all_damage_regions_retained']=False
    with pytest.raises(ValueError,match='cropped out'):validate(claims,audit,splits,config,registry,exclusions)
