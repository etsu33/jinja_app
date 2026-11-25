> **[G1 追記 / point-in-time note]** 本書はPR-F3以前の時点で作成されたpoint-in-time auditである。本文中の「canonical registryは未定義 / 意図的に空」「46件のGoriyakuTagへの対応表は未確定」等の記述は、**当時の事実**であって現行の事実ではない。G1のDATA_REVIEWでgoriyaku canonical registryはexactly 18件でactivated、alias registryはexactly 1件（`八方除け -> all_direction_warding`）で確定している。現行契約は`docs/knowledge/evidence-foundation-shared-contract.md`を参照すること。本書の監査結果そのものは記録として改変していない。
>
> **Status: Audit only — read-only. No model change, no migration, no DB write, no backfill, no seed change, no admin change, no Recommendation/Ranking/Concierge change.**
>
> 本書は、GoriyakuTag / Evidence Foundation に関する過去監査群を、最新`develop`・現行コード・（到達可能な範囲の）DBと突き合わせ、**過去監査の再発見ではなく、過去監査と現在との差分**を明示する目的で新規作成した。
>
> 新規作成の理由: 既存の関連文書（`docs/audit/compass-purpose-goriyaku-mapping.md`等）はいずれも特定PRの完了記録（historical record、`NEED_TO_GORIYAKU_IDS`の特定補正のみを対象）であり、上書き対象として不適切。`docs/knowledge/evidence-foundation-shared-contract.md`はPR-F1/F2で実装済みの契約そのものを記録する文書であり、責務が異なる（「何を実装したか」であって「goriyakuについて何が未解決か」ではない）。「Current Status / Delta」を主目的とする既存文書は存在しないため、本書を新規作成した。

# Goriyaku Evidence Foundation Preflight Audit

## 1. Repository Baseline

- **develop base SHA**: `dbe686b1b245740e3ec9ab27c3c511c19eb44ce4`（`docs: モバイルWeb現在地取得不具合の原因を監査 (RH3-4) (#2677)`）
- **branch**: `audit/goriyaku-evidence-foundation-refresh`（このSHAから作成）
- **PR-F2確認**: `HistoryThemeAssignment`（`backend/temples/models.py:582`）、`HistoryThemeAssignmentAdmin`/`HistoryThemeAssignmentInline`（`backend/temples/admin.py:333,369`）、`backend/temples/migrations/0102_history_theme_assignment_foundation.py`、`backend/temples/migrations_nogis/0009_historythemeassignment.py`が本SHA上に存在することを確認済み（`git log origin/develop --oneline`で`7b8708eed feat: add HistoryTheme Evidence Foundation (#2675)`のマージを確認）。

**関連ファイル一覧（本監査で直接確認したもの）**:

```
backend/temples/models.py                                  # GoriyakuTag, Shrine.goriyaku_tags, ShrineSubmission.goriyaku_tags, HistoryThemeAssignment
backend/temples/admin.py                                    # GoriyakuTagAdmin, ShrineAdmin.filter_horizontal, HistoryThemeAssignment*(precedent)
backend/temples/management/commands/backfill_goriyaku_tags.py
backend/temples/domain/need_to_goriyaku_tag_ids.py
backend/temples/domain/evidence_taxonomy.py                 # PR-F1 taxonomy registry (namespace/version/canonical key validator)
backend/temples/domain/evidence_provenance.py                # PR-F1 provenance contract
backend/temples/domain/evidence_qualification.py             # PR-F1 qualification contract
backend/temples/domain/history_theme_taxonomy_v1.py           # PR-F2 taxonomy registry precedent
backend/temples/services/concierge_chat_ranking.py            # matched_by_gid / matched_by_tag / matched_by_user_selected_gid
backend/temples/services/shrine_submission.py                 # approve_shrine_submission()
backend/temples/api/serializers/shrine.py                     # GoriyakuTagSerializer
docs/knowledge/evidence-foundation-shared-contract.md
docs/audit/production-migration-modules-nogis-root-cause.md
docs/audit/personal-meaning-shrine-evidence-readiness.md
docs/audit/goriyaku-mapping-master-integrity.md / -correction.md
docs/audit/remaining-need-goriyaku-semantic-mapping.md / safe-remaining-need-goriyaku-mapping-correction.md
docs/audit/compass-purpose-goriyaku-mapping.md / -correction.md
```

---

