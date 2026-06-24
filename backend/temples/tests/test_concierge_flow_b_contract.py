# temples/tests/test_concierge_flow_b_contract.py


def test_mode_meta_compat_without_birthdate_uses_condition_label():
    from temples.services.concierge_chat_ranking import _resolve_mode_meta

    mode = _resolve_mode_meta(
        public_mode="compat",
        flow="B",
        weights={"element": 0.8, "need": 0.2, "popular": 0.0},
        astro_bonus_enabled=True,
        birthdate=None,
    )

    assert mode["mode"] == "compat"
    assert mode["flow"] == "B"
    assert mode["ui_label_ja"] == "条件重視"
    assert mode["ui_note_ja"] == "追加条件との一致を中心に並べ替えています"


def test_mode_meta_compat_with_birthdate_uses_compat_label():
    from temples.services.concierge_chat_ranking import _resolve_mode_meta

    mode = _resolve_mode_meta(
        public_mode="compat",
        flow="B",
        weights={"element": 0.8, "need": 0.2, "popular": 0.0},
        astro_bonus_enabled=True,
        birthdate="2000-03-21",
    )

    assert mode["mode"] == "compat"
    assert mode["flow"] == "B"
    assert mode["weights"] == {"element": 0.8, "need": 0.2, "popular": 0.0}
    assert mode["ui_label_ja"] == "相性重視"
    assert mode["ui_note_ja"] == "生年月日との相性を中心に並べ替えています"
