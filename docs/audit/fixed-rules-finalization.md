# KAMI MUSUBI Fixed Rules Finalization

> **Status: `Audit / Historical`**
>
> 本書は`docs/core/fixed-rules.md`の確定過程と、`CURRENT_FIXED` 124件からFixed Ruleへのtraceabilityを記録する監査文書である。
>
> **本書自身はCurrent Source of Truthではない。** 現在有効な横断原則は`docs/core/fixed-rules.md`を参照する。
>
> 本PRはDocs-onlyであり、runtime code、tests、DB、Product / Knowledge / Analytics canonicalのいずれも変更していない。

## 0. 監査条件

| 項目 | 値 |
| --- | --- |
| 対象branch | `develop` |
| Base commit | `fa94f5f`（PR #2848時点） |
| 前提PR | #2833（Phase 2B）/ #2835（Phase 3）/ #2838 / #2846 / #2847（canonical stale alignment） |
| 監査日 | 2026-09-15 |
| 成果物 | `docs/core/fixed-rules.md`（Active）、本書、`docs/core/README.md`更新 |

---

## 1. Phase 1〜3の入力

| Phase | 文書 | 本書への入力 |
| --- | --- | --- |
| Phase 1 | `docs/audit/rule-canonicalization-audit.md` | Current Source of Truth inventory、E章 Rule Candidate 193件（本文・type・source） |
| Phase 2A | `docs/audit/rule-authority-resolution.md` | Authority解決とHOLD対象の特定 |
| Phase 2B | `docs/audit/rule-conflict-resolution.md` | Decision A（Shared Recommendation Eligibility維持）、Decision B（Current Score Authority = v2）、MIXED_CURRENT_DESIREDのsection-scoped判定 |
| Phase 3 | `docs/audit/rule-status-classification.md` | `CURRENT_FIXED` 124 / `CURRENT_VERSIONED` 64 / `UNRESOLVED` 5 の分類、S-1〜S-9 Superseded |

Rule本文はAudit文書のみから生成していない。責務境界に関わるRuleは、現在のowning canonical（`docs/core/README.md`、`docs/core/recommendation-readiness.md`、`docs/knowledge/recommendation-eligibility-contract.md`等、#2838 / #2846 / #2847適用後の状態）へ戻って意味を確認した。

---

## 2. 圧縮方法

### 2.1 原則

1. 同一の禁止理由を持つRule Candidateのみを1つの上位原則へ統合する
2. 異なる禁止理由を1文へ無理に統合しない
3. 特定のfile path、関数名、Field名、Weight、Event property等のversioned detailをFixed Rule本文へ持ち込まない
4. 124件を124条として複製しない

### 2.2 versioned detailの扱い

Rule Candidate本文に含まれていた実装固有の記述は、Fixed Rule本文から除去し、owning canonicalおよび実装・テストへ委譲した。

| Candidate側の記述例 | Fixed Rule本文での扱い |
| --- | --- |
| `localStorage` / `NEXT_PUBLIC_API_BASE` / `.env` 等の具体名 | 「client側のJavaScriptから到達できる領域」「接続先設定」等の抽象表現へ |
| `direction_reference` / `_explanation_payload` / `history_theme` 等のField名 | 「Backendが決定・生成した結果」「監査・品質計測用のpayload」等へ |
| 禁止Analytics属性の具体一覧（緯度経度、駅名、Place ID…） | 「個人または場所を特定しうる情報」等へ抽象化し、具体一覧はAnalytics契約へ委譲 |
| `Wikipedia` / `OSM` / `Wikidata` の固有名 | 「単一の二次source」へ |
| `not_collected` / `unknown` の値名 | 「未着手」「確認済みの情報不足」へ |

### 2.3 件数

| 項目 | 値 |
| --- | --- |
| 入力 `CURRENT_FIXED` | 124 |
| 確定 Fixed Rule | **40** |
| カテゴリ数 | 11 |

目安として提示された20〜35を5件超過している。これは「件数そのものを最適化せず、正確性と責務境界を優先する」という指示に従った結果である。超過の主因は`FR-REC`（7件）と`FR-SEC`（4件）で、いずれも禁止理由が互いに異なるため統合しなかった。

統合を検討したうえで**見送った**主な組み合わせは次のとおり。

| 見送った統合 | 理由 |
| --- | --- |
| `FR-REC-05`（Runtime signal越境）と`FR-REC-06`（単一signal・未検証入力） | 前者は「根拠の捏造」、後者は「判断材料の不足」で禁止理由が異なる |
| `FR-KNOW-03`（未解決の矛盾）と`FR-KNOW-02`（確度・種別の混同） | 前者は未解決conflict固有の扱い、後者は確度grading。`FR-GOV-01`との役割分担も崩れる |
| `FR-SEC-02`（公開境界）と`FR-SEC-03`（secret取扱い） | 前者はaccess control、後者は情報漏洩経路 |
| `FR-ANA-02`（payload最小化）と`FR-ANA-03`（識別誤用） | 前者は送信量、後者は再識別リスク |

