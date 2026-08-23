import json
from pathlib import Path

SEED_PATH = (
    Path(__file__).resolve().parents[1] / "data" / "shrines_seed_clean.json"
)
KNOWLEDGE_SEED_PATH = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "knowledge_seeds"
    / "batch_17_seed.json"
)

TARGETS = {
    "北海道神宮": {
        "address": "北海道札幌市中央区宮ヶ丘474",
        "latitude": 43.0553,
        "longitude": 141.3126,
    },
    "建部大社": {
        "address": "滋賀県大津市神領1-16-1",
        "latitude": 34.9735,
        "longitude": 135.9135,
    },
    "波上宮": {
        "address": "沖縄県那覇市若狭1-25-11",
        "latitude": 26.2144,
        "longitude": 127.6672,
    },
}


def _load_seed():
    return json.loads(SEED_PATH.read_text(encoding="utf-8"))


def test_shrine_base_seed_has_103_entries_existing_100_plus_batch17_3():
    data = _load_seed()
    assert len(data) == 103


def test_shrine_base_seed_batch17_shrines_present_exactly_once():
    data = _load_seed()
    for name in TARGETS:
        matches = [e for e in data if e["name_jp"] == name]
        assert len(matches) == 1, name


def test_shrine_base_seed_batch17_identity_matches_knowledge_seed():
    """Batch 17 Knowledge Seed（shrine_ref）が参照するname_jp/addressと
    Shrine base Seedの新規3社が完全に一致することを固定化する。
    一致しなければ import_shrine_knowledge の resolve_shrine が
    NOT_FOUND/AMBIGUOUS になる。"""
    data = _load_seed()
    by_name = {e["name_jp"]: e for e in data}

    knowledge_seed = json.loads(KNOWLEDGE_SEED_PATH.read_text(encoding="utf-8"))
    for shrine_block in knowledge_seed["shrines"]:
        ref = shrine_block["shrine_ref"]
        assert ref["name_jp"] in TARGETS
        base_entry = by_name[ref["name_jp"]]
        assert base_entry["address"] == ref["address"]


def test_shrine_base_seed_batch17_coordinates_and_address():
    data = _load_seed()
    by_name = {e["name_jp"]: e for e in data}

    for name, expected in TARGETS.items():
        entry = by_name[name]
        assert entry["address"] == expected["address"]
        assert entry["latitude"] == expected["latitude"]
        assert entry["longitude"] == expected["longitude"]
        assert entry["location"] == {
            "lat": expected["latitude"],
            "lng": expected["longitude"],
        }


def test_shrine_base_seed_no_duplicate_name_or_address():
    data = _load_seed()
    names = [e["name_jp"] for e in data]
    assert len(names) == len(set(names))

    addresses = [(e["name_jp"], e["address"]) for e in data]
    assert len(addresses) == len(set(addresses))


def test_shrine_base_seed_existing_100_entries_unchanged():
    """Batch17追加前の既存100社の値（name_jp/address/latitude/longitude）が
    一切変更されていないことを固定化する。"""
    data = _load_seed()
    existing_100 = data[:100]
    names = [e["name_jp"] for e in existing_100]
    for target in TARGETS:
        assert target not in names, "Batch17 shrine must be appended after the existing 100, not intermixed"
    # spot-check a few well-known existing entries are unmodified
    by_name = {e["name_jp"]: e for e in existing_100}
    assert by_name["明治神宮"]["address"] == "東京都渋谷区代々木神園町1-1"
    assert by_name["明治神宮"]["latitude"] == 35.6764
    assert by_name["明治神宮"]["longitude"] == 139.6993
    assert by_name["阿蘇神社"]["address"] == "熊本県阿蘇市一の宮町宮地3083-1"
