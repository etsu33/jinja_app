# Fact Source Citation Contract

## 1. 目的

同じ Source 文書（例: 市町村が公開する郡誌 PDF）の **異なる位置** を、複数の Knowledge Fact
（`ShrineHistory` / `ShrineDeity`）が参照できるようにする。

これまで Fact 固有の頁は `ShrineKnowledgeSource.bibliography` に書くしかなかった。その場合、
同じ normalized URL の Source を別の頁で再宣言すると、`bibliography` が異なるため
`SOURCE_REUSE_CONFLICT` となり、Source の重複作成も既存 Source の書き換えもできない。

例:

- nsrc-000007 の Fact は郡誌 PDF の `中魚沼郡誌上 p.398` を参照する（既存 Source の `bibliography`）
- 後続の Fact は同じ normalized PDF の `中魚沼郡誌上 p.445` を参照する必要がある

本契約は Fact 単位の位置情報（locator）を Source から分離する。

## 2. 責務の分離

| 層 | 保持するもの | 変更 |
| --- | --- | --- |
| `ShrineKnowledgeSource` | document-level の出典（identity = `source_type` + normalized URL） | なし |
| `ShrineHistory.sources` / `ShrineDeity.sources` | Fact と Source の関連（M2M） | なし（through model に置き換えない） |
| `ShrineFactSourceCitation` | Fact ごとの Source 内位置 `locator_text` | 新規（additive provenance） |

- `SOURCE_REUSE_CONFLICT`（`_SOURCE_REUSE_FIELDS` の差分 = CONFLICT）は弱めない。
- citation 対応の新しい packet では、Fact 固有の頁を `bibliography` に書く必要はない。
  `bibliography` は document-level の書誌（例: `中魚沼郡誌上`）として扱う。
- 既存 Production の Source（例: nsrc-000007 の `bibliography` に頁を含むもの）は書き換えない。
  本 PR はデータ移行を含まない。

## 3. Model: `ShrineFactSourceCitation`

| field | 型 | 制約 |
| --- | --- | --- |
| `source` | FK → `ShrineKnowledgeSource`（CASCADE） | 必須 |
| `shrine_history` | FK → `ShrineHistory`（CASCADE, nullable） | `shrine_deity` と exactly one |
| `shrine_deity` | FK → `ShrineDeity`（CASCADE, nullable） | `shrine_history` と exactly one |
| `locator_text` | CharField(255) | 非空白 |
| `created_at` | DateTimeField | default now |

DB 制約:

- `chk_fact_source_citation_exactly_one_fact`: `shrine_history` / `shrine_deity` の exactly one
- `chk_fact_source_citation_locator_not_blank`: `locator_text ~ '\S'`
- `uq_fact_source_citation_history`: (`shrine_history`, `source`, `locator_text`)（history 側のみ）
- `uq_fact_source_citation_deity`: (`shrine_deity`, `source`, `locator_text`)（deity 側のみ）

application validation（`clean()`。`save()` は常に `full_clean()` する）:

- exactly one の Fact selector
- `source` は対象 Fact の `.sources` に **既に** 関連付いていること。citation は M2M の関連を
  作らない・置き換えない。
- 同じ Fact + Source に別の `locator_text` は許容する（同じ Fact が同じ文書の複数頁を参照できる）。

Migration: `temples/migrations/0121_shrine_fact_source_citation.py` /
`temples/migrations_nogis/0020_shrine_fact_source_citation.py`。単一の `CreateModel` のみで、
RunPython / RunSQL / 既存 table の変更を含まない。両系統は dependency 行以外同一。

## 4. Runtime への影響

なし。Evidence Gate（`decide_fact_usability`）、Shared Recommendation Eligibility、Recommendation
ranking、Position、G5 / G6 の各経路は `ShrineFactSourceCitation` を参照しない。Fact の usability は
従来どおり Fact の `verification_status` と M2M で関連する Source の `verification_status` だけで決まる。
`EvidenceLink` は流用しない。

