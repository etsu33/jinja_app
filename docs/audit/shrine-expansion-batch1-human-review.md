> **Status: `HUMAN_REVIEW_CLOSURE_HOKKAIDO_JINGU_TAKEBE_TAISHA_NAMINOUEGU_COMPLETE`。**
>
> 本監査はHuman Reviewの結果記録のみ。Production DBへの書き込み、Production
> Seed/Knowledge Seedへの追加、Model/Migration/Evidence Gate/Recommendation/
> Source Contract/Knowledge Contractの変更は一切行っていない。
>
> **要旨**: `docs/audit/shrine-knowledge-fact-generation-pilot.md`（PR #2533）
> がscratch DB上で構造検証済みの北海道神宮・建部大社・波上宮のFact Candidateに
> ついてHuman Reviewを実施・記録した。北海道神宮はH1（`tradition`→`founding`）の
> 1件revisionでPASS。建部大社はD1・D2・H1・H3が既存Source・既存Contractと一致し
> PASS、H2は675年説（建部大社公式「見どころ」）と676年説（日本遺産ポータル）と
> いう同一粒度の具体年競合が確認済みSourceから解消不能なため、既存Disputed
> Evidence Contractに従い`history_type: tradition` / `verification_status:
> disputed`のMultiple Fact（H2-A・H2-B）へ分離した。**波上宮はHuman Review時点で
> 取得可能な公式Source本文と既存Knowledge ContractからHuman Review Candidateを
> 再構成した結果、Deity 6 / History 6 / Total 12となり、全FactがPASS、
> disputedは0件だった。旧Pilot Candidate本文はscratch Seedにのみ存在し
> repositoryへ保存されていなかったため、1対1の差分比較はできない。** 3社とも
> Human Review Closure完了。Production Importは別タスク。

# Shrine Expansion Batch 1 — Human Review Closure

## 1. Scope

- Human Reviewの結果を正確にrepoへ記録することのみを目的とする
- Production Import・Production Seed追加・Coverage更新・Recommendation変更・
  Evidence Gate変更は行わない
- 新しいKnowledge Model・Migration・Schema・Pipelineは作らない
- 北海道神宮・建部大社・波上宮の3社すべてでHuman Reviewを完了した
  （波上宮は本文書の後続版で追加。§5参照）

## 作業ブランチ / worktree（Phase 0）

北海道神宮・建部大社分（初版）:

| 項目 | 結果 |
|---|---|
| メインworking tree | 変更なし（別タスクが`docs/shrine-geographic-expansion-rollout-plan`branch上で進行中、touchしていない） |
| `origin develop`最新化 | `git fetch origin`実行、`origin/develop` SHA=`a92ced698477eb35b2af54c77e32752005964397`（`feat: Compass候補に段階的な距離境界を追加 (#2535)`）を記録 |
| `audit/shrine-expansion-batch1-human-review`branch/worktree衝突 | なし（`git branch -a`・`ls ../`で事前確認、衝突0件） |
| worktree作成 | `git worktree add ../jinja_app-shrine-human-review audit/shrine-expansion-batch1-human-review`（`origin/develop`起点で新規branch作成後） |
| worktree内working tree | clean（作成直後に確認） |
| `feature/compass-geographic-distance-boundary`への変更 | なし（当該branchは既にdevelopへmerge済み（PR #2535）であることを`git log origin/develop`で確認したのみで、branch/worktree自体には一切触れていない） |

波上宮分（本改訂）:

| 項目 | 結果 |
|---|---|
| メインworking tree | 変更なし（`docs/shrine-geographic-expansion-rollout-plan`branch、touchしていない） |
| 既存`audit/shrine-expansion-batch1-human-review`worktree | 変更なし（`../jinja_app-shrine-human-review`、PR #2536としてmerge済み。touchしていない） |
| `origin/develop`最新化 | `git fetch origin`実行、`origin/develop` SHA=`aa447fc5f01c7388959904c103eb485143a3a25e`（`docs: Compass Purpose Sensitivity監査を追加 (#2537)`）を記録 |
| `audit/shrine-expansion-batch1-naminoue-human-review`branch/worktree衝突 | なし |
| worktree作成 | `git worktree add ../jinja_app-naminoue-human-review audit/shrine-expansion-batch1-naminoue-human-review`（`origin/develop`起点で新規branch作成後） |
| worktree内working tree | clean（作成直後に確認） |
| Compass branch/worktreeへの変更 | 0（一切touchしていない） |