## 2. Previous Audit Inventory

| File | Audit Purpose | Current Relevance |
|---|---|---|
| `docs/audit/personal-meaning-shrine-evidence-readiness.md` | PR-E: `PremiumMeaningShrineEvidence.relevantToConsultation`/`.relevantToVisit`が生成元を持たずhardcoded `null`であることを発見。Evidence Foundation構想全体の起点。 | **STILL_VALID** — この文書自体はPersonal/Action Meaning層の話であり、PR-F1〜F3のEvidence Foundation基盤層とは別責務。基盤層が未接続である限り、この文書の結論（relevance judgmentが存在しない）は現在も成立する。 |
| `docs/audit/production-migration-modules-nogis-root-cause.md` | `temples.migrations_nogis`が`temples/migrations/`と独立した手動維持squashed lineageであることの根本原因監査。 | **STILL_VALID** — PR-F2のNoGIS migration追加時に実地で再確認済み（`0009_historythemeassignment.py`が`0008`をheadとする独立lineageに正しく追従）。PR-F3で`ShrineGoriyakuAssignment`を追加する際も同じ二重lineage対応が必要になる（下記5参照）。 |
| `docs/audit/goriyaku-mapping-master-integrity.md` + `-correction.md` | `NEED_TO_GORIYAKU_IDS`の一部IDが当時の39行canonical masterに存在しない（42/43/44/45）ことを発見し補正。 | **RESOLVED**（この文書が対象とした具体的補正について） — 補正は既に`need_to_goriyaku_tag_ids.py`へ反映済み（コード内コメントで確認）。ただし「NEED_TO_GORIYAKU_IDSはRecommendation Signal専用でEvidence provenanceに使えない」という上位の設計境界自体はEvidence Foundation文脈で改めてSTILL_VALID（後述）。 |
| `docs/audit/remaining-need-goriyaku-semantic-mapping.md` + `docs/audit/safe-remaining-need-goriyaku-mapping-correction.md` | `relationship`/`health`/`focus`/`family`のNEED_TO_GORIYAKU_IDS補正、`marriage`/`communication`/`mental`/`courage`はMother Ship判断待ちとして保留。 | **STILL_VALID**（保留分）+ **RESOLVED**（SAFE_CORRECTIONS分） — `communication`は空集合のまま（2026-08-29 Mother Ship決定でEVIDENCE_LIMITED/DISABLE_GID_EVIDENCE）、`family`はNARROW方針で補正済み。現在のコードと文書の記述は一致している。 |
| `docs/audit/compass-purpose-goriyaku-mapping.md` + `-correction.md` | Need→Goriyaku mappingのVALID/QUESTIONABLE/INVALID/MISSING分類。 | **STILL_VALID** — 分類根拠として現行`need_to_goriyaku_tag_ids.py`のコメントから直接参照されている。 |
| `docs/knowledge/evidence-foundation-shared-contract.md` | PR-F1（Shared Contracts）・PR-F2（HistoryThemeAssignment）で実装した契約の記録。 | **STILL_VALID** — PR-F3の直接の前提。「HistoryThemeAssignment」節がPR-F3の構造テンプレート（6章参照）。 |

**このセッション内で過去に生成されたが、リポジトリへcommitされなかった監査（chat-onlyで実施、ファイルパスなし）**: 本セッションの以前の会話ターンで「GoriyakuTag Relationship-Origin Readiness Audit」「Relationship Origin Evidence Remediation Design（Phase 1–3）」「Evidence Foundation Feasibility Audit」「Evidence Foundation Live Data Readiness Audit」「Evidence Foundation Live DB Data Audit」「Evidence Foundation Implementation Readiness Audit」が実施されたが、いずれもMother Shipの明示指示（「文書を作成しない」）によりchat応答としてのみ提供され、`docs/`へcommitされていない。したがってfile pathは存在しない。本書はそれらchat監査の結論のうち現時点のコード・DBと再照合可能なものを、file-based auditと同じ厳密さで再検証し、Delta Classification Tableへ統合した（3節参照）。

---

## 3. Delta Classification Table

