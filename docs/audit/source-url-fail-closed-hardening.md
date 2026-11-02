# Source URL Fail-Closed Hardening

## Executive Summary

- Date: 2026-11-02
- Base: `develop` / `73bef9f3fc5b9f21751fc6d133a82ebf937f689c`
- 対象: `normalize_source_url` / `resolve_source_identity` / `parse_seed` / `import_shrine_knowledge` の Source 検証経路
- 結論: 不正な Source URL は **DB write 前**に、型付きの actionable error（`SourceUrlError` / plan error）で止まる
- 有効 URL の正規化結果: **変更なし**（既存16境界値のうち有効15件は同値を維持）
- Source identity 契約（`source_type + normalized URL`、metadata 一致時のみ REUSE）: **変更なし**
- Shrine identity / Recommendation / production data: **変更なし**
- Mother Ship 判断待ち: §6 の3項目（現行挙動を維持したまま記録のみ）

## 1. 変更前の挙動（事実：旧コードに新テストを当てて再現）

| 入力の種類 | `--validate-only` | `--dry-run` | 本 import |
|---|---|---|---|
| 不正 port（`:abc`, `:99999`）/ 壊れた IPv6（`[2001:db8::1`） | **OK を返す** | 未処理 `ValueError`（traceback） | 未処理 `ValueError` |
| 空 host（`https://:443/a`）/ 制御文字（`exa\nmple`） | **OK を返す** | **`dry-run: OK` を返す**（unsafe decision） | transaction 内で `URLField` の `ValidationError` が未処理送出（rollback されるが crash） |
| 非文字列 url（`12345`） | OK を返す | 未処理 `AttributeError` | 未処理 `AttributeError` |
| 同 `source_type` の既存 Source に不正 URL が1行ある | — | 未処理 `ValueError` | 未処理 `ValueError` |

`--validate-only` は Source URL を一切検査していなかった。`--dry-run` は
`normalize_source_url` が送出する例外を握っておらず、さらに空 host や
制御文字のように「例外にならず別 URL に潰れる」入力は plan を OK と判定していた。

正規化そのものの衝突（事実）:

- `https://:443/a` / `https://user@/a` / `https:/a` / `https:///a` → すべて `https:///a`
- `https://exa\nmple.com/a` → `https://example.com/a`（`urlsplit` が TAB/CR/LF を黙って削除）
- `https://[v1.x]/a`（IPvFuture）→ `https://v1.x/a`（実在しうる host `v1.x` と衝突）

## 2. 変更内容

### 2.1 `normalize_source_url`（`backend/temples/services/knowledge_seed.py`）

`SourceUrlError(ValueError)` を追加し、以下を **raise**（値を返さない）:

| 規則 | 例 |
|---|---|
| 非文字列（`None` は従来どおり `""`） | `123` |
| C0 制御文字・DEL を含む | `\t` `\n` `\r` `\x00` `\x7f` |
| `urlsplit` が拒否する構造 | `[::1`、`[::1]x`、`[zzz]` |
| port が ASCII 数字以外 / 65535 超 | `:abc` `:+443` `:-1` `:４４３` `:443:80` `:99999` |
| host に空白・backslash | `ex ample.com`、`example.com\a` |
| `[` の前 / `]` の後に余計な文字、括弧の不整合 | `a[::1]`、`[::1]x` |
| 括弧内が IPv6 アドレスでない、zone id 付き | `[v1.x]`、`[::1%25eth0]` |
| authority（`//`）があるのに host が空 | `https://:443/a`、`https://user@/a`、`//:80/x` |
| http/https で host が空 | `https:///a`、`https:example.com`、`http://` |

port 判定は `SplitResult.port` に依存せず自前で ASCII 数字を検査する。
Python のバージョンで `int()` の寛容さが異なっても受理集合が変わらないようにするため
（3.11.18 / 3.13 で38入力の出力が一致することを確認）。

エラーメッセージは問題のある部品だけを示し、URL 全体は出さない
（userinfo に資格情報が含まれる可能性があるため）。`urlsplit` の例外文言は netloc を
含みうるので、chain するだけで本文には転記しない。

### 2.2 `resolve_source_identity`

- seed URL が正規化不能 → `INVALID_URL`
- 同じ `source_type` の既存行に正規化不能な URL がある → `INVALID_EXISTING_URL`（該当 id を列挙）
- どちらも例外を送出しない

既存行の不正 URL を「読み飛ばす」設計は採らない。その行が同一文書である可能性を
否定できず、読み飛ばすと重複 Source を CREATE しうるため（fail closed）。

### 2.3 `parse_seed`（`_parse_source`）