STOP条件（branch/worktree衝突、origin/develop以外を基点、Compass branchへの
変更が必要、unrelated working tree変更の発見）はいずれも該当しなかった。

## 2. Source Set

### 北海道神宮

| Source | Publisher | source_type | 備考 |
|---|---|---|---|
| 由緒（`hokkaido-jingu-official-history`） | 北海道神宮 | shrine_official | `shrine-knowledge-fact-generation-pilot.md`でSource確認・validate-only/dry-run PASS済み |

### 建部大社

| Source | Publisher | source_type | 備考 |
|---|---|---|---|
| Source A: 建部大社について（既存key `takebe-taisha-official-about`） | 建部大社 | shrine_official | Pilotで確認済み。天武天皇の時代に瀬田へ移った趣旨 |
| Source B: 見どころ（新規、本Human Reviewで初めて登場） | 建部大社 | shrine_official | **URL未指定**——本Human Review入力に記載がなく、推測で補完していない。白鳳4年（675年）に瀬田へ遷し祀られた趣旨。Production Seed化前に別途URL確認が必要（§9 Unresolved参照） |
| Source C: 日本遺産ポータル「建部大社」（既存key `takebe-taisha-japan-heritage`） | 日本遺産ポータルサイト | government | Pilotで確認済み。天武天皇4年（676年）に現在地へ移されたと「伝わる」と明記 |

### 波上宮

| Source | Publisher | source_type | URL | 備考 |
|---|---|---|---|---|
| 波上宮公式「由緒」 | 波上宮 | shrine_official | https://naminouegu.jp/yuisyo.html | Fact Generation Pilot時点で確認済み（`naminoue-gu-official-history`）。創始年不詳・御鎮座伝説・琉球王府期の信仰・明治23年の列格・戦後再建・御祭神を本文で直接確認済みとPilot時点の`note`に記載 |

## 3. 北海道神宮 Review

Human Review済みの判断を再解釈せず、そのまま記録する。

### Deity（4件、PASS）

| display_name | role | verification_status | confidence | Review |
|---|---|---|---|---|
| 大国魂神 | unknown | source_confirmed | high | PASS |
| 大那牟遅神 | unknown | source_confirmed | high | PASS |
| 少彦名神 | unknown | source_confirmed | high | PASS |
| 明治天皇 | unknown | source_confirmed | high | PASS |

神社庁Sourceと直接一致。roleはSourceに明示的な序列がないため既存Contract
（`ROLE_CHOICES`、序列不明時は`unknown`）どおり`unknown`を維持する。

### History（3件、うち1件Revision）

| ID | 旧`history_type` | 新`history_type` | 内容 | Review |
|---|---|---|---|---|
| H1 | `tradition` | **`founding`** | 明治2年の北海道鎮座神祭を創祀とする由緒 | **REVISED** |
| H2 | `historical_event` | （変更なし） | 明治4年の札幌神社への社名決定と円山遷座 | PASS |
| H3 | `historical_event` | （変更なし） | 昭和39年の明治天皇増祀と北海道神宮への改称 | PASS |

**H1 Revision理由**: `docs/knowledge/shrine-knowledge-contract.md`「history_type
一覧」節が`founding`を「創建・鎮座に関する情報（確定年・推定年代・不詳を区別）」
と定義しており、北海道鎮座神祭は鎮座・創祀そのものを扱う内容のため`tradition`
より`founding`がContractに整合する。本監査でこの定義箇所を`docs/knowledge/
shrine-knowledge-contract.md`（現行develop上に存在、行303-304）から直接確認し、
Human Reviewの判断根拠がContractと一致することを検証した。Sourceに存在しない
「北海道神宮はこれを創祀としている」等の追加表現は、この確認過程で削除対象として
扱われている（Fact Candidateの`content`には現状Source本文相当の記述のみが残る）。