| Previous Finding | Previous State | Current Evidence | Classification | PR-F3 Impact |
|---|---|---|---|---|
| Shrine.goriyaku_tags is a plain M2M with no through model, no assignment identity, no provenance, no lifecycle | GoriyakuTag Feasibility Audit（chat-only）で確認 | `models.py:252` `goriyaku_tags = models.ManyToManyField("GoriyakuTag", related_name="shrines", blank=True)` — through modelなし、追加fieldなし（今回再確認） | **STILL_VALID** | ShrineGoriyakuAssignmentは既存M2Mを置き換えず別モデルとして追加する（確定事項2/3） |
| through-model conversion is needed to add provenance to the M2M | 初期のGoriyaku Feasibility Auditで「Option A（through-model化）」が検討された | Mother Ship確定事項3/4により、legacy M2Mは完全維持・through-model conversionはHOLD。PR-F2で`HistoryThemeAssignment`が「既存フィールドを変更せず別モデルを追加する」という設計で実装され、実際に機能した前例が存在 | **SUPERSEDED** — through conversion要件はOption B（別モデル追加）採用により置き換え済み。ただしHOLDそのものが「不要と確定した」わけではなく「現在のロードマップでは要求されていない」という位置づけ（確定事項4のまま） | PR-F3はShrineGoriyakuAssignmentを新規追加するのみで、既存M2Mへは触れない |
| `filter_horizontal`（`ShrineAdmin.filter_horizontal = ("goriyaku_tags",)`）は、through model化した場合にrequired fieldを持つ through modelと非互換という技術的blocker | Feasibility Audit / Implementation Readiness Auditで、through-model化（Option A）を選んだ場合のblockerとして記録 | `admin.py:398` `filter_horizontal = ("goriyaku_tags",)` は現在も legacy M2M に対してそのまま存在（今回再確認）。PR-F3はOption B（legacy M2M維持 + 別モデル追加）を採用するため、この`filter_horizontal`は一切変更を必要としない | **SUPERSEDED**（blockerとしての意味において） — Option Bを採用する限り、この制約自体が発火する状況（through-model化）が発生しない。「filter_horizontalが技術的制約である」という事実自体はSTILL_VALIDだが、「PR-F3にとってのblocker」という意味では無関係化した | PR-F3のGoriyakuTag admin拡張は、PR-F2の`HistoryThemeAssignmentInline`と同型の別Inline追加で対応可能（`filter_horizontal`に触れない） |
| GoriyakuTag taxonomyがopen-ended（`backfill_goriyaku_tags.py`の`get_or_create`により自由増殖） | Feasibility Audit / Live DB Auditで指摘 | `backfill_goriyaku_tags.py:126` `tag, created = GoriyakuTag.objects.get_or_create(name=name)` は現在も無条件（今回再確認）。`GoriyakuTagAdmin`（`admin.py:273`）も自由rename/create のまま（list_display/search_fieldsのみ、governance gateなし） | **STILL_VALID** | Evidence Foundation側のcanonical registryは、legacy taxonomy（この open-ended な`GoriyakuTag.name`）とは分離した別レイヤーとして構築する必要がある（Option Bの前提と整合）。PR-F3では既存GoriyakuTagの是正は行わない（確定事項7/8） |
| NEED_TO_GORIYAKU_IDSが production Ranking の実際の入力として使われている | 複数の過去監査で確認 | `concierge_chat_ranking.py:6` `from temples.domain.need_to_goriyaku_tag_ids import need_tags_to_goriyaku_ids`、および`matched_by_gid`/`matched_by_tag`/`matched_by_user_selected_gid`（614-693行、947-1129行）が現在も実装されている（今回再確認、コード引用は5節参照） | **STILL_VALID** | リスクとして存在し続けるが、PR-F3実装のために変更が必要という意味ではない（確定事項5により、これはRecommendation Signal専用の別レイヤーとして扱われ続ける）。「リスクが存在する」と「PR-F3で変更が必要」は分離して記載（5節） |
| ShrineSubmission.goriyaku_tags is a dead-end field never connected to GoriyakuTag/Shrine.goriyaku_tags | Live DB Data Audit（chat-only）で code trace により確認 | `shrine_submission.py:210-211`（コメント: "投稿者選択の goriyaku_tags / note は審査時の参考情報として扱う。検索・推薦に使う Shrine.goriyaku_tags は admin が確認後に確定するため、ここでは自動反映しない。"）、`approve_shrine_submission()`内で`submission.goriyaku_tags`が一切読まれていないことを今回再確認 | **STILL_VALID** | PR-F3でこのdead-end channelを勝手に接続する提案は行わない（Mother Ship決定境界の対象） |
| GoriyakuTag: 46件、used=39、unused=7、exact duplicate=0、M2M relations=284、orphan=0、NEED_TO_GORIYAKU_IDS 29/29 IDs exist | Mother Ship提供のLive DB Audit結果（このセッションの前ターンで提供、Codex自身による測定ではない） | 本セッションのsandboxはDB接続不可（`OperationalError: failed to resolve host 'db'`、今回も再確認）。数値の独立した再測定はできなかった | **STILL_OPEN**（再測定という意味で） / 数値そのものは参考値として利用可能 | Live measurementが必要な場合は、DB到達可能な環境（Mother Ship側 or CI環境）での再測定が前提。本書では推定しない（4節） |
| PR-F1のTaxonomyVersion表現が当初int `1`だった | PR-F1/F2の会話内でMother Ship指摘により是正済み | `evidence_taxonomy.py`の`TaxonomyVersion.version: str`、`_CURRENT_TAXONOMY_VERSION_BY_NAMESPACE = {"history_theme": "v1", "goriyaku": "v1"}`（今回再確認） | **RESOLVED** | `goriyaku`側のtaxonomy versionは既に`"v1"`として登録済み（namespace自体はPR-F1で両方登録済み、goriyaku側のcanonical key一覧は依然未定義 — 6節） |
| PR-F1のProducer/Mechanism列挙が当初`human`/`system`だった | PR-F1の会話内でMother Ship FINAL値により是正済み | `evidence_provenance.py`の`EVIDENCE_PRODUCERS = ["admin","curator","migration","verified_import","controlled_automation"]`、`EVIDENCE_MECHANISMS = ["manual_review","source_backed_import","verified_migration","controlled_rule"]`（今回再確認） | **RESOLVED** | PR-F3の`ShrineGoriyakuAssignment`はこのFINAL値をそのまま再利用可能（新しいenumを作らない） |
| GoriyakuTag Evidence Foundationのlifecycle語彙は historyTheme と分離すべき（ACTIVE/REVOKED、historyThemeのACTIVE/SUPERSEDEDとは異なる） | Remediation Design（chat-only）で確定 | `HistoryThemeAssignment.Lifecycle`は`ACTIVE`/`SUPERSEDED`のみ（`models.py:593-595`、今回再確認）。goriyaku側の`ACTIVE`/`REVOKED`はまだコードとして存在しない | **STILL_VALID**（設計方針として） / goriyaku側の実装は**NEW_FINDING**ではなく単に未着手 | PR-F3で`ShrineGoriyakuAssignment.Lifecycle`を`ACTIVE`/`REVOKED`として新規実装する（historyThemeの`Lifecycle` TextChoicesパターンを再利用可能、ただし値は異なる） |
| Existing M2M Compatibility Option Aは`filter_horizontal`のDjango制約により危険、Option B（additive、legacy M2M維持）が最も安全 | Feasibility Audit（chat-only）で評価、Mother Ship確定事項2/3で正式にOption B相当が採用された | 現在のMother Ship確定事項1-4がOption Bの内容そのものと一致（今回の指示文で再確認） | **RESOLVED**（Mother Ship決定として確定） | PR-F3のスコープそのもの |