---

## 3. 最終Fixed Rule一覧

| カテゴリ | Fixed Rule | 件数 |
| --- | --- | ---: |
| 1. Authority / Source of Truth | `FR-AUTH-01`〜`FR-AUTH-04` | 4 |
| 2. Conflict / Documentation Governance | `FR-GOV-01`〜`FR-GOV-04` | 4 |
| 3. Backend / Frontend Responsibility | `FR-RESP-01`〜`FR-RESP-04` | 4 |
| 4. Safety / Non-assertion / User Autonomy | `FR-SAFE-01`〜`FR-SAFE-04` | 4 |
| 5. Fact / Evidence / Knowledge Integrity | `FR-KNOW-01`〜`FR-KNOW-04` | 4 |
| 6. Recommendation / Meaning / Reason Boundary | `FR-REC-01`〜`FR-REC-07` | 7 |
| 7. Security / Production Safety | `FR-SEC-01`〜`FR-SEC-04` | 4 |
| 8. Analytics Privacy / Interpretation | `FR-ANA-01`〜`FR-ANA-04` | 4 |
| 9. Historical Snapshot / Audit Governance | `FR-HIST-01`, `FR-HIST-02` | 2 |
| 10. Fail-safe / External Dependency Boundary | `FR-FAIL-01` | 1 |
| 11. Fixed Rule Change Procedure | `FR-CHANGE-01`, `FR-CHANGE-02` | 2 |
| **合計** | | **40** |

### 3.1 Fixed Rule別の吸収件数

| Fixed Rule | 吸収数 | `CURRENT_FIXED` Rule ID |
| --- | ---: | --- |
| `FR-AUTH-01` | 1 | `E2-1` |
| `FR-AUTH-02` | 4 | `E2-6`, `E2-7`, `E2-8`, `E9-6` |
| `FR-AUTH-03` | 2 | `E3-12`, `E3-13` |
| `FR-AUTH-04` | 3 | `E4-12`, `E4-13`, `E4-14` |
| `FR-GOV-01` | 4 | `E1-1`, `E1-3`, `E1-4`, `E1-5` |
| `FR-GOV-02` | 3 | `E1-6`, `E1-8`, `E9-2` |
| `FR-GOV-03` | 3 | `E8-6`, `E8-8`, `E8-15` |
| `FR-GOV-04` | 4 | `E8-1`, `E8-2`, `E8-3`, `E8-9` |
| `FR-RESP-01` | 2 | `E3-1`, `E3-2` |
| `FR-RESP-02` | 7 | `E5-34`, `E5-35`, `E5-36`, `E5-38`, `E5-41`, `E5-42`, `E5-43` |
| `FR-RESP-03` | 2 | `E3-20`, `E5-44` |
| `FR-RESP-04` | 1 | `E3-19` |
| `FR-SAFE-01` | 10 | `E5-1`, `E5-2`, `E5-3`, `E5-4`, `E5-6`, `E5-8`, `E5-9`, `E5-10`, `E5-11`, `E5-13` |
| `FR-SAFE-02` | 2 | `E5-5`, `E5-7` |
| `FR-SAFE-03` | 3 | `E5-12`, `E5-14`, `E5-15` |
| `FR-SAFE-04` | 2 | `E5-16`, `E5-40` |
| `FR-KNOW-01` | 6 | `E5-17`, `E5-23`, `E5-27`, `E5-28`, `E5-29`, `E5-31` |
| `FR-KNOW-02` | 5 | `E4-16`, `E4-17`, `E4-18`, `E5-25`, `E5-26` |
| `FR-KNOW-03` | 1 | `E5-24` |
| `FR-KNOW-04` | 2 | `E5-32`, `E5-33` |
| `FR-REC-01` | 6 | `E3-3`, `E3-4`, `E3-5`, `E3-6`, `E3-7`, `E3-8` |
| `FR-REC-02` | 2 | `E4-15`, `E4-19` |
| `FR-REC-03` | 3 | `E4-10`, `E4-11`, `E5-39` |
| `FR-REC-04` | 3 | `E4-1`, `E4-2`, `E4-3` |
| `FR-REC-05` | 6 | `E5-18`, `E5-19`, `E5-20`, `E5-21`, `E5-22`, `E9-4` |
| `FR-REC-06` | 4 | `E5-30`, `E5-37`, `E5-50`, `E5-51` |
| `FR-REC-07` | 3 | `E5-45`, `E5-46`, `E8-11` |
| `FR-SEC-01` | 3 | `E5-52`, `E5-53`, `E5-54` |
| `FR-SEC-02` | 3 | `E5-55`, `E5-56`, `E5-57` |
| `FR-SEC-03` | 4 | `E5-58`, `E5-59`, `E5-60`, `E5-61` |
| `FR-SEC-04` | 1 | `E5-64` |
| `FR-ANA-01` | 4 | `E5-65`, `E5-66`, `E5-71`, `E5-73` |
| `FR-ANA-02` | 3 | `E5-67`, `E5-68`, `E8-12` |
| `FR-ANA-03` | 2 | `E5-69`, `E5-70` |
| `FR-ANA-04` | 4 | `E4-20`, `E4-21`, `E4-22`, `E5-72` |
| `FR-HIST-01` | 2 | `E8-14`, `E4-24` |
| `FR-HIST-02` | 2 | `E8-7`, `E8-13` |
| `FR-FAIL-01` | 2 | `E6-13`, `E6-14` |
| `FR-CHANGE-01` | 0 | —（新設。Phase 3 §8のRule変更手順および本タスク指示に基づく） |
| `FR-CHANGE-02` | 0 | —（新設。Phase 3 §8のRule変更手順および本タスク指示に基づく） |