**Contract上の副次的影響（記録のみ、判断・変更はしない）**: `docs/knowledge/
shrine-knowledge-contract.md`「Recommendation Reason側での強制
（TRADITION_ALWAYS_HEDGED）」節は、`history_type="tradition"`のFactに対しては
confidenceに関わらずhedge表現を強制するが、この強制は`tradition`分類にのみ
適用される。H1が`founding`へ変更されたことで、この自動hedge強制の対象外となる
（confidence=highのまま、hedge表現の強制メカニズムが変わる）。これはH1
Revisionの直接的な帰結として記録するに留め、本監査ではReason生成側の挙動を
検証・変更していない。

**北海道神宮 Review Result: `PASS WITH 1 REVISION`**

## 4. 建部大社 Review

### 4.1 D1・D2（Human Review、Phase 5）

| ID | Fact | Source | role | verification_status | confidence | Review |
|---|---|---|---|---|---|---|
| D1 | 日本武尊 | Source A, Source C | unknown | source_confirmed | high | **PASS** |
| D2 | 大己貴命 | Source A, Source C | unknown | source_confirmed | high | **PASS** |

**判定根拠**: Source A（「建部大社について」）はPilot確認時点の`note`
（`shrine-knowledge-fact-generation-pilot.md`のSource一覧記載）で「日本武尊・
大己貴命…を直接確認」と明記されており、Source Cも祭神・遷座を補助する公式性を
持つ。両Sourceとも祭神間の序列を明示していないため、role=`unknown`を維持する
（Source本文に序列が無い場合`unknown`とする既存Contract・本Review基準に一致）。
不支持の追加情報（御眷属・境内社祭神等のdeity boundary外の情報）は含まれていない。

### 4.2 H1（Human Review、Phase 5）

| ID | history_type | period_text | event_date | confidence | Review |
|---|---|---|---|---|---|
| H1 | tradition | 景行天皇46年（西暦116年、由緒） | null | high | **PASS** |

**判定根拠**: Sourceは「創建」を由緒として提示しており、確定史実として断定して
いない。西暦116年という換算値はSource以上に確定Fact化されておらず、`period_text`
内の参考表記に留まる。`event_date`は`null`のまま（推測生成なし）。`history_type:
tradition`は、古代の創建由緒を確定史実へ格上げしない既存の保守的分類方針
（Pilot時点の`note`「古代の創建由緒を現代の確定史実へ格上げしないため
traditionとして保持する」）と一致し、Contractとも矛盾しない。

### 4.3 H2（Human Review確定済み、Phase 3〜4、再判断せず記録）

3 Sourceが同一の瀬田への遷座イベントを扱っているとHuman Reviewで判断済み。
`天武天皇期`という一般的な時代表現（Source A）は675年（Source B）・676年
（Source C）のいずれとも両立するが、675年 vs 676年という**同一粒度の具体年
競合**は確認済みSourceからは解消不能と判断されている。本監査ではこの判断を
再解釈していない（詳細は§6）。

Human Review後、H2は単一Factから2 Fact（H2-A・H2-B）へ分離された。

| ID | history_type | period_text | event_date | verification_status | confidence | Source | Review |
|---|---|---|---|---|---|---|---|
| H2-A | tradition | 白鳳4年（675年） | null | **disputed** | high | Source B（見どころ） | Human Review確定済み |
| H2-B | tradition | 天武天皇4年（676年） | null | **disputed** | high | Source C（日本遺産ポータル） | Human Review確定済み |

### 4.4 H3（Human Review、Phase 5）

| ID | history_type | period_text | event_date | confidence | Review |
|---|---|---|---|---|---|
| H3 | tradition | 平安時代末期 | null | high | **PASS** |

