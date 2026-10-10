"""nsrc-000002 G7 SQL の Source identity が importer と完全一致することの regression。

scripts/migration_safety/sql/nsrc_000002_g7_*.sql は同一の
`nsrc_000002_source_identity` block を持つ。その normalized_url は
knowledge_seed.normalize_source_url() と一致しなければならない
（accepted_source_count は importer の semantic identity だけで数える）。
"""

import re
from pathlib import Path

import pytest
from django.db import connection

from temples.models import ShrineKnowledgeSource
from temples.services.knowledge_seed import normalize_source_url

REPO_ROOT = Path(__file__).resolve().parents[3]
SQL_DIR = REPO_ROOT / "scripts" / "migration_safety" / "sql"
SQL_FILES = (
    "nsrc_000002_g7_preflight.sql",
    "nsrc_000002_g7_pre_base_guard.sql",
    "nsrc_000002_g7_post_base_guard.sql",
    "nsrc_000002_g7_post_knowledge_verification.sql",
)
BLOCK_RE = re.compile(
    r"-- BEGIN nsrc_000002_source_identity\n(.*?)-- END nsrc_000002_source_identity\n",
    re.DOTALL,
)

TARGET_NORMALIZED = "https://matsuri.geo-itoigawa.com/calendar/m04"
TARGET_TYPE = "government"

# importer と同じ semantic identity になる表記揺れ
IDENTITY_VARIANTS = (
    "https://matsuri.geo-itoigawa.com/calendar/m04/",
    "https://matsuri.geo-itoigawa.com/calendar/m04",
    "HTTPS://MATSURI.GEO-ITOIGAWA.COM/calendar/m04/",
    "https://matsuri.geo-itoigawa.com:443/calendar/m04/",
    "https://matsuri.geo-itoigawa.com:0443/calendar/m04",
    "https://matsuri.geo-itoigawa.com:/calendar/m04",
    "https://matsuri.geo-itoigawa.com/calendar/m04///",
    "https://matsuri.geo-itoigawa.com/calendar/m04/#top",
    "https://matsuri.geo-itoigawa.com/calendar/m04#a?b=1",
    "https://matsuri.geo-itoigawa.com/calendar/m04?",
    "https://user:pw@matsuri.geo-itoigawa.com/calendar/m04/",
    "  https://matsuri.geo-itoigawa.com/calendar/m04/  ",
    "\u3000https://matsuri.geo-itoigawa.com/calendar/m04/\u3000",
    "\x01https://matsuri.geo-itoigawa.com/calendar/m04/",
    "https://matsuri.geo-itoigawa.com/cal\tendar/m04/",
    "https://matsuri.geo-itoigawa.com/calendar/m04/\n",
)

# lookalike だが importer の identity ではない（再利用してはいけない）
# importer の identity ではないが、SQL の lookalike 診断には必ず拾われる表記
NON_IDENTITY_LOOKALIKE_VARIANTS = (
    "http://matsuri.geo-itoigawa.com/calendar/m04/",
    "https://matsuri.geo-itoigawa.com/Calendar/m04/",
    "https://matsuri.geo-itoigawa.com/calendar/M04/",
    "https://matsuri.geo-itoigawa.com/calendar/m04/?lang=ja",
    "https://matsuri.geo-itoigawa.com:8443/calendar/m04/",
    "https://matsuri.geo-itoigawa.com:80/calendar/m04/",
    "https://www.matsuri.geo-itoigawa.com/calendar/m04/",
    "https://matsuri.geo-itoigawa.com./calendar/m04/",
    "https://matsuri.geo-itoigawa.com/calendar/m04/index.html",
    "matsuri.geo-itoigawa.com/calendar/m04/",
    "//matsuri.geo-itoigawa.com/calendar/m04/",
    "https:/matsuri.geo-itoigawa.com/calendar/m04/",
)

# importer の identity でも lookalike でもない表記（別ページ / host なし）
NON_IDENTITY_OTHER_VARIANTS = (
    "https://matsuri.geo-itoigawa.com/calendar/m05/",
    "https:///calendar/m04",
)

# 正規化の一般挙動（target 以外）も importer と一致すること
GENERAL_CORPUS = (
    "",
    "   ",
    "/",
    "https://example.com",
    "https://example.com/",
    "https://Example.com:8080/a/B/?Q=1&q=2#frag",
    "http://example.com:80/x",
    "http://example.com:443/x",
    "https://example.com:80/x",
    "ftp://Example.com:21/a/",
    "mailto:someone@example.com",
    "Mailto:Someone@Example.com",
    "urn:isbn:0451450523",
    "host:80",
    "relative/path/",
    "/abs/path//",
    "?only=query",
    "#only-fragment",
    "https://example.com//",
    "https://example.com/a//b//",
    "https://u@h@example.com/p",
    "https://example.com?x=1",
    "https://example.com/p?x=1#y?z",
    "file:///tmp/x/",
    "https:example.com/p/",
    "git+ssh://Host.Example:22/repo/",
    "custom-scheme://Host/p/",
    "1abc://host/p",
    "a_b://host/p",
)

