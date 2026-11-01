> **Status: Audit / Historical（read-only）。** `evidence_coverage_audit` command（PR-E1）を repository seed から作ったローカル DB で実行した結果の記録。**Production では実行していない**（承認済みの読み取り専用経路が無いため）。Production データ、schema、migration、seed、eligibility、ranking、score、API、LLM 設定、frontend、infra はいずれも変更していない。

# Evidence Coverage Audit（PR-E1）— Repository Seed Baseline（2026-11-01）

## 1. Metadata

| 項目 | 値 |
|---|---|
| Base | `origin/develop` @ `aadad69`（#3395 merge 後） |
| Command | `python manage.py evidence_coverage_audit`（`backend/temples/management/commands/evidence_coverage_audit.py`） |
| 計算ロジック | `backend/temples/services/evidence_coverage_audit.py` |
| 手順 | `docs/runbooks/evidence-coverage-audit.md` |
| 分類の定義 | `docs/audit/shrine-recommendation-evidence-eligibility-audit-2026-11-01.md` §6 |
| data_origin | `repository-seed-local` |
| read_only_guard | `postgresql_transaction_read_only` |

### 実行方法と限界

この session の環境には PostGIS が無く、`manage.py migrate` で本番相当のローカル DB を作れなかった。そこで pytest の test DB（NoGIS migration set）の中で、runbook §3.1 と同じ順序で次を実行した（scratch のみで、repo には追加していない）。

1. `bootstrap_production_data`
2. knowledge seed 26 ファイルを `import_shrine_knowledge` で import（26/26 成功）
3. command を実行

Production のロールアップ（PostGIS 版 migration）と schema の差は、この集計が読む列には影響しない想定である。ただし実測はしていない（[unknown]）。

## 2. 結果（Repository seed。Production の値ではない）

| 指標 | 値 |
|---|---:|
| Shrines（QA fixture 除外後） | 133 |
| eligible_now（現行 Shared Eligibility） | 115 |
| base_complete（D かつ H） | 107 |
| VERIFIED / PARTIAL_A / PARTIAL_B / INSUFFICIENT | 2 / 105 / 8 / 18 |
| D / H / C（いずれかの Need） | 111 / 110 / 2 |
| 柱の conflict（disputed の Fact しか無い柱） | 0 |
| 軸単位の conflict（review 記録 5 件を入力。未一致 0） | 2 社（明治神宮 4 軸、護王神社 1 軸） |
| disputed の Fact を持つ Shrine | 1（建部大社。他の Fact で D と H を満たすため PARTIAL_A） |
| 出典追跡可能な Fact の epistemic 内訳 | fact 14 / tradition 521 / interpretation 10 |

#3395 の repo probe と一致することを確認した（eligible 115、base_complete 107、PARTIAL_B 8 社、INSUFFICIENT 18 社、VERIFIED 2 社）。唯一の差は建部大社で、probe の簡易判定では CONFLICTING、本 command（#3395 §7.3 の refined rule）では PARTIAL_A になる。

### 2.1 Need 別

| Need | legacy_unattributed | ∩eligible | ∩base_complete | C | verified | conflicting |
|---|---:|---:|---:|---:|---:|---:|
| career | 70 | 61 | 60 | 0 | 0 | 0 |
| protection | 65 | 58 | 56 | 2 | 2 | 1 |
| health | 39 | 36 | 36 | 1 | 1 | 0 |
| love / marriage / relationship | 38 | 34 | 33 | 0 | 0 | 1 |
| rest | 34 | 31 | 31 | 1 | 1 | 0 |
| money | 30 | 25 | 25 | 2 | 2 | 0 |
| mental | 25 | 23 | 22 | 1 | 1 | 0 |
| courage | 20 | 19 | 19 | 0 | 0 | 0 |
| travel_safe | 15 | 15 | 15 | 2 | 2 | 1 |
| study / focus | 14 | 14 | 14 | 2 | 2 | 0 |
| family | 11 | 9 | 9 | 1 | 1 | 0 |
| communication | 0 | 0 | 0 | 0 | 0 | 0 |

`legacy_unattributed` は出典を追跡できない（未検証）ことを示すだけで、誤りであることは意味しない。

### 2.2 都道府県別（差が出る県のみ）

| 都道府県 | total | eligible_now | base_complete | PARTIAL_B | INSUFFICIENT |
|---|---:|---:|---:|---:|---:|
| 新潟県 | 14 | 10 | 4 | 6 | 4 |
| 東京都 | 31 | 25 | 24 | 1 | 6 |
| 千葉県 | 5 | 4 | 3 | 1 | 1 |
| 群馬県 | 4 | 1 | 1 | 0 | 3 |
| 埼玉県 | 9 | 7 | 7 | 0 | 2 |
| 栃木県 | 5 | 4 | 4 | 0 | 1 |
| 宮崎県 | 1 | 0 | 0 | 0 | 1 |

その他 24 都道府県は total = eligible_now = base_complete。VERIFIED は大阪府（大阪天満宮）と宮城県（大崎八幡宮）に各 1 社。

### 2.3 Trace chain の例（要約）

| 分類 | Shrine → Fact → Source | 相談根拠 | Reason inputs |
|---|---|---|---|
| VERIFIED | 大阪天満宮 → 祭神「菅原道真公」（tradition）、由緒 3 件（`regional_context` は interpretation、`historical_event` は神社公式のみの裏付けのため tradition）→ `shrine_official`（URL あり、2026-10-02 確認） | Channel B 7 件（focus / study / money / protection / travel_safe）。すべて出典追跡可能 | 祭神名、由緒の見出し、Channel B の Source 表記（「商売繁昌」など、Source 上の表記のまま） |
| PARTIAL_A | 明治神宮 → 祭神 2、`official_origin` 1 → `shrine_official`（2026-08-01） | Channel B なし。legacy タグ 縁結び / 厄除け / 交通安全（未検証）。review 記録により love / marriage / relationship / travel_safe は conflicting | 祭神名、由緒の見出し、legacy タグ |
| PARTIAL_B | 香取神宮 → 祭神 1 のみ（H なし） | legacy タグのみ（career / mental / protection） | 祭神名、legacy タグ |
| INSUFFICIENT | 長太稲荷神社 → Fact なし | なし | なし |

## 3. Production

**未実行（[unknown]）。** 実行には、オーナーによる読み取り専用経路の明示的な承認が必要である（runbook §2・§3.2）。実行後は `--compare-with` に本 baseline の JSON を渡し、差分を runbook §4 に従って記録する。