## 5. Knowledge Seed schema 1.3

1.3 は 1.2 の上位互換。1.2 で許可されるもの（`collectives` / `source_facts`、shrine block の
未知 key 拒否）はすべて 1.3 でも同じ。追加は `histories[]` / `deities[]` 要素の optional な
`citations` のみ。

```json
{
  "schema_version": "1.3",
  "sources": [
    {
      "key": "src-gunshi",
      "source_type": "local_history",
      "title": "中魚沼郡誌",
      "url": "https://example.jp/gunshi.pdf",
      "bibliography": "中魚沼郡誌上",
      "verification_status": "source_confirmed",
      "verified_at": "2026-10-01T00:00:00+09:00"
    }
  ],
  "shrines": [
    {
      "shrine_ref": {"name_jp": "…", "address": "…"},
      "histories": [
        {
          "history_type": "regional_context",
          "title": "…",
          "content": "…",
          "verification_status": "source_confirmed",
          "verified_at": "2026-10-01T00:00:00+09:00",
          "source_keys": ["src-gunshi"],
          "citations": [{"source_key": "src-gunshi", "locator_text": "中魚沼郡誌上 p.445"}]
        }
      ]
    }
  ]
}
```

parser 規則（すべて fail closed）:

- `citations` は schema 1.3 でのみ許可。1.0 / 1.1 / 1.2 では空リストでもエラー。
- `citations` は list、各要素は object。未知 key（例: `page`）はエラー。
- `source_key` は必須の非空文字列で、同じ Fact の `source_keys` に含まれていること。
- `locator_text` は必須・非空白・前後の空白なし。trim / 正規化はしない。
- 同じ Fact 内で (`source_key`, `locator_text`) の重複はエラー。
- `citations` を持たない既存 seed（1.0 / 1.1 / 1.2）は変更なしで parse / import できる。

## 6. Importer（`import_shrine_knowledge`）

処理順:

1. Source を既存規則で resolve / reuse / create する（`resolve_source_identity`。変更なし）
2. Fact を create / reuse する（変更なし）
3. Fact の `.sources` を保つ（既存 Fact の `.sources` は従来どおり変更しない）
4. citation を冪等に materialize する
5. citation の衝突・不正な Fact / Source 関係は全体を止める

plan（`kind = "citation"`）:

| Fact | cited Source | citation action |
| --- | --- | --- |
| CREATE | （seed の `source_keys` で関連付く） | `CREATE` |
| SKIP_EXISTS | 既存 Fact の `.sources` に含まれる | 同じ Fact + Source + `locator_text` があれば `SKIP_EXISTS`、なければ `CREATE` |
| SKIP_EXISTS | 既存 Fact の `.sources` に含まれない、または新規作成予定 | `CITATION_SOURCE_NOT_RELATED`（import blocked） |

- `--validate-only`: parser 規則と shrine identity のみ。DB 書き込みなし。
- `--dry-run`: 上表の plan を出す。DB 書き込みなし。
- apply: Fact の作成・skip の直後に citation を作る。同じ atomic transaction 内で行い、
  `citation created` が plan の `CREATE` 数と一致しなければ rollback する。
- 出力の summary 行は、seed が citation を持つ場合だけ末尾に `, citations created=N` を付ける。
  citation を持たない seed の出力は従来と同一。

citation は create-only で、既存 citation の更新・削除は行わない。citation の identity は
Fact + Source + `locator_text` 全体なので、同じ identity で他の field が異なる状態は存在しない。

## 7. 範囲外

- Recommendation ranking / Evidence Gate の usability 規則 / Position / G5・G6 の挙動の変更
- 既存 Production Source の `bibliography` からの頁情報の移行・書き換え
- 現行 Deity Fact の追加、nsrc-000009 の Knowledge Seed 作成
- `EvidenceLink` の流用
- Production への書き込み