# importer が ValueError で停止する URL（SQL は NULL = identity にならない）
IMPORTER_UNPARSEABLE = (
    "https://matsuri.geo-itoigawa.com:abc/calendar/m04/",
    "https://matsuri.geo-itoigawa.com:99999/calendar/m04/",
    "https://matsuri.geo-itoigawa.com:-1/calendar/m04/",
    "https://[matsuri.geo-itoigawa.com]/calendar/m04/",
    "https://[::1/calendar/m04/",
)


def _blocks() -> dict[str, str]:
    blocks = {}
    for name in SQL_FILES:
        text = (SQL_DIR / name).read_text(encoding="utf-8")
        found = BLOCK_RE.findall(text)
        assert found, name
        assert len(set(found)) == 1, name
        blocks[name] = found[0]
    return blocks


def _python_normalized(url: str) -> str | None:
    try:
        return normalize_source_url(url)
    except ValueError:
        return None


def _sql_rows() -> dict[int, tuple[str | None, bool, bool, bool]]:
    block = next(iter(_blocks().values()))
    sql = (
        "WITH "
        + block
        + """
SELECT n.id, n.normalized_url,
       EXISTS (SELECT 1 FROM source_identity i WHERE i.id = n.id),
       EXISTS (SELECT 1 FROM source_metadata_compatible m WHERE m.id = n.id),
       EXISTS (SELECT 1 FROM source_url_lookalike l WHERE l.id = n.id)
FROM source_url_norm n
"""
    )
    with connection.cursor() as cursor:
        cursor.execute(sql)
        return {row[0]: tuple(row[1:]) for row in cursor.fetchall()}


def _create(urls, *, source_type=TARGET_TYPE, compatible=True) -> dict[int, str]:
    rows = [
        ShrineKnowledgeSource(
            source_type=source_type,
            title=f"t{index}",
            url=url,
            publisher="糸魚川市 / 糸魚川ジオパーク協議会" if compatible else "別の発行者",
            verification_status="source_confirmed",
            confidence="high",
            language="ja",
        )
        for index, url in enumerate(urls)
    ]
    created = ShrineKnowledgeSource.objects.bulk_create(rows)
    return {row.pk: row.url for row in created}


def test_identity_block_is_identical_in_every_g7_sql_file():
    blocks = _blocks()
    assert len(set(blocks.values())) == 1


@pytest.mark.django_db
def test_sql_normalized_url_equals_importer_normalize_source_url():
    urls = (
        *IDENTITY_VARIANTS,
        *NON_IDENTITY_LOOKALIKE_VARIANTS,
        *NON_IDENTITY_OTHER_VARIANTS,
        *GENERAL_CORPUS,
        *IMPORTER_UNPARSEABLE,
    )
    created = _create(urls)
    rows = _sql_rows()

    for pk, url in created.items():
        expected = _python_normalized(url)
        assert rows[pk][0] == expected, (url, rows[pk][0], expected)


@pytest.mark.django_db
def test_identity_count_uses_importer_semantics_only():
    identity = _create(IDENTITY_VARIANTS)
    lookalike_non_identity = _create(NON_IDENTITY_LOOKALIKE_VARIANTS)
    other_non_identity = _create(NON_IDENTITY_OTHER_VARIANTS)
    unparseable = _create(IMPORTER_UNPARSEABLE)
    other_type = _create(("https://matsuri.geo-itoigawa.com/calendar/m04/",), source_type="web")
    rows = _sql_rows()

    # rows[pk] = (normalized_url, is_identity, is_metadata_compatible, is_lookalike)
    for pk, url in identity.items():
        assert normalize_source_url(url) == TARGET_NORMALIZED, url
        assert rows[pk][1] is True, url
        # lookalike 診断は identity の superset
        assert rows[pk][3] is True, url
    for pk, url in lookalike_non_identity.items():
        assert normalize_source_url(url) != TARGET_NORMALIZED, url
        assert rows[pk][1] is False, url
        assert rows[pk][3] is True, url
    for pk, url in other_non_identity.items():
        assert normalize_source_url(url) != TARGET_NORMALIZED, url
        assert rows[pk][1] is False, url
        assert rows[pk][3] is False, url
    for pk, url in unparseable.items():
        assert _python_normalized(url) is None, url
        assert rows[pk][0] is None, url
        assert rows[pk][1] is False, url
    # 同じ URL でも source_type が違えば identity ではない（lookalike としてだけ拾う）
    for pk in other_type:
        assert rows[pk][1] is False
        assert rows[pk][3] is True


@pytest.mark.django_db
def test_metadata_compatibility_is_a_subset_of_identity():
    compatible = _create(("https://matsuri.geo-itoigawa.com/calendar/m04/",))
    drifted = _create(("https://matsuri.geo-itoigawa.com/calendar/m04",), compatible=False)
    rows = _sql_rows()

    for pk in compatible:
        assert rows[pk][1:3] == (True, True)
    for pk in drifted:
        assert rows[pk][1:3] == (True, False)