---

## 4. Live Data Status

**DBアクセス: 不可（本セッション）。**

```
OperationalError: failed to resolve host 'db': [Errno -2] Name or service not known
```

`backend/shrine_project/settings.py`の`DB_HOST`が`db`（Docker Compose相当のホスト名）に解決され、このsandbox環境からは到達不能。この事実は本セッション内で複数回、複数タイミングで再確認されており（PR-F1/F2作業時含む）、一貫している。

**推定は行わない。** 以下は前セッションでMother Shipから「測定済みの事実として扱ってよい」と提供された数値であり、本監査が独自に測定したものではない（出典: PR-F1修正時のMother Shipメッセージ「LIVE DB FACTS」）。今回のsandboxでは再測定できなかったため、**参考値（NOT INDEPENDENTLY RE-VERIFIED THIS SESSION）**として記載する。

| 項目 | 値（Mother Ship提供、未再測定） |
|---|---|
| total GoriyakuTag rows | 46 |
| distinct tag names | 46 |
| category distribution | 全46件が`ご利益` |
| used tags（≥1 shrine割当） | 39 |
| unused tags | 7 |
| exact duplicate names | 0 |
| shrine-tag relation row count | 284 |
| duplicate shrine-tag relations | 0 |
| orphan relations（missing Shrine / missing GoriyakuTag） | 0 / 0 |
| shrines with 0 tags | 7 |
| shrines with 1 tag | 0 |
| shrines with 2 tags | 14 |
| shrines with 3 tags | 80 |
| shrines with 4+ tags | 4 |
| NEED_TO_GORIYAKU_IDS referenced IDs existence | 29/29 存在（missing=0） |
| NEED_TO_GORIYAKU_IDS assigned/unassigned | 29件中7件が0 shrine assignment（2, 5, 6, 11, 12, 14, 15） |