**判定根拠**: Source A（公式サイト、平治物語を根拠として掲載）に直接の記述が
ある。「祈願」（源頼朝が捕らわれた際の祈願）と「寄進」（源氏再興後の再参拝・
神宝と神領の寄進）を1 Factへまとめている点について確認した——これはSource間の
複数説を1 contentへ合成する「Multiple Fact保持方針」違反ではなく、**単一Source
（建部大社公式）が自ら語る一続きの物語（祈願→再興→再参拝→寄進）**であり、
既存Batch実例（例: Batch 16 平塚八幡宮の「戦国期の兵火と徳川家康公による復興」
History、`temples/data/knowledge_seeds/batch_16_seed.json`で確認——単一の公式
Sourceが語る「兵火で焼失→徳川家康公が復興」という一続きの経緯を1つの
`historical_event`として保持している）と同型のパターンである。したがって
Source粒度を壊すMerge判定には該当しないと判断した。`history_type: tradition`は
一次史料検証を伴わない由緒紹介である旨（Pilot時点の`note`）と整合し、
`historical_event`への確定は行わない。不支持の因果関係の追加（例:
「寄進によって○○が実現した」等）は含まれていない。

### 4.5 建部大社 Fact一覧（最終）

| ID | Fact | Source | history_type/role | verification_status | confidence | Review |
|---|---|---|---|---|---|---|
| D1 | 日本武尊 | A, C | role: unknown | source_confirmed | high | PASS |
| D2 | 大己貴命 | A, C | role: unknown | source_confirmed | high | PASS |
| H1 | 景行天皇46年を起源とする創建由緒 | A | tradition | source_confirmed | high | PASS |
| H2-A | 白鳳4年（675年）に瀬田へ遷し祀られたとする由緒 | B | tradition | **disputed** | high | Human Review確定済み（H2分離） |
| H2-B | 天武天皇4年（676年）に現在地へ移されたと伝わる | C | tradition | **disputed** | high | Human Review確定済み（H2分離） |
| H3 | 源頼朝の祈願と源氏再興後の寄進伝承 | A | tradition | source_confirmed | high | PASS |

**建部大社 Review Result: `PASS`（D1・D2・H1・H3）+ `Multiple Fact分離確定`
（H2→H2-A/H2-B）。HOLD・STOPは0件。**

## 5. 波上宮 Review

### 5.1 Deity（6件、PASS）

| display_name | role | verification_status | confidence | Review |
|---|---|---|---|---|
| 伊弉冉尊 | unknown | source_confirmed | high | **PASS** |
| 速玉男尊 | unknown | source_confirmed | high | **PASS** |
| 事解男尊 | unknown | source_confirmed | high | **PASS** |
| 火神 | enshrined | source_confirmed | high | **PASS** |
| 産土神 | enshrined | source_confirmed | high | **PASS** |
| 少彦名神 | enshrined | source_confirmed | high | **PASS** |

**D1〜D3（伊弉冉尊・速玉男尊・事解男尊）**: 波上宮公式は「御祭神」として列挙
しているが「主祭神」とは明記していない。既存Contract（Sourceに序列が無い場合
`unknown`）に従いroleは`unknown`とする。

**D4〜D6（火神・産土神・少彦名神）**: 波上宮公式が「別鎮斎」として本殿祭神
3柱とは区分して掲載している。Fact Generation Pilot（PR #2533）時点で既に
`role: enshrined`として運用済みであり、Pilotの`note`「公式サイトが『別鎮斎』
として御祭神三柱とは区分して掲載。既存Seedのenshrined運用と整合確認済み」と
一致する。本Human Reviewでこの判断を維持する。

**confidence根拠**: 全6 Deityとも、Fact Generation Pilot時点で既に
Source本文との直接一致が確認され`confidence: high`・`verification_status:
source_confirmed`として構造検証（validate-only/dry-run PASS、Evidence Gate
11/11 usableの一部）を通過済みの内容と完全に一致する。本Human Reviewは
`source_type=shrine_official`であること自体を理由にconfidenceをhighとした
のではなく、**内容がPilot時点で既に確認されたSource確認記録と直接一致する
こと**を根拠にhighを維持している。

### 5.2 History（6件、PASS、旧Pilotとの1対1比較は不可）

