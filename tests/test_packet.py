import pytest
import yaml
from pydantic import ValidationError
from src.schemas.claim import Claim, ClaimRecord
from src.schemas.packet import EvidencePacket, SCHEMA_VERSION
from src.schemas.evidence import DecisionLabel, LABELS_CONFIG_PATH


def test_claim_record_preserves_existing_class_identity():
    assert ClaimRecord is Claim


def test_packet_roundtrip_missing_evidence():
    packet = EvidencePacket(claim=ClaimRecord(claim_id="fixture"))
    assert EvidencePacket.model_validate_json(packet.model_dump_json()) == packet
    assert packet.schema_version == SCHEMA_VERSION
    assert packet.visual is None


def test_packet_rejects_unknown_contract_version():
    with pytest.raises(ValidationError):
        EvidencePacket(claim=ClaimRecord(claim_id="fixture"), schema_version="unknown")


def test_decision_labels_match_canonical_configuration():
    config = yaml.safe_load(LABELS_CONFIG_PATH.read_text())
    assert set(config["decision_classes"]) == {label.value for label in DecisionLabel}