**今回のコード側再検証で裏付けが取れた項目**（DB接続なしで確認可能な範囲）:
- `NEED_TO_GORIYAKU_IDS`の参照ID集合を`need_to_goriyaku_tag_ids.py`から直接計算した結果、distinct ID数 = **29**（Mother Ship提供値と一致、3節参照）。これはコードのみから導出可能な値であり、DBアクセス不要で本監査が独自に再確認した。

**正規化重複監査（Unicode/空白/句読点）**: DBアクセス不可のため、実データに対する正規化重複判定は**NOT MEASURED**のまま。Mother Ship提供の近似候補リスト（前ターン記載）は以下のグループが挙げられていたが、これは実データからの抽出結果であり本監査が独自に生成したものではない。分類はいずれも`NEEDS_HUMAN_REVIEW`または`POSSIBLE_ALIAS`相当のものとして、同一視・merge判定はしない:

```
厄除け・方除け / 厄除け / 方除け        -> NEEDS_HUMAN_REVIEW（複合語と単独語の関係）
開運招福 / 開運                          -> NEEDS_HUMAN_REVIEW
勝運・必勝祈願 / 勝運                    -> NEEDS_HUMAN_REVIEW
仕事運・出世 / 仕事運 / 出世運           -> NEEDS_HUMAN_REVIEW
金運・商売繁盛 / 金運 / 商売繁盛         -> NEEDS_HUMAN_REVIEW
子宝・安産 / 子宝 / 安産                 -> NEEDS_HUMAN_REVIEW
八方除 / 八方除け                        -> FORMATTING_VARIANT候補（送り仮名差）
芸能 / 芸能運                            -> FORMATTING_VARIANT候補（接尾辞差）
健康長寿 / 延命長寿                      -> POSSIBLE_ALIAS候補（意味重複の可能性、断定しない）
航海安全 / 海上安全                      -> POSSIBLE_ALIAS候補
家内安全 / 家庭円満                      -> NEEDS_HUMAN_REVIEW（意味が異なる可能性あり、断定しない）
縁結び / 恋愛成就                        -> NEEDS_HUMAN_REVIEW（意味が異なる可能性あり、断定しない）
```

いずれも本監査ではmerge/alias化を判定しない（確定事項7）。実データでの再測定・最終分類はDB到達可能な環境でのフォローアップが必要（8節）。

---

## 5. Recommendation Compatibility

**existing M2M**: `Shrine.goriyaku_tags`（`ManyToManyField("GoriyakuTag")`、`models.py:252`）は変更されていない。今回のコード確認で、through modelなし・assignment identityなし・provenanceなし・lifecycleなしという構造は当初監査時点から不変であることを確認した。

**GoriyakuTag IDs**: `GoriyakuTag.id`は今回のコード確認でも他の一切のガバナンスなしに`GoriyakuTagAdmin`経由でリネーム・新規作成可能（`admin.py:273`、`list_display=("id","name","category")`、`search_fields=("name","category")`、governance gateなし）。

**NEED_TO_GORIYAKU_IDS**: 現行`need_to_goriyaku_tag_ids.py`から独立して再計算した結果、29の distinct GoriyakuTag ID が参照されている（3節）。`need_tags_to_goriyaku_ids()`は`concierge_chat_ranking.py`から`import`され、production Ranking の入力として使われ続けている。

**Ranking consumers**（今回コード確認、`concierge_chat_ranking.py`）:
- `matched_by_tag`（615, 678行、`need_tags_clean`と`shrine_tag_set`の交差）
- `matched_by_gid`（616, 688-693行、`need_tags_to_goriyaku_ids()`経由）
- `matched_by_user_selected_gid`（618, 667-673行、UI選択`requested_goriyaku_tag_ids`との交差）
- いずれも`_attach_breakdown`相当の関数（947-979行）でスコア内訳へ反映され、`evidence=["goriyaku_tag_ids"]`/`evidence=["requested_goriyaku_tag_ids"]`のラベルで区別される