| ID | history_type | 内容 | event_date | verification_status | confidence | Review |
|---|---|---|---|---|---|---|
| H1 | founding | 創始年不詳・聖地/拝所としての始まり | null | source_confirmed | high | **PASS** |
| H2 | tradition | 崎山の里主・霊石・熊野権現の御鎮座伝説 | null | source_confirmed | high | **PASS** |
| H3 | regional_context | 那覇港・航海安全・琉球王府崇敬・琉球八社における地域的文脈 | null | source_confirmed | high | **PASS** |
| H4 | historical_event | 明治23年 官幣小社列格 | null | source_confirmed | high | **PASS** |
| H5-A | historical_event | 戦争による被災 | null | source_confirmed | high | **PASS** |
| H5-B | historical_event | 昭和28年以降の社殿再建・平成の造営および境内整備 | null | source_confirmed | high | **PASS** |

**H1（founding、創始年不詳）**: `docs/knowledge/shrine-knowledge-contract.md`
「history_type一覧」節の`founding`定義（「創建・鎮座に関する情報（確定年・
推定年代・**不詳**を区別）」、行303-304、本Review時点で現行developに存在する
ことを直接確認）は、確定年だけでなく不詳の場合も`founding`で表現することを
明示的に許容している。創始年不詳のまま`founding`へ分類することはContractと
矛盾しない。`event_date`は`null`のまま、推測生成していない。

**H2（tradition、御鎮座伝説）**: Fact Generation Pilot時点の内容と完全に一致
（崎山の里主が霊石を得て豊漁となり、熊野権現の神託を受け社殿を建立したという
伝説）。公式自身が「御鎮座伝説」と明記する内容であり、`historical_event`へ
昇格していない。

**H3（regional_context、confidence根拠を最終確認）**: 本Factの内容（那覇港の
航海安全祈願、琉球王府の信仰、琉球八社の首位）は、Fact Generation Pilot時点で
既にSource本文との直接一致が確認され`confidence: high`として構造検証を通過
済みの内容と一致する。特定の創建年ではなく地域信仰の文脈を記述するため
`regional_context`が妥当（`founding`/`historical_event`のような確定的分類には
該当しない）。Source本文にない解釈（例: 特定の交易ルートとの関連づけ等）の
追加は確認されなかった。**unsupported interpretationなし → confidence: high
を確定する。**

**H4（historical_event、明治23年列格）**: Fact Generation Pilot時点の内容と
完全に一致。確定年（明治23年）を伴う制度上の事実であり`historical_event`が
妥当。

**H5-A（historical_event、戦災）・H5-B（historical_event、戦後再建、
confidence根拠を最終確認）**: Fact Generation Pilot時点の単一History
（「波上宮は先の大戦で被災し、昭和28年に本殿と社務所、昭和36年に拝殿を
再建し、平成5年には平成の御造営による社殿が竣工した。」）を、被災（H5-A）と
戦後の再建・造営プロセス（H5-B）に分割した形になっている。H5-Bの中心的主張
（昭和28年の本殿・社務所再建、昭和36年の拝殿再建、平成5年の平成の御造営）は
Pilot時点で既にSource確認済みの内容と直接一致し、一連の復興過程をSource本文が
直接支持している。**ただし「境内整備」という表現は、Pilot時点で記録された
Source確認内容（本殿・社務所・拝殿の再建、社殿の竣工）には明示的に含まれて
おらず、本監査は`WebFetch`によるSource本文の再取得ができないため
（`docs/audit/shrine-knowledge-source-automation-readiness.md`が記録した
ネットワークegress制約が本セッションでも継続）、この語のSource本文への
直接対応を独立に再確認できていない。** 「御造営」という語が社殿本体に加えて
境内整備を含みうる一般的な範囲の表現であり、新しい年代・出来事・因果関係を
追加するものではないと判断し、**この限定的な不確実性を明記した上でconfidence:
highを維持する**（HOLDへは倒さない）。Production Seed化時点でSource本文の
再確認を推奨する（§9 Unresolved参照）。

### 5.3 Fact Boundary

Human Review時点で取得可能な公式Source本文と既存Knowledge Contractから
Human Review Candidateを再構成した結果、Deity 6 / History 6 / Total 12と
なった。

