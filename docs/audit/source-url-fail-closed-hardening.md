# Source URL Fail-Closed Hardening

## Executive Summary

- Date: 2026-11-02
- Base: `develop` / `73bef9f3fc5b9f21751fc6d133a82ebf937f689c`
- 対象: `normalize_source_url` / `resolve_source_identity` / `parse_seed` / `import_shrine_knowledge` の Source 検証経路
- 結論: 不正な Source URL は **DB write 前**に、型付きの actionable error で止まる。`--validate-only` / `--dry-run` / 本 import のどれも未処理例外を出さない
- Source identity 契約（`source_type + normalize_source_url()`、metadata 一致時のみ REUSE）: **変更なし**。G7 preflight SQL（`scripts/migration_safety/sql/*_g7_*.sql`）との一致も維持
- 有効 URL の正規化結果: **変更なし**
- Shrine identity / Recommendation / production data: **変更なし**
- Mother Ship 判断待ち: §6 の4項目（現行挙動を維持し、記録のみ）

## 1. 変更前の挙動（事実：base に新テストを当てて再現）

| 入力の種類 | `--validate-only` | `--dry-run` | 本 import |
|---|---|---|---|
| 不正 port（`:abc`, `:99999`）/ 壊れた IPv6（`[2001:db8::1`） | **OK を返す** | 未処理 `ValueError`（traceback） | 未処理 `ValueError` |
| 空 host（`https://:443/a`）/ 制御文字（`exa\nmple`） | **OK を返す** | **`dry-run: OK` を返す**（unsafe decision） | transaction 内で `URLField` の `ValidationError` が未処理送出（rollback はされる） |
| 非文字列 url（`12345`） | OK を返す | 未処理 `AttributeError` | 未処理 `AttributeError` |
| 同 `source_type` の既存 Source に不正 port の URL が1行ある | — | 未処理 `ValueError` | 未処理 `ValueError` |
| `normalize_source_url` は通るが model が拒否（`//host/p`、前後空白、201文字超） | OK | **`dry-run: OK`** | `ValidationError` が未処理送出 |

`--validate-only` は Source URL を検査していなかった。`--dry-run` は
`normalize_source_url` の例外を握っておらず、CREATE 時に `_apply()` の
`full_clean()` が拒否する URL も OK と判定していた。

## 2. 変更内容

### 2.1 `normalize_source_url`：identity を決められない入力だけを raise

`SourceUrlError(ValueError)` を追加した。対象は **G7 preflight SQL が NULL
（identity にしない）を返す入力** に限る:

| 規則 | 例 | 変更前 |
|---|---|---|
| 非文字列（`None` は従来どおり `""`） | `123` | `AttributeError` |
| port が ASCII 数字以外 / 65535 超 | `:abc` `:+443` `:-1` `:４４３` `:443:80` `:99999` | `ValueError`（3.13）。3.11 の `int()` の寛容さに依存しない |
| `urlsplit` が拒否する括弧構造 | `[::1`、`[::1]x`、`[zzz]` | `ValueError` |
| 括弧内が IPv6 でない / zone id 付き / `[` の前に文字 | `[v1.x]`、`[::1%25eth0]`、`a[::1]` | 括弧が落ちて `https://v1.x/a` 等。**host `v1.x` と衝突** |

port の判定は SQL と同じ `^[0-9]+$` かつ 65535 以下で、`SplitResult.port` に頼らない。
Python 3.11.18 と 3.13 で、38入力の出力が一致することを確認した。

エラーメッセージには問題の部品だけを出し、URL 全体は出さない（userinfo に資格情報が
入っている可能性がある）。`urlsplit` の例外文言は netloc を含むことがあるため、
chain するだけで本文には写さない。

### 2.2 `validate_seed_source_url`：seed 入力だけに使う追加検査

次の入力は `normalize_source_url` では **従来どおりの値を返す**（§4）。そのうえで、
seed に書かれた場合だけ拒否する:

| 規則 | 例 | 正規化値（維持） |
|---|---|---|
| C0 制御文字・DEL | `exa\nmple`、`a\tb`、`\x01https://…` | `\t\r\n` は削除、先頭の C0 は strip |
| authority があるのに host が空 | `https://:443/a`、`https://user@/a` | `https:///a` |
| http/https で host が空 | `https:///a`、`https:/a`、`http://` | `https:///a` 等 |
| host に空白・backslash | `ex ample.com`、`example.com\a` | そのまま |

既存の DB 行には適用しないため、既存 Source の identity は変わらない。

### 2.3 `resolve_source_identity`

- seed URL を正規化できない → `INVALID_URL`
- 同じ `source_type` の既存行に正規化できない URL がある → `INVALID_EXISTING_URL`（該当 id を列挙）
- どちらの場合も例外は送出しない

既存行の不正 URL を読み飛ばす設計は採らなかった。その行が同じ文書である可能性を
否定できず、読み飛ばすと重複 Source を CREATE しうるため（fail closed）。

### 2.4 `parse_seed` / `import_shrine_knowledge`

- `_parse_source` が `validate_seed_source_url` で検査し、`sources[i].url: <理由>` を返す
  → `--validate-only` も失敗するようになった