**リスクとPR-F3変更要否の分離**:
- **リスクとして存在する事実**: NEED_TO_GORIYAKU_IDSは29 ID分がRanking Signalとして production で使われ続けており、これが変わればRanking挙動が変わる（STILL_VALID）。
- **PR-F3で変更が必要かどうか**: **不要**。Mother Ship確定事項5により、NEED_TO_GORIYAKU_IDSはRecommendation Signal専用として維持され、Evidence Foundation（`ShrineGoriyakuAssignment`）は完全に別レイヤーとして追加されるため、PR-F3の実装そのものはこのファイルに一切触れる必要がない。

---

## 6. Canonical Registry Readiness

| 項目 | 状態 |
|---|---|
| code-level taxonomy registry共通基盤の所在 | **ALREADY_AVAILABLE** — `backend/temples/domain/evidence_taxonomy.py`（PR-F1）。`EVIDENCE_TAXONOMY_NAMESPACES = ["history_theme", "goriyaku"]`として`goriyaku`namespace自体は既に登録済み。`get_current_taxonomy_version("goriyaku")`は`TaxonomyVersion(namespace="goriyaku", version="v1")`を返す（今回直接importして確認可能な構造。DBアクセス不要）。`validate_canonical_semantic_key()`も`goriyaku:<key>`形式のformat検証に対して汎用的に使える（namespace非依存の実装） |
| historyTheme v1 registryの構造（再利用可能パターン） | **ALREADY_AVAILABLE** — `backend/temples/domain/history_theme_taxonomy_v1.py`が具体的な参照実装。`HISTORY_THEME_V1_CANONICAL_KEYS: Dict[str, str]`（ローカルkey→日本語表示ラベル）、`validate_history_theme_v1_canonical_key()`（PR-F1のformat validatorを呼び出した上でnamespace一致・key所属を追加検証）という2段構成。goriyaku側も同型の`goriyaku_taxonomy_v1.py`相当のファイルを追加すれば流用できる構造だが、**このパターンをコピーして実装することは本監査のスコープ外**（監査のみ） |
| goriyaku側の既存registry | **NEEDS_PR_F3** — 現時点で`goriyaku_taxonomy_v1.py`相当のファイルは存在しない。`EVIDENCE_TAXONOMY_NAMESPACES`にnamespace自体は登録済みだが、実際に有効な`goriyaku:<key>`のcanonical key一覧（46件のGoriyakuTagに対応する具体的key文字列）は一切定義されていない |
| 既存46タグへのcanonical key対応表 | **DATA_REVIEW** — 本監査ではcanonical key命名・対応表を一切作成しない（確定事項13、Mother Ship決定境界）。以下は事実の記録のみ: 46タグ中、7タグ（10節と同一のID群、参照0件のタグ）を含め、いずれも現時点で「どの日本語ラベルにどのcanonical key文字列を当てるか」は未決定 |
| 正規化重複（4節記載の12グループ）のalias/merge判定 | **DATA_REVIEW** | 断定禁止（確定事項7、9節Mother Ship Decision Needed） |
| Shrine×GoriyakuTag assignment（ShrineGoriyakuAssignment）のprovenance/lifecycle実装そのもの | **NEEDS_PR_F3** — PR-F1の`evidence_provenance.py`（producer/mechanism、再利用可能）とPR-F2の`HistoryThemeAssignment`モデル構造（6節下記）はすでに揃っているが、goriyaku固有のモデル自体はまだ実装されていない |
| Source Evidence Link・Qualification | **HOLD**（PR-F4のスコープ、確定事項10） |

---

## 7. PR-F2 Precedent Confirmation

最新develop上に以下が存在することを確認した（`git show`/直接ファイル読み取りで確認、今回のsandboxでも検証可能。DBアクセス不要）:

- `HistoryThemeAssignment`（`models.py:582`）: `shrine` FK（`on_delete=CASCADE`）、`canonical_key`（`CharField(max_length=64)`）、`taxonomy_version`（`CharField(max_length=8)`）、`lifecycle`（`TextChoices`: `ACTIVE`/`SUPERSEDED`）、`producer`/`mechanism`（PR-F1 `EVIDENCE_PRODUCERS`/`EVIDENCE_MECHANISMS`をそのまま`choices`化、重複定義なし）、`assigned_at`（`DateTimeField`、必須）、`created_at`（`DateTimeField(default=timezone.now)`）
- `taxonomy_version = CharField` / `"v1"`: 確認済み（当初`IntegerField`だったものがPR-F1/F2是正で`CharField`化。3節参照）
- `Lifecycle`: `ACTIVE` / `SUPERSEDED`の2値のみ、`models.TextChoices`
- provenance fields: `producer`/`mechanism`/`assigned_at`の3フィールド構成、PR-F1由来
- normal migration: `backend/temples/migrations/0102_history_theme_assignment_foundation.py`（単一`CreateModel`、partial `UniqueConstraint(fields=["shrine"], condition=Q(lifecycle="ACTIVE"))`）
- NoGIS migration: `backend/temples/migrations_nogis/0009_historythemeassignment.py`（同一スキーマ、dependency のみ`0008_actionevent_conciergehistory_and_more`という別lineage head）

**PR-F3で流用可能な構造パターン**（記録のみ、コピー実装はしない）:
1. 既存フィールドを一切変更せず、別モデルとして追加する設計（compatibility layer分離）
2. `Lifecycle`を`TextChoices`のネストクラスとして定義し、`Meta.constraints`にpartial `UniqueConstraint`を1本追加する形（ただしgoriyakuは「1 shrineにつき1 ACTIVE」ではなく「1 shrine×1 canonical tag×1 taxonomy versionにつき1 ACTIVE」という別の一意性キーになる点はPR-F2と異なる — 単純なコピーでは対応できない）
3. `producer`/`mechanism`をPR-F1の`EVIDENCE_PRODUCERS`/`EVIDENCE_MECHANISMS`から`choices=[(v,v) for v in ...]`として直接構築し、新しいenumを作らない
4. 通常migration・NoGIS migrationの両方を同一PR内で生成する必要がある（5節/`production-migration-modules-nogis-root-cause.md`参照）。NoGIS側は`0009`をheadとして`0010_...`が次番号
5. Admin: 標準の`@admin.register`クラス + `TabularInline`の両方を用意し、既存`ShrineAdmin.inlines`へ追加する（既存inlineを削除・置換しない）

---

## 8. PR-F3 Ready Scope

以下は、現時点の証拠に基づき、Mother Shipの既存判断と衝突せずにPR-F3実装へ含めてよいと判断できる項目（実装はしない、リストのみ）:

- `ShrineGoriyakuAssignment`モデルの新規追加（`shrine` FK、`canonical_key`、`taxonomy_version`、`lifecycle`、`producer`、`mechanism`、`assigned_at`、`created_at`の8フィールド構成、PR-F2と同型）
- `Lifecycle` = `ACTIVE` / `REVOKED`（historyThemeの`ACTIVE`/`SUPERSEDED`とは異なる語彙、Remediation Designで確定済み）
- 一意性制約: `UniqueConstraint(fields=["shrine","canonical_key","taxonomy_version"], condition=Q(lifecycle="ACTIVE"))`相当（shrine単位ではなくshrine×tag×version単位、確定事項の「1 shrine×1 canonical tag×1 taxonomy versionにつき1 ACTIVE」に対応）
- PR-F1の`EVIDENCE_PRODUCERS`/`EVIDENCE_MECHANISMS`のそのままの再利用（新規enum作成禁止）
- PR-F1の`evidence_taxonomy.py`の`goriyaku`namespace・`"v1"`versionのそのままの再利用
- 通常migration・NoGIS migration（`0009`の次番号）の両方の追加
- 既存`ShrineAdmin.filter_horizontal = ("goriyaku_tags",)`・`GoriyakuTagAdmin`は無変更のまま、`ShrineGoriyakuAssignmentInline`を別途追加

これらはいずれも「既存M2M・既存GoriyakuTag・既存Recommendationに一切触れない」という確定事項1-4/9と矛盾しない範囲に限定される。

---

## 9. Mother Ship Decision Needed

Codex自身では決定しない。以下のみを判断待ちとして提示する。