旧Fact Generation Pilot（PR #2533）はDeity 6・History 5・Total 11だった。
ただし**旧History Candidateの本文はscratch Seed（このセッション専用のscratch
DB/scratchpad）にのみ存在し、repositoryへ保存されていない**（Pilot監査文書
`shrine-knowledge-fact-generation-pilot.md`自体もScratch Seedの内容を全文
転記していない）。したがって、今回のHistory 6件を「旧Pilot Factを修正した」
と記録することはできない。**旧Pilot Candidateとの1対1差分比較は不可能**
であり、本監査ではその比較を行っていない（推測復元も行っていない）。

### 5.4 verification_status

既存Contractにおいて、`source_confirmed`は「Source内容との一致確認済み」、
`reviewed`は「複数人または承認工程でレビュー済み」を意味する
（`docs/knowledge/shrine-knowledge-contract.md`
`KNOWLEDGE_VERIFICATION_STATUS_CHOICES`定義を確認）。今回実施したHuman
Reviewが、既存運用上「複数人または承認工程でレビュー済み」に該当する正式な
承認工程であるとContract上確定していないため、**Human Reviewを実施した
ことのみを理由に`reviewed`へ昇格させていない。** 全Deity・全History
とも`verification_status: source_confirmed`を維持する。

### 5.5 波上宮 Review Result

**`PASS`（全12 Fact: Deity 6・History 6）。REVISE・HOLD・STOPは0件。
新たなSource conflictは発見されなかったため、いずれのFactにも`disputed`を
付与していない。**

## 6. H2 Conflict Evidence

| 項目 | 内容 |
|---|---|
| 675年Source | Source B（建部大社公式「見どころ」）——白鳳4年（675年）に瀬田へ遷し祀られたとする趣旨 |
| 676年Source | Source C（日本遺産ポータル「建部大社」）——天武天皇4年（676年）に現在地へ移されたと「伝わる」とする趣旨 |
| 同一遷座と判断した理由 | Source A（建部大社公式「建部大社について」）が示す「天武天皇の時代に瀬田へ移った」という一般的な時代表現が、675年（Source B）・676年（Source C）のいずれとも矛盾なく両立する。3 Sourceは同一の史実的出来事（瀬田への遷座）を異なる粒度で記述していると判断できる |
| unresolved conflict | 「天武天皇期」という時代表現の一致では解消できない、675年 vs 676年という**同一粒度の具体年競合**が残る。確認済み3 Sourceの範囲内では、どちらが正確かをAIが判断していない（禁止事項10「AIが675年/676年のどちらが正しいか判断しない」に従う） |
| Multiple Fact化 | 675年説と676年説を1つの`content`へ合成せず、`ShrineHistory`の別レコード（H2-A/H2-B）として保持する。既存「Multiple Fact保持方針」節（8坂神社の創祀二説パターンと同型の構造）に従う |
| disputed判断 | 8坂神社の創祀二説（其の一・其の二、いずれも`verification_status: source_confirmed`）とは異なり、H2-A/H2-Bは**同一シンボル（瀬田遷座）についての直接competing numeric claim**であるため`verification_status: disputed`とする。8坂神社の二説は同一神社が並立提示する異なる起源伝承であり、Source同士が直接競合する具体年主張ではない点で区別される |
| confidence根拠 | H2-A: Source B本文が675年という具体的な内容を直接記載しており、Fact側でSource以上の推測を加えていないためhigh。H2-B: Source Cが具体年および「伝わる」という伝承性を明示し、Fact側でもその限定を維持しているためhigh。**`shrine_official`であること自体をhighの根拠にしていない**（禁止事項に該当する推論を避けている） |

波上宮のHuman Reviewでは新たなSource conflictは発見されなかった（§5.5）。
本節の対象は建部大社H2のみである。

## 7. Contract Compatibility

