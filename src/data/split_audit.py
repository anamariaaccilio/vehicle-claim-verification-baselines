"""Audit persisted JSONL rows without silently ignoring missing groups/splits."""
from itertools import combinations
from src.data.split import LeakageError, check_no_leakage
from src.schemas.claim import SourceImage, Split


def audit_rows(rows, group_key="source_image_id", split_key="split"):
    rows = list(rows)
    if not rows:
        raise ValueError("Manifest is empty")
    groups = {s.value: set() for s in Split}
    records = []
    for index, row in enumerate(rows, 1):
        group, split = row.get(group_key), row.get(split_key)
        if not isinstance(group, str) or not group.strip():
            raise ValueError(f"Row {index}: missing/invalid {group_key}")
        if not isinstance(split, str) or split not in groups:
            raise ValueError(f"Row {index}: missing/invalid {split_key}")
        groups[split].add(group)
        records.append(SourceImage(source_image_id=group, path="audit-only", split=split))
    overlap = {f"{a}/{b}": sorted(groups[a] & groups[b])
               for a, b in combinations(groups, 2)}
    try:
        check_no_leakage(records)
        passed = True
    except LeakageError:
        passed = False
    return {"group_key": group_key, "split_key": split_key, "rows": len(rows),
            "groups": {s: len(ids) for s, ids in groups.items()},
            "overlap": overlap, "result": "PASS" if passed else "FAIL"}