`sources[i].url` を `normalize_source_url` で検査し、失敗時は
`sources[i].url: <理由>` を `errors` に積む。これにより `--validate-only` も失敗する。
非文字列 url は raw のまま保持し、identity 解決でも `INVALID_URL` になる。

### 2.4 `import_shrine_knowledge`（`_build_plan`）

- `INVALID_URL` / `INVALID_EXISTING_URL` を `CONFLICT` / `AMBIGUOUS` と同様に blocking error とする
- **CREATE 予定の Source に限り**、model field（`URLField`, `max_length=200`）の validators を
  plan 時に実行し、失敗を `SOURCE_URL_REJECTED_ON_CREATE` として報告する。
  `_apply()` が CREATE 時に必ず `full_clean()` するのと同じ検査を前倒ししただけで、
  REUSE_EXISTING 経路には適用しない（＝現在成功している import の挙動は変わらない）

## 3. 互換性

- 有効 URL の正規化出力: 変更なし。既存16境界値（`test_source_url_sheet_parity.py`）は
  そのまま green。唯一の例外ケース `:abc` は `ValueError` のサブクラスで送出されるため既存テストも green
- 新たに拒否される入力は、変更前に「例外」「別 URL への衝突」「apply 時 crash」の
  いずれかだったものに限る
- 影響確認（事実）: `backend/temples/data/knowledge_seeds/*.json` の全 Source URL
  （147件）が新規則で正規化可能、かつ model validator も通過
- 影響未確認（推測ではなく未観測）: **production DB の既存 Source URL**。
  新規則で正規化不能な行が同じ `source_type` に1行でもあると、その `source_type` の
  URL-backed Source を含む import はすべて `INVALID_EXISTING_URL` で停止する。
  変更前も port / IPv6 不正行は crash していたため悪化はないが、
  空 host・制御文字・IPvFuture・host 内空白の行は「従来通っていた → 停止」に変わる

本番投入前の read-only 確認手順（DB write なし）:

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

以下は「情報を落とす / 不自然」な正規化だが、出力を変えると既存 identity
（`a5b_reproducibility_projection` が出力する normalized URL、G7 SQL 生成テストの期待値を含む）
が変わるため **現状維持** とし、テストで固定した。

| 現行挙動 | 理由 |
|---|---|
| IPv6 の括弧を落とす（`https://[2001:db8::1]/p` → `https://2001:db8::1/p`） | 出力変更＝identity 変更。括弧なし形は入力として正規化不能なので有効入力同士の衝突はない |
| userinfo を落とす（`user:secret@`） | 既存16境界値の契約。生 URL は `entry.url` としてそのまま保存される |
| `:0443` を default port とみなし除去 | 既存16境界値の契約 |
| 空 port（`host:`）、空 query（`?`）を除去 | 既存16境界値の契約 |
| path 内の空白を保持（`/a b`） | 情報を落とさない。CREATE 時は model validator が拒否する |
| port 0 を受理 | RFC 3986 上は構文的に有効 |

## 5. 検証結果

- `test_source_url_sheet_parity.py` + `test_source_url_fail_closed.py` + `test_knowledge_seed_import.py`: 162 passed（Python 3.13 / 3.11.18、PostgreSQL 16 non-GIS）
- 旧コード（base）に同じ162テストを当てた場合: 83 failed / 79 passed（§1 の表はその出力）
- backend 全体: PR 本文に記載
- ruff check / ruff format --check: pass

## 6. Mother Ship 判断が必要な事項（未変更・記録のみ）

1. **scheme なし / 非 http(s) URL の扱い**: `//example.com/path`、`example.com/a`、
   `ftp://…`、`mailto:`、`javascript:` は正規化で受理される（`//…` は既存16境界値の契約）。
   CREATE 時は model validator が `//…` と `example.com/a` を止めるが、REUSE 経路と
   正規化関数自体は受理する。拒否に変えると Source identity 契約の変更になる
2. **IPv6 括弧の除去**（§4）: 正しい形（括弧保持）へ直すと normalized URL が変わり、
   a5b projection 出力など既存 artifact と不一致になる
3. **userinfo 付き URL**: 正規化では落ちるが raw は DB に保存される。資格情報を含む URL を
   seed で拒否するかはポリシー判断

## 7. 残リスク

- production の既存 Source URL は未観測（§3 の手順で事前確認が必要）
- `a5b_reproducibility_projection._source` は `SourceUrlError`（`ValueError`）を
  `ProjectionUnresolved` に変換していない。本タスクのスコープ外のため未変更
- §6 の3項目は現行挙動のまま