| 契約要素 | 適用結果 |
|---|---|
| Multiple Fact保持方針 | H2-A/H2-Bを別`ShrineHistory`レコードとして保持し、`content`を合成していない。既存Model制約（`unique_together`なし）に適合 |
| `tradition != disputed` | H2-A/H2-Bは`history_type: tradition`かつ`verification_status: disputed`——2軸は独立しており矛盾しない（既存Contract「history_type/verification_status/confidenceの3軸分離」節と一致） |
| confidenceと verification_statusの独立性 | H2-A/H2-Bは`disputed` + `confidence: high`——既存Contract「confidenceが`high`であっても、`disputed`のFactはRecommendation Reasonへ使用しない」の直接該当例として成立する |
| Evidence Gate（Recommendation側） | `decide_fact_usability()`（`temples/services/evidence_gate.py`、未変更）は`FACT_READY_VERIFICATION_STATUSES = (source_confirmed, reviewed)`のみを`usable=True`とする。H2-A/H2-Bは`disputed`のため`usable=False`、`display_mode="hidden"`、`reason_strength="suppressed"`となる。Recommendation Reasonには使用されない。波上宮の全12 Factは`source_confirmed`のため`usable=True`となる想定 |
| Evidence Gate（Detail側） | `decide_detail_display_state()`（同ファイル、未変更）は`verification_status: disputed`かつfact-ready Source（`source_confirmed`/`reviewed`）を1件以上Relationする場合`"disputed"`を返す。H2-A/H2-BのSource（Source B/Source C）はいずれも`verification_status: source_confirmed`のため、Detail側では`"disputed"`表示状態となり、Web側（`FactDisplayState`、`resolveFactDisplayState()`）で固定文言「異なる見解を含む情報」とともに個別表示される想定。波上宮の全12 Factは`"full"`表示状態となる想定 |
| Recommendation suppression | H2-A/H2-Bは既存契約によりRecommendation Reasonへは使用されない。波上宮の全12 Factは`disputed`を含まないため、この抑制の対象外である。いずれもコード変更を伴わない既存契約の適用結果であり、本監査で新たに実装したものではない |

本監査はEvidence Gate・Detail表示コードを一切変更していない。上記はいずれも
既存の未変更コードをH2-A/H2-B・波上宮のデータへ適用した場合の**期待される
挙動の記録**であり、実際にscratch DB/Production DBへ投入して動作確認したもの
ではない（§9の通りImportそのものが本監査のスコープ外のため。validate-only/
dry-runの再実行も未実施）。

## 8. Deviations from Pilot

| 神社 | Before（Fact Generation Pilot、PR #2533） | After（Human Review） | Reason |
|---|---|---|---|
| 北海道神宮 | Deity 4・History 3（H1: `tradition`） | Deity 4・History 3（H1: `founding`） | H1のhistory_type訂正（§3参照）。Fact件数に変化なし |
| 建部大社 | Deity 2・History 3（H2は単一Fact、Source 2件） | Deity 2・History 4（H2→H2-A/H2-B、Source 3件） | H2を675年説/676年説の2 Factへ分離。Source Bが新規追加。history_type/role/verification_status/confidenceの意味的判断はH1・H3・D1・D2について変更なし（PASS） |
| 波上宮 | Deity 6・History 5・Total 11 | Deity 6・History 6・Total 12 | Human Review時点で取得可能な公式Source本文と既存Knowledge Contractから Human Review Candidateを再構成した結果。**旧History Candidate本文はscratch Seedにのみ存在しrepositoryへ保存されていないため、「旧Pilot Factを修正した」という表現ではなく「再構成した」と記録する。旧Pilot Candidateとの1対1差分比較は不可能**（§5.3参照） |

## 9. STOP / HOLD

### 波上宮（Closure完了、旧STOP事項を解消）

前版（PR #2536）では、波上宮のHuman Review完了を示す記録がrepository内に
存在しないことを確認し、タスク指示に従い着手せずSTOPとして記録していた。
本改訂で波上宮のHuman Reviewを実施・記録し、このSTOP事項を解消した
（§5参照）。波上宮のHuman Review Result: `PASS`（全12 Fact）。

### 残る未解決事項

- H2-B Source（日本遺産ポータル）記載の「天武天皇4年（676年）」は「伝わる」と
  いう伝承性が明記されており、これをevent_dateへ確定していない（禁止事項12
  に従う）。675年についても同様にevent_date化していない
- Source B（建部大社公式「見どころ」）のURLは本Human Review入力に含まれて
  おらず、本監査では推測補完していない。Production Seed化を検討する際は
  別途URL確認が必要