- `_build_plan` は `INVALID_URL` / `INVALID_EXISTING_URL` を `CONFLICT` / `AMBIGUOUS` と同じく blocking error として扱う
- **CREATE 予定の Source に限り**、model field（`URLField`, `max_length=200`）の
  validators を plan 時に実行し、失敗を `SOURCE_URL_REJECTED_ON_CREATE` として報告する。
  `_apply()` が CREATE 時に行う `full_clean()` を前倒ししただけで、REUSE_EXISTING には適用しない

## 3. 互換性

- 有効 URL の正規化出力: 変更なし。既存16境界値（`test_source_url_sheet_parity.py`）は
  そのまま green。`:abc` は `ValueError` のサブクラスで送出されるため、既存テストも green
- G7 SQL parity テスト（`test_nsrc_*_g7_source_identity_sql.py` 他）: Python 3.11 で全件 green
- 影響確認（事実）: `backend/temples/data/knowledge_seeds/*.json` の Source URL 147件は、
  すべて `validate_seed_source_url` と model validator を通過する
- 未観測: **production DB の既存 Source URL**。`INVALID_EXISTING_URL` になるのは
  §2.1 の行（port 不正・括弧不正）だけ。port 不正と `urlsplit` が拒否する括弧は
  変更前から crash していたので、悪化はない。新たに停止するのは
  IPvFuture、zone id、`[` の前に文字がある行だけ

本番 import 前の read-only 確認（DB write なし）:

```python
# python manage.py shell
from temples.models import ShrineKnowledgeSource
from temples.services.knowledge_seed import SourceUrlError, normalize_source_url
bad = []
for s in ShrineKnowledgeSource.objects.exclude(url="").only("id", "source_type", "url"):
    try:
        normalize_source_url(s.url)
    except SourceUrlError as exc:
        bad.append((s.id, s.source_type, str(exc)))
print(len(bad), bad)
```

## 4. 変更しなかったもの（Source identity を変えないため）

当初は `normalize_source_url` 自体で制御文字と空 host を拒否した。しかし backend 全体の
テストで、G7 preflight SQL（10 set）がこの挙動を identity 契約として再現していることが
分かった（例：`"\x01https://…/m04/"`、`"…/cal\tendar/m04/"` は target と同一 identity）。
importer 側だけを変えると SQL preflight と importer の判定が食い違う。そのため、
これらは §2.2 の seed 入力検査に移した。

| 現行挙動（維持） | 理由 |
|---|---|
| `\t\r\n` を削除し、先頭の C0 を strip する | G7 SQL が再現している identity 契約 |
| 空 host を `https:///a` 等に正規化する | 同上（SQL も値を返す） |
| IPv6 の括弧を落とす（`[2001:db8::1]` → `2001:db8::1`） | 出力を変えると identity が変わる。括弧なしの形は入力として正規化できないので、有効入力同士は衝突しない |
| userinfo を落とす | 既存16境界値の契約。生 URL は `entry.url` のまま保存される |
| `:0443` を default port として除去する | 既存16境界値の契約（SQL も `ltrim('0')`） |
| 空 port（`host:`）・空 query（`?`）を除去する | 既存16境界値の契約 |
| port 0 を受理する | RFC 3986 上は構文的に有効。SQL も受理する |

## 5. 検証結果

- `test_source_url_sheet_parity.py` + `test_source_url_fail_closed.py` + `test_knowledge_seed_import.py`
  - 変更後: **179 passed**（Python 3.11.18 / 3.13、PostgreSQL 16 non-GIS）
  - base（`73bef9f`）に同じテストを当てた場合: **85 failed / 94 passed**（§1 はこの出力から作成）
- backend 全体（`pytest -n 4`、PostgreSQL 16 non-GIS、GIS 依存は skip）
  - Python 3.11.18（CI と同じ版）: **7662 passed, 27 skipped, 0 failed**
  - Python 3.13: 7661 passed, 1 failed。失敗は §7 の既存不具合で、base でも同じ1件が失敗する
- `ruff check` / `ruff format --check`: pass

## 6. Mother Ship 判断が必要な事項（未変更・記録のみ）

1. **制御文字・空 host を identity 上も不正にするか**: 実施するには、`normalize_source_url`
   と G7 SQL 10 set を同時に変える必要がある（identity 契約の変更）
2. **scheme なし / 非 http(s) URL**: `//host/p`、`host/p`、`ftp:`、`mailto:`、`javascript:`
   は正規化で受理される（`//…` は既存16境界値の契約）。CREATE 時は model validator が
   一部を止めるが、REUSE 経路では受理される
3. **IPv6 括弧の除去**（§4）: 括弧を保持する形に直すと normalized URL が変わり、
   a5b projection の出力など既存 artifact と一致しなくなる
4. **userinfo 付き URL**: 正規化では落ちるが、raw は DB に保存される。資格情報を含む URL を
   seed で拒否するかはポリシー判断

## 7. 残リスク

- **Python 3.13 での既存の不一致**（本 PR とは無関係。base でも再現）:
  `normalize_source_url("https:example.com/p/")` は 3.11 で `https:///example.com/p`、
  3.13 で `https:example.com/p` を返す（`urlunsplit` の挙動差）。G7 SQL は 3.11 側と一致する。
  CI は 3.11 なので green だが、runtime を 3.13 に上げると identity 値が変わる
- production の既存 Source URL は未観測（§3 の手順で事前に確認すること）
- `a5b_reproducibility_projection._source` は `SourceUrlError`（`ValueError`）を
  `ProjectionUnresolved` に変換していない。スコープ外のため未変更
- §6 の4項目は現行挙動のまま