`FR-CHANGE-01` / `FR-CHANGE-02`はPhase 1 E章のRule Candidateを吸収していない。これらは`docs/audit/rule-status-classification.md` §8「Why `CURRENT_FIXED` Does Not Mean Immutable Forever」が示す変更手順を、Fixed Rule本体の運用契約として明文化したものである。124件のcoverage計算には含めない。

---

## 4. 124 `CURRENT_FIXED` traceability

1候補につきprimary mappingを1つだけ決めている。二重カウントはない。

| `CURRENT_FIXED` ID | Rule Candidate（Phase 1 E章。要約） | Primary Fixed Rule |
| --- | --- | --- |
| `E1-1` | 文書、実装およびテストが食い違う場合、いずれか一つを自動的に正しいものとして扱わず、意図した仕様を確認する | `FR-GOV-01` |
| `E1-3` | 情報源が矛盾する場合、黙って一方を採用しない | `FR-GOV-01` |
| `E1-4` | 矛盾するSourceを削除せず保持する（片方を消して整合性があるように見せない） | `FR-GOV-01` |
| `E1-5` | 異なる用途の住所を「新旧」「正誤」と推測で統合しない。説明不能な競合は推測で解消しない | `FR-GOV-01` |
| `E1-6` | 下流文書だけを更新し、上流仕様または共通用語と矛盾する変更は禁止する | `FR-GOV-02` |
| `E1-8` | `mobile-user-flow.md`と監査文書の記載が食い違う場合、より新しい実装・テストの確認結果を優先する | `FR-GOV-02` |
| `E2-1` | Core文書は目的・責務・境界・入出力の意味・禁止事項・委譲関係・互換方針・更新条件を管理する。実装とテストはEndpoint / Route / Fie… | `FR-AUTH-01` |
| `E2-6` | 方位計算と表示契約の正本はBackendとする | `FR-AUTH-02` |
| `E2-7` | Consultation Interpretation Engineの正本はbackend実装とする | `FR-AUTH-02` |
| `E2-8` | Recommendation Reasonの意味生成正本はBackendとする | `FR-AUTH-02` |
| `E3-1` | Frontendは認証状態と認証要求時のUIを担当する。Tokenの保持・更新・Backendへの付与はBFFの責務。認証・権限・所有者・課金状態の最終判… | `FR-RESP-01` |
| `E3-2` | WebとMobileのToken保存方式を同一視しない | `FR-RESP-01` |
| `E3-3` | Meaning Layerは表示コピーを直接生成せず、推薦順位を直接決定せず、永続データを保持しない | `FR-REC-01` |
| `E3-4` | Meaning Translationは推薦の意味づけを担う補助レイヤーであり、推薦順位・Scoreを単独で決定しない | `FR-REC-01` |
| `E3-5` | Action Suggestionは行動レイヤーであり、神社の選定・推薦順位・推薦理由そのものを決定しない。推薦理由を再生成しない | `FR-REC-01` |
| `E3-6` | Consultation Interpreter自体は推薦コピーを生成しない | `FR-REC-01` |
| `E3-7` | Recommendation Readinessの責務はGovernance観測のみ。Candidate generation / Candidate e… | `FR-REC-01` |
| `E3-8` | Recommendation ReadinessとEvidence Gateは別責務であり混同しない。Readiness側でEvidence Gateのv… | `FR-REC-01` |
| `E3-12` | Knowledge Baseはデータ品質・文章品質・生成原則を管理し、Core・Productの実装契約を重複定義しない。正本文書とReference文書… | `FR-AUTH-03` |
| `E3-13` | Coreはシステム全体構造・横断技術責務・品質基準・接続契約・生成原則を管理し、画面/体験はProduct、神社データ/意味定義/コピーはKnowledg… | `FR-AUTH-03` |
| `E3-19` | 検索（Explore）・コンシェルジュ・地図・人気ランキングの責務を混同しない | `FR-RESP-04` |
| `E3-20` | ComponentはSemantic Tokenを参照し、Primitive Tokenを直接参照しない（例外はコード上に理由を残す） | `FR-RESP-03` |
| `E4-1` | ConciergeとCompassは別の製品体験である。共有基盤は共有製品責務を意味しない | `FR-REC-04` |
| `E4-2` | Compassの価値を作るために、Conciergeの挙動・Ranking・API契約・UX責務を再設計または弱めてはならない。Existing Conc… | `FR-REC-04` |
| `E4-3` | Concierge内での方位前面化制約はRESTRICTED（不変）。Direction Audit完了はConcierge内での方位前面化を自動的に許可… | `FR-REC-04` |
| `E4-10` | 保存済みの推薦結果は、神社情報・評価ロジック・ユーザー行動状態が後から変化しても暗黙に再計算または再ランキングしない | `FR-REC-03` |
| `E4-11` | 現在のFavorite / Visit / Reflectionは現在状態として管理し、過去の推薦結果と同一視しない | `FR-REC-03` |
| `E4-12` | local `jinja_db`の現在状態そのものをcanonical source of truthとはしない（Database Is Not the … | `FR-AUTH-04` |
| `E4-13` | 開発に使用する唯一のlocal Repositoryを固定する。別cloneをactive development sourceとして使用しない | `FR-AUTH-04` |
| `E4-14` | feature / audit / chore / docs branchは作業単位の一時branchであり、merge後の長期的なsource of t… | `FR-AUTH-04` |
| `E4-15` | Fact（事実）とInterpretation（意味文脈）は責務が別であり、どちらか一方だけでは他方を代替しない | `FR-REC-02` |
| `E4-16` | `history_type="tradition"`であることは「記述内容が史実として確定している」ことを意味しない | `FR-KNOW-02` |
| `E4-17` | `not_collected`と`unknown`を同一視しない。前者は運用上の未着手、後者は確認済みの情報不足である | `FR-KNOW-02` |
| `E4-18` | 概念項目と物理フィールドを同一視しない | `FR-KNOW-02` |
| `E4-19` | RecommendationはMeaningを前提とし、ActionはRecommendationを前提とし、ReflectionはActionを前提とす… | `FR-REC-02` |
| `E4-20` | Eventが存在しないことを、その行動が発生しなかったことの証拠として扱わない | `FR-ANA-04` |
| `E4-21` | 相関は因果を意味しない。あるEventの後に別のEventが多く発生していることは、前者が後者の原因であることを意味しない | `FR-ANA-04` |
| `E4-22` | 同一の神社であっても、異なる相談文脈または異なるセッションから発生した行動は同一の意思決定として扱わない | `FR-ANA-04` |
| `E4-24` | 延期（Deferred）は削除を意味しない | `FR-HIST-01` |
| `E5-1` | 心理状態、性格、運命を断定しない | `FR-SAFE-01` |
| `E5-2` | AIはユーザーの人生を診断せず、運勢・未来・霊的意味を断定しない。AIによる断定・診断・宗教的保証を目的としない | `FR-SAFE-01` |
| `E5-3` | 「吉方位なので行くべき」「必ず良い結果になる」「運気が上がる」「願いが叶う」と断定しない | `FR-SAFE-01` |
| `E5-4` | Factに心理診断を書く／Interpretationに神社の未確認事実を書く／Actionに宗教的効果保証を書くことを禁止する | `FR-SAFE-01` |
| `E5-5` | `history_type="tradition"`のFactを、confidenceに関わらず断定表現（assertive）で出してはならない | `FR-SAFE-02` |
| `E5-6` | 決定論的な未来予測・結果保証をしてはならない | `FR-SAFE-01` |
| `E5-7` | 日次精度を含意してはならない（「今日の吉方位」等） | `FR-SAFE-02` |
| `E5-8` | 神社の由緒やご利益を、未来の結果やユーザーの心理状態を保証する根拠として利用しない | `FR-SAFE-01` |
| `E5-9` | `history_theme`をユーザーの性格・心理状態・将来を断定するために使用しない。`history_theme`だけでユーザーの状態を判定しない | `FR-SAFE-01` |
| `E5-10` | 医療、心理、宗教または人生上の結果を判定しない。心理診断として扱わない | `FR-SAFE-01` |
| `E5-11` | AIは過去のReflectionだけを根拠にユーザーの状態・性格・将来を断定しない | `FR-SAFE-01` |
| `E5-12` | Reflectionでは感情を評価しない。回答を誘導せず、正解や望ましい感情を設定しない。他人との比較は行わない | `FR-SAFE-03` |
| `E5-13` | 神社詳細であっても宗教的・心理的に断定しない | `FR-SAFE-01` |
| `E5-14` | 参拝作法や宗教的実践を唯一の正解として強制しない。危険または禁止されている行動を提案しない | `FR-SAFE-03` |
| `E5-15` | 行動しない選択を異常として扱わない | `FR-SAFE-03` |
| `E5-16` | Readiness / Coverageを「神社の信頼度」「神社の格」としてユーザーへ直接表示しない。断定的な優劣表現は避ける | `FR-SAFE-04` |
| `E5-17` | 保存済み根拠がなければFactとして主張しない | `FR-KNOW-01` |
| `E5-18` | 神社の根拠を占術から捏造してはならない。方位の根拠は神社の根拠を代替できない | `FR-REC-05` |
| `E5-19` | Runtime signal（方位・占術）がShrine Knowledgeを新設・上書きしてはならない | `FR-REC-05` |
| `E5-20` | 未使用のsignalをrecommendation evidenceとして提示してはならない。データが存在するというだけの理由で占術・九星気学・方位・ご利… | `FR-REC-05` |
| `E5-21` | 方位単独で最終的な神社を決定してはならない。神社の決定は常にRecommendation Authority + Shrine Knowledge Aut… | `FR-REC-05` |
| `E5-22` | 方位一致をRecommendation Reasonの主理由として表示しない。`direction_reference`・方位一致状態・方角・方位加点をR… | `FR-REC-05` |
| `E5-23` | AI生成だけで事実項目を確定しない。AI生成のみの祭神情報を`verification_status: source_confirmed`以上として保存し… | `FR-KNOW-01` |
| `E5-24` | 情報が`disputed`（矛盾未解決）の場合は断定利用しない | `FR-KNOW-03` |
| `E5-25` | 公式情報であっても、由緒に含まれる伝承的記述を歴史的確定事実として扱わない | `FR-KNOW-02` |
| `E5-26` | ご利益タグ（`goriyaku_tags`）を歴史的事実の代替として扱わない。`history_theme`を由緒そのものとして扱わない | `FR-KNOW-02` |
| `E5-27` | Actionの根拠として、実在しない施設・文化財・由緒書・境内設備を使用しない。存在が確認できない場所を案内しない | `FR-KNOW-01` |
| `E5-28` | 神社固有の理由が存在しないActionは禁止 | `FR-KNOW-01` |
| `E5-29` | Wikipediaのみを唯一の根拠としない。OSM / Wikidataを唯一のprimary sourceにしない | `FR-KNOW-01` |
| `E5-30` | ご利益タグだけで推薦理由を完結させない。`theme_key`・ご利益・誕生日・占術・方位だけで推薦結果を決定しない | `FR-REC-06` |
| `E5-31` | 根拠のない文化解釈を保存しない。Derived情報を一次情報として扱わない | `FR-KNOW-01` |
| `E5-32` | HOLD状態では座標を推測してSeed / Productionへ投入しない。既存座標を惰性で維持しない。current candidateを距離だけで自… | `FR-KNOW-04` |
| `E5-33` | 法人登記住所をVisitor / Navigation Anchorの採用根拠として単独では使用しない | `FR-KNOW-04` |
| `E5-34` | frontend / mobileに判定ロジックを重複実装しない | `FR-RESP-02` |
| `E5-35` | FrontendおよびMobileは、Backendが返す観測用Scoreを独自に順位へ反映しない | `FR-RESP-02` |
| `E5-36` | Web / mobileは`direction_reference`を再計算しない。クライアントは方位を再計算・補完しない | `FR-RESP-02` |
| `E5-37` | raw_queryを直接スコア加点しない。LLM出力でユーザーの原文を上書きしない | `FR-REC-06` |
| `E5-38` | Frontendを意味生成の正本にしない。FrontendはRecommendation Reasonの意味を独自に再解釈しない | `FR-RESP-02` |
| `E5-39` | `_explanation_payload`とRecommendation Reasonを同一視しない。Snapshotを後から暗黙に再計算しない | `FR-REC-03` |
| `E5-40` | 内部タグをそのまま表示しない。内部変数名やフォールバック文言を表示しない | `FR-SAFE-04` |
| `E5-41` | FrontendでVisit / Reflection / Action生成 / 相談解釈の業務判定を重複実装しない | `FR-RESP-02` |
| `E5-42` | Home HeroやConcierge Entryで相談テーマ一覧や内部キー対応を独自に重複管理しない。Frontend / Backend / Anal… | `FR-RESP-02` |
| `E5-43` | Premium優先・Free制限・未確定時の判定ロジックを画面ごとに重複実装しない。共通実装へ集約する | `FR-RESP-02` |
| `E5-44` | 画面からPostHog SDK等を直接呼ばず、必ずhelper経由でEventを送信する。Event名と固定`source`/`platform`を画面コ… | `FR-RESP-03` |
| `E5-45` | Recommendation ScoreへLLMへ全候補を無条件に渡す設計を正本にしない | `FR-REC-07` |
| `E5-46` | Candidate生成段階で最終順位を決定しない（広め取得と最終順位付けを分離する）。入力保持段階でスコア加点や推薦順位への影響を発生させない | `FR-REC-07` |
| `E5-50` | 投稿者入力は直接推薦ロジックに入れず、必ずadmin確認を経由する | `FR-REC-06` |
| `E5-51` | Runtime情報を神社プロフィールへ固定情報として保存しない。Runtime情報を神社固定情報として扱わない | `FR-REC-06` |
| `E5-52` | Access Token・Refresh TokenはHttpOnly Cookieで管理し、`localStorage`等のJS到達可能な領域へ保存しな… | `FR-SEC-01` |
| `E5-53` | FrontendからBackendへ認証付き通信を直接行わない。Frontend Route内でBackend URLを直接組み立てない。Frontend… | `FR-SEC-01` |
| `E5-54` | 認証付きRouteで`NEXT_PUBLIC_API_BASE`や`API_BASE_URL`を直接参照しない。FrontendにJWT発行Routeを複… | `FR-SEC-01` |
| `E5-55` | 課金状態や権限をFrontendだけで確定しない。Frontend側の未確定状態を理由にBackendの利用制限を回避できる設計にはしない | `FR-SEC-02` |
| `E5-56` | staff/admin操作（Django Admin、superuser作成等）を認証・権限チェックを経ない匿名HTTPエンドポイントとして公開しない。B… | `FR-SEC-02` |
| `E5-57` | DB接続情報・ファイルシステムpath・migration状態・生exceptionなど内部stateを返すdebug endpointを、認証・権限チェ… | `FR-SEC-02` |
| `E5-58` | 指定情報はDebug/Info/Error/Warningいずれのlevelであってもproduction runtimeのログへ出力してはならない | `FR-SEC-03` |
| `E5-59` | `.env`はGitへコミットしない。APIキーは環境変数で管理し、ソースコードへ直接記述しない | `FR-SEC-03` |
| `E5-60` | private / authentication stateを含むbackupをRepositoryへcommitしない | `FR-SEC-03` |
| `E5-61` | Production databaseをlocal development databaseとして使用しない。Production `DATABASE_U… | `FR-SEC-03` |
| `E5-64` | 外部API（LLM等）の実コールはテストで禁止（コスト事故防止）。E2Eは実Backend、外部ジオコードAPI、本番データへ接続しない | `FR-SEC-04` |
| `E5-65` | 禁止属性はEvent名を問わず送信しない（緯度経度、住所、駅名、都道府県名、神社名・住所、Place ID、経路URL、生年月日、予定日、相談文、推薦理由… | `FR-ANA-01` |
| `E5-66` | 同種の禁止Payload規定をMobile Search / Mobile Reflection / Consultation History各契約でも適… | `FR-ANA-01` |
| `E5-67` | 禁止属性が1件でも見つかれば即時停止・調査とする | `FR-ANA-02` |
| `E5-68` | 品質検証用キーを本番イベントへ追加しない。品質判定のために本番payload・イベント名・ユーザー識別子を増やさない | `FR-ANA-02` |
| `E5-69` | 少数データから個人を推測しない。少数セルは非表示または期間を延長する。Person property・住所系プロパティ・個別ユーザーcohortを作成しない | `FR-ANA-03` |
| `E5-70` | WebのsessionIdを相談threadIdの代用として使用しない | `FR-ANA-03` |
| `E5-71` | ConciergeのURLクエリ（`theme`/`q`）へReflection由来の本文を渡さない（自由入力本文がURLへ含まれるため） | `FR-ANA-01` |
| `E5-72` | Analyticsは体験改善の観測に利用し、個別ユーザーの心理状態・宗教的効果・信仰の程度・人生上の成果を判定するためには利用しない | `FR-ANA-04` |
| `E5-73` | 方位ログ境界で座標・住所・駅名・都道府県名・神社情報・生年月日・参拝日・相談文・推薦理由・例外メッセージ・イベントpayloadを記録しない（例外本文も記… | `FR-ANA-01` |
| `E6-13` | Billing状態が未取得またはエラーの場合、FrontendはPremiumユーザーを誤ってPaywall表示で遮断しない | `FR-FAIL-01` |
| `E6-14` | 地図が利用できない状態でも主要フローを完遂できることを必須条件とする | `FR-FAIL-01` |
| `E8-1` | Core文書を追加・削除または分類変更した場合は`docs/core/README.md`を同じPRで更新する。Active / Reference分類は… | `FR-GOV-04` |
| `E8-2` | 正本を追加・削除した場合は`docs/product/README.md`の「読む順番」と「正本」を同じPRで更新する。分類変更時は`product-do… | `FR-GOV-04` |
| `E8-3` | Event名またはPayloadを変更する場合は、実装と契約文書を同じPRで更新する。分類変更時は対象文書のStatusヘッダと`docs/analyti… | `FR-GOV-04` |
| `E8-6` | Reference文書の未実装案を、実装済み仕様として扱わない | `FR-GOV-03` |
| `E8-7` | Audit文書に記載された時点判断やTODOを現行契約として扱わない | `FR-HIST-02` |
| `E8-8` | Archive文書は履歴保存を目的とし、現行の仕様・計測契約判断には使用しない | `FR-GOV-03` |
| `E8-9` | 詳細仕様、TODO、実装履歴、監査結果およびPR情報を各READMEへ記載しない | `FR-GOV-04` |
| `E8-11` | 新しいScoreは既存順位へ直ちに反映せず、差分・寄与・行動データとの関係を観測した上で適用可否を判断する | `FR-REC-07` |
| `E8-12` | Analytics Eventの追加より既存属性による集計を優先する。追加が必要な場合は目的・発火箇所・重複単位・保持期間・禁止属性検査・Web／モバイル… | `FR-ANA-02` |
| `E8-13` | `docs/audit/README.md`は audit文書の内容・Status・削除・移動を管理しない。新しいaudit chainを索引化する場合は… | `FR-HIST-02` |
| `E8-14` | 古い数値（Coverage件数、shrine件数等）はHistorical Snapshotとしてそのまま残りうる。現在値へ無断更新しない | `FR-HIST-01` |
| `E8-15` | Statusなしは「未分類」を意味するに留まり、Statusなし＝古い/Superseded/Archiveと断定しない | `FR-GOV-03` |
| `E9-2` | 現在仕様を知る際は Current Source of Truth → Final/latest audit → Intermediate audit →… | `FR-GOV-02` |
| `E9-4` | element / birthdate / directionはprimary_reasonを上書きしない | `FR-REC-05` |
| `E9-6` | Backend生成値が利用可能な場合、Frontendはそれを優先する | `FR-AUTH-02` |

---

## 5. Coverage Gate結果

機械的に検証した。検証スクリプトはmapping定義とPhase 3の`CURRENT_FIXED`リストを突き合わせるものである。

```text
SOURCE_FIXED_COUNT = 124
MAPPED_FIXED_COUNT = 124
UNMAPPED           = 0
UNKNOWN_RULE_ID    = 0
DUPLICATE(primary) = 0
FIXED_RULE_COUNT   = 40
```

`SOURCE_FIXED_COUNT`はPhase 3 §4が列挙するID範囲から再構成した。

| Phase 3 の分類 | 列挙 | 再構成件数 |
| --- | --- | ---: |
| E1 Conflict Rule | `E1-1`, `E1-3`, `E1-4`, `E1-5`, `E1-6`, `E1-8` | 6 |
| E2 Source of Truth | `E2-1`, `E2-6`, `E2-7`, `E2-8` | 4 |
| E3 Responsibility Boundary | `E3-1`〜`E3-8`, `E3-12`, `E3-13`, `E3-19`, `E3-20` | 12 |
| E4 Invariant | `E4-1`, `E4-2`, `E4-3`, `E4-10`〜`E4-22`, `E4-24` | 17 |
| E5 Prohibition / MUST NOT | `E5-1`〜`E5-46`, `E5-50`〜`E5-61`, `E5-64`〜`E5-73` | 68 |
| E6 Fail-safe | `E6-13`, `E6-14` | 2 |
| E8 Update Rule | `E8-1`, `E8-2`, `E8-3`, `E8-6`〜`E8-9`, `E8-11`〜`E8-15` | 12 |
| E9 Precedence | `E9-2`, `E9-4`, `E9-6` | 3 |
| **合計** | | **124** |

---

## 6. Fixed Rule間の意味重複確認

40件について、他Fixed Ruleと意味上重複していないことを確認した。境界が近接するものは次のとおり整理している。

| 近接する組 | 境界 |
| --- | --- |
| `FR-AUTH-02`（Backend authority）/ `FR-RESP-02`（client再計算禁止） | 前者は「どこが決めるか」、後者は「clientが何をしてはならないか」 |
| `FR-GOV-01`（conflict解決禁止）/ `FR-CHANGE-02`（Rule衝突時STOP） | 前者は一般的なconflict、後者はFixed Rule固有の停止義務 |
| `FR-SAFE-01`（断定禁止）/ `FR-KNOW-01`（Evidence要件） | 前者は出力表現、後者は保存・確定する事実の要件 |
| `FR-SAFE-02`（確度超過表現）/ `FR-KNOW-02`（確度混同） | 前者は表現強度、後者はデータ分類の同一視 |
| `FR-REC-01`（レイヤー責務）/ `FR-REC-02`（依存順序） | 前者は越境禁止、後者は概念の前提関係と非代替性 |
| `FR-ANA-01`（送信禁止）/ `FR-ANA-03`（識別誤用） | 前者は送らない、後者は送った後の推論・代用 |
| `FR-HIST-01`（Snapshot不変）/ `FR-REC-03`（Runtime Snapshot不変） | 前者は文書上の時点記録、後者は保存済み推薦結果 |

---

## 7. Versioned / Unresolved / Superseded 境界

### 7.1 `CURRENT_VERSIONED` 64件をFixedへ誤昇格していない

`CURRENT_VERSIONED` 64件は本書のmappingに一切含まれていない。`docs/core/fixed-rules.md`にも列挙していない。

各owning canonical contractがCurrent authorityであり、専用Feature / Contract PRでcanonical + implementation + testsを同期して変更する。この扱いは`fixed-rules.md` §Fixed / Versioned / Unresolved / Supersededで明記した。

### 7.2 `UNRESOLVED` 5件をCurrentへ誤昇格していない

| ID | 内容 | 本PRでの扱い |
| --- | --- | --- |
| `E2-5` | API schema関連ファイルの正本未確定 | Fixed / Versionedいずれへも昇格させていない |
| `E4-23` | Concierge Input Levelの用語衝突 | 同上 |
| `E5-62` | Production DBへの直接DELETE禁止（Guest data retention側のAuthority未確定） | 同上 |
| `E5-63` | 認証済みrow削除禁止（同上） | 同上 |
| `E9-7` | Concierge Input LevelのPrecedence | 同上 |

`E5-62` / `E5-63`はSecurity的に重要な内容を含むが、owning canonicalのAuthority（`docs/ops/guest-data-retention.md`がDomain READMEを持たない）が未解決であるため、推測でFixed化しない。`FR-SEC-03`はProduction接続情報の取り扱い境界を扱うが、`E5-62` / `E5-63`が扱うdeletion手順そのものは含めていない。

Authority解消は本PRのScope外とする。

### 7.3 S-1〜S-9 Supersededを復活させていない

S-1〜S-9（旧Runtime Readiness Level 0〜3を含む）は`fixed-rules.md`に一切出現しない。

`fixed-rules.md`内に`Readiness Level`、`Level 0`〜`Level 3`という語は存在しない。Governance観測とRuntime判定の責務分離は`FR-REC-01`が抽象レベルで固定しており、ordinal Levelを再導入していない。

---

## 8. Scope外（本PRへ混ぜていないもの）

| 項目 | 状態 |
| --- | --- |
| `shrine-data-guide.md`のInput GuidanceとShared Eligibilityの関係整理 | follow-up候補 |
| Roadmap内の`SCORE_V3_MODE` / `resolve_score_sort_key()`という実装シンボル依存cleanup | follow-up候補 |
| Concierge Input orphan authority解消（`E4-23` / `E9-7`） | UNRESOLVED |
| Guest data retention authority解消（`E5-62` / `E5-63`） | UNRESOLVED |
| Score / Ranking変更、Eligibility条件変更、runtime変更 | 変更なし |

### Production `SCORE_V3_MODE`

Productionの`SCORE_V3_MODE`実値が未確認であることは、Fixed Rule Candidate 124件とは別のoperational unresolved stateである。

- 193 Rule Candidateの分類件数へ加算していない
- `fixed-rules.md`本文にProduction実値を断定して記載していない
- Current Score Authorityの扱いは既存canonical（`docs/analytics/recommendation-score-v2-current-design.md`、`docs/core/roadmap.md`、`docs/audit/rule-conflict-resolution.md` Decision B）へ委譲している

---

## 9. 本PRで変更した文書

| path | 変更 |
| --- | --- |
| `docs/core/fixed-rules.md` | 新規（Status: Active） |
| `docs/audit/fixed-rules-finalization.md` | 新規（本書。Status: Audit / Historical） |
| `docs/core/README.md` | `fixed-rules.md`をActive Coreとして登録、読む順番へ追加 |

runtime code、tests、DB、Migration、Product / Knowledge / Analytics canonicalは変更していない。

---

## 関連ドキュメント

- `docs/core/fixed-rules.md`（Current Source of Truth）
- `docs/core/README.md`
- `docs/audit/rule-canonicalization-audit.md`
- `docs/audit/rule-authority-resolution.md`
- `docs/audit/rule-conflict-resolution.md`
- `docs/audit/rule-status-classification.md`