- 波上宮H5-Bの「境内整備」という表現は、Pilot時点で記録されたSource確認内容
  に明示的な対応が確認できておらず、本監査はネットワークegress制約により
  Source本文を再取得できなかった（§5.2参照）。confidence: highは維持したが、
  Production Seed化前にSource本文の直接再確認を推奨する
- D1/D2/H1/H3（建部大社）・全12 Fact（波上宮）のHuman Reviewは、本監査
  セッションが直接Source本文を再取得して行ったものではなく、Fact Generation
  Pilot時点で記録済みのSource確認内容（Sourceの`note`、各Factの`note`）との
  整合確認として実施した（本セッションの`WebFetch`は
  `docs/audit/shrine-knowledge-source-automation-readiness.md`が記録した通り
  ネットワークegress制約により機能しない）。新たな矛盾は発見されなかった
- 3社ともHuman Review後のFact内容を反映した`validate-only`/`dry-run`の
  再実行は未実施（§10参照）

## 10. Mother Ship Decision Inputs

実Production Seed化・Production Importの可否は本監査では判断しない。
以下の材料のみを提供する。

- **北海道神宮**: PASS WITH 1 REVISION（H1: `tradition`→`founding`）。Deity 4・
  History 3。Human Reviewは完了。ただしrevision後のvalidate-only/dry-run
  再実行はまだ行っていない
- **建部大社**: D1・D2・H1・H3 PASS、H2をH2-A/H2-Bへ分離しdisputed確定。
  Deity 2・History 4（合計6 Fact）。Source BのURL未確認という未解決事項が
  残る。Human Review後のvalidate-only/dry-run再実行はまだ行っていない
- **波上宮**: PASS（全12 Fact: Deity 6・History 6）。Human Reviewは完了。
  H5-Bの「境内整備」表現に軽微な未確認事項が残る。Human Review後の
  validate-only/dry-run再実行はまだ行っていない
- **3社共通**: 北海道神宮・建部大社・波上宮のいずれもHuman Review自体は
  完了した。Human Review後のFact内容（北海道神宮H1のhistory_type変更、
  建部大社H2の2 Fact分離、波上宮の6 History再構成）を反映した新しい
  scratch Knowledge Seedでの`validate-only`/`dry-run`再実行、および
  Production Seed化・Production Importの可否判断は、いずれも本監査では
  実施・判断していない

## Repository Change

`docs/audit/shrine-expansion-batch1-human-review.md`（既存文書）を更新した。
新規Audit文書は作成していない——この文書が北海道神宮・建部大社のHuman
Review結果と、波上宮の未Review STOP事項を既に管理しており、今回の作業は
その波上宮STOP事項のClosureに該当するため、既存文書の更新が適切と判断した。

## Validation

```
$ git status --short
```

の結果、本ドキュメント1件の変更のみであることを確認する（コミット時に
併記）。コード・Seed・DB変更を一切行っていないため、Django testの実行は
不要と判断した。本文書内で事実として引用した既存コード・Contract箇所
（`docs/knowledge/shrine-knowledge-contract.md`のhistory_type定義・3軸分離・
Disputed Evidence Contract・`KNOWLEDGE_VERIFICATION_STATUS_CHOICES`定義、
`backend/temples/services/evidence_gate.py`の`decide_fact_usability`/
`decide_detail_display_state`、`backend/temples/data/knowledge_seeds/
batch_1_7_seed.json`の8坂神社Multiple Fact実例、`batch_16_seed.json`の
平塚八幡宮History実例）は、いずれも本worktree（`origin/develop`起点）上で
実在することを直接確認した。

- Production write = 0
- Production Shrine Seed変更 = 0
- Production Knowledge Seed変更 = 0
- Model / Migration変更 = 0
- Evidence Gate変更 = 0
- Recommendation変更 = 0
- Source Contract変更 = 0
- Knowledge Contract変更 = 0
- validate-only / dry-run再実行 = 0
- Compass branch/worktreeへの変更 = 0
- 旧scratch Fact Candidate（History 5件分の本文）の推測復元 = 0

STOP条件はいずれも該当しなかった。波上宮の旧STOP事項はHuman Review完了に
より解消された。