```
MOTHER_SHIP_DECISION_NEEDED:
- issue: 46件のGoriyakuTagへの具体的canonical key（goriyaku:<stable_key>）の命名・対応表
- repository evidence: goriyaku側taxonomy registryが未実装（6節 NEEDS_PR_F3）。historyTheme側は7カテゴリの日本語ラベル→英語keyの対応表が既にPR-F2で実装済みの前例あり（history_theme_taxonomy_v1.py）
- available options:
  A) PR-F3実装時に、全46タグへ一括でcanonical keyを割り当てる
  B) PR-F3では registry infrastructure のみ実装し、実際のkey割当は別の限定スコープPRへ分離する
  C) 使用頻度の高いタグ（used=39件、4節参照）のみ先行してkey割当し、unused 7件は保留する
- consequence of each option:
  A) 実装量が大きくなる。誤ったkey命名を後から変更するコストが発生しうる
  B) PR-F3のスコープが小さくなるが、実際にShrineGoriyakuAssignmentを使い始めるにはさらに1PR必要になる
  C) 段階的だが、unused 7件がいつまでも未対応のまま残るリスクがある
```

```
MOTHER_SHIP_DECISION_NEEDED:
- issue: 4節記載の12件の正規化重複候補（例: 厄除け・方除け/厄除け/方除け）をalias統合するか、独立タグとして扱うか
- repository evidence: 全てexact-string-matchでは重複しない（Mother Ship提供の"exact duplicate names = 0"と整合）が、Unicode/句読点正規化・部分文字列関係では重複候補が存在する（Mother Ship提供の近似候補リスト、本監査では独自に実データ再検証できていない）
- available options:
  A) 全てを独立タグとして扱い、alias機構を作らない
  B) Alias Registry（確定事項13の将来構想）を用意し、表示は別々でも意味的に関連づける
  C) 個別に人手レビューし、統合すべきものだけをMother Ship判断で個別にmerge
- consequence of each option:
  A) シンプルだが、将来のcanonical key割当時に同じ問題を先送りするだけになる
  B) Alias Registry自体の設計・実装コストが発生する（PR-F3のスコープを超える可能性）
  C) レビューコストが発生するが、誤merge のリスクは最小
```

```
MOTHER_SHIP_DECISION_NEEDED:
- issue: GoriyakuTag taxonomy governance（legacy側のfree-text get_or_create / GoriyakuTagAdmin自由編集）を、PR-F3と同時にある程度制限するか、完全に別トラックとして先送りするか
- repository evidence: `backfill_goriyaku_tags.py`の`get_or_create`と`GoriyakuTagAdmin`は現在も無制限（3/5節）。Evidence Foundation側のcanonical registryとは独立して動き続ける
- available options:
  A) legacy側governanceには一切触れず、PR-F3はEvidence Foundation層のみ追加する（Option Bの精神に最も忠実）
  B) legacy側にも軽微な警告・レビューフラグ程度を追加する
  C) legacy側governanceの見直しを別の独立したPRとして計画する
- consequence of each option:
  A) 最小スコープ。ただしlegacy taxonomyの無秩序な増殖は止まらない
  B) PR-F3のスコープが広がり、Recommendation側コードに（間接的にでも）触れるリスクが増える
  C) 対応が先送りされるが、確定事項1-9との衝突リスクが最も低い
```

---

## 10. Explicit Non-Goals

本監査は以下を一切行っていない:

- no Relevance Rule
- no Relationship
- no Premium Meaning connection
- no Source Evidence Link
- no qualification producer
- no normalized_evidence
- no tag merge
- no alias inference
- no backfill
- no Recommendation changes
- no Ranking changes
- no Concierge changes
- no model change
- no migration
- no DB write
- no admin change
- no canonical key命名・対応表作成
- no ShrineGoriyakuAssignment実装

---

## 11. Verification

- `git status --short`: 監査branch作成直後にclean確認済み（作業はdocs追加のみ）
- `git fetch origin develop` + `git merge --ff-only`: 実施済み、`develop`は最新（`dbe686b1b`）に同期
- 監査branch (`audit/goriyaku-evidence-foundation-refresh`) は最新developから作成
- コード確認はすべてread-only（`grep`/`Read`）。model/migration/admin/Recommendation/Rankingファイルへの変更は一切行っていない
- DB queryはread-only接続試行のみ（`connection.ensure_connection()`）、書き込みは一切行っていない。接続自体が失敗したため、いかなるread queryも実行されていない
- `git diff --check`: 本書追加後に実行予定（コミット前）
