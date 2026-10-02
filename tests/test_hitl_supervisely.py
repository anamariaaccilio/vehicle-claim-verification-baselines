import json
from pathlib import Path

import pytest
from PIL import Image

from src.data.hitl_supervisely import parse_hitl_supervisely
from src.schemas.evidence import HITL_TO_CANONICAL


@pytest.fixture
def dataset(tmp_path):
    (tmp_path/'meta.json').write_text(json.dumps({'classes':[{'title':c} for c in HITL_TO_CANONICAL]}))
    (tmp_path/'File1/ann').mkdir(parents=True)
    (tmp_path/'File1/img').mkdir()
    Image.new('RGB', (20, 10)).save(tmp_path/'File1/img/car.png')
    doc = {'size':{'width':20,'height':10},'objects':[{'classTitle':'Dent','geometryType':'polygon','points':{'exterior':[[1,1],[10,1],[10,8]],'interior':[]}}]}
    (tmp_path/'File1/ann/car.png.json').write_text(json.dumps(doc))
    return tmp_path


def mutate(dataset, callback):
    path=dataset/'File1/ann/car.png.json'
    doc=json.loads(path.read_text()); callback(doc); path.write_text(json.dumps(doc))


def test_reads_real_format_without_inventing_confidence(dataset):
    record, = parse_hitl_supervisely(dataset, relative_to=dataset)
    assert record.source_image_id == 'hitl:car'
    assert record.path == 'File1/img/car.png'
    assert record.damage_classes == ['dent']
    assert record.annotations[0].confidence is None
    assert record.annotations[0].bbox.x_max == 10
    assert record.annotations[0].polygon.points == [(1.,1.), (10.,1.), (10.,8.)]


@pytest.mark.parametrize('problem',['size','class','holes','bitmap','bounds','degenerate','nonfinite'])
def test_rejects_incompatible_geometry_or_labels(dataset,problem):
    def change(doc):
        obj=doc['objects'][0]
        if problem=='size': doc['size']['width']=21
        if problem=='class': obj['classTitle']='Hood'
        if problem=='holes': obj['points']['interior']=[[[2,2],[3,2],[3,3]]]
        if problem=='bitmap': obj['geometryType']='bitmap'
        if problem=='bounds': obj['points']['exterior'][0]=[-1,0]
        if problem=='degenerate': obj['points']['exterior']=[[1,1],[2,2],[3,3]]
        if problem=='nonfinite': obj['points']['exterior'][0]=[float('nan'),0]
    mutate(dataset,change)
    with pytest.raises(ValueError): parse_hitl_supervisely(dataset)


def test_rejects_parts_taxonomy(dataset):
    (dataset/'meta.json').write_text(json.dumps({'classes':[{'title':'Hood'}]}))
    with pytest.raises(ValueError,match='taxonomy'): parse_hitl_supervisely(dataset)


def test_rejects_missing_image(dataset):
    (dataset/'File1/img/car.png').rename(dataset/'File1/img/other.png')
    with pytest.raises(FileNotFoundError): parse_hitl_supervisely(dataset)


def test_does_not_merge_different_images_under_same_source(dataset):
    other=dataset/'File2/ann';other.mkdir(parents=True)
    (other/'car.png.json').write_bytes((dataset/'File1/ann/car.png.json').read_bytes())
    with pytest.raises(ValueError,match='Ambiguous'): parse_hitl_supervisely(dataset)


def test_rejects_empty_dataset(dataset):
    (dataset/'File1/ann/car.png.json').rename(dataset/'File1/ann/car.png.backup')
    with pytest.raises(ValueError,match='No annotation'): parse_hitl_supervisely(dataset)
