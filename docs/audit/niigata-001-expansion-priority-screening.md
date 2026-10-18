# NIIGATA-001 Expansion Priority Screening（lightweight, read-only）

## 1. Status

```text
SCREENING                  = DRAFT FOR MOTHER SHIP REVIEW
PRIORITY_A                 = 5
PRIORITY_B                 = 5
PRIORITY_C                 = 70（DEFERRED_FOR_NOW）
TOTAL                      = 80
bulk deep-source research  = NOT REQUIRED
PROPOSED_NEXT_HANDOFF      = 5 candidates（see §5）. Membership frozen as NIIGATA-001-VPG001. NOT registered

Candidate Master / handoff fixture / identity manifest / Seed write   NONE
G1 / G2 / G3 / Knowledge / Product Surface                           NOT EXECUTED
Production access                                                   NONE
H004 G1                                                             unchanged（PR #3258 is evidence only, not closure）
```

- Recorded at: 2026-10-18
- Base: `develop@84a369b`
- Policy: `docs/knowledge/shrine-expansion-priority-policy.md`
- Updated 2026-10-18: 天津神社（page007-row006）PRIORITY_B → PRIORITY_A after Mother Ship primary-source
  deity verification（§6.1）. No other row changed.

This is **not** G1, G2, G3, a Knowledge review or a Product Surface decision. Every value below is a
screening estimate. Gates still run in full.

## 2. Scope

Universe: the frozen NIIGATA-001 Ready Set（`docs/audit/niigata-batch001-ready-set-freeze.md`, 100 rows）.
H001–H004（20 rows）are already in processing and are excluded. In scope: **H005–H020, 80 rows**.

## 3. Screening reach（read before using the results）

```text
repository / frozen Source    name, address, ready_basis only. No deity / history / benefit for any in-scope row
external web search           AVAILABLE（one query per shrine; 17 rows shared a query with a same-name row）
external page fetch           NOT AVAILABLE（every host DNS-blocked in this environment）
official Source site          NOT REACHABLE（niigata-jinjacho.jp denied, see H004 G1 audit §2.3）
新潟県神社庁 directory / 市町村誌 / 郡誌   NOT CHECKED
```

Consequences:

- Every external fact is at **`SEARCH_SUMMARY`** level: a search result summary attributed to a
  specific page and matched by municipality + locality. **No primary page was opened.** Policy §6.7
  requires primary-page verification before any PRIORITY_A candidate is frozen into a handoff.
- Generic results（e.g. "秋葉神社 usually enshrine 火之迦具土神", Tokyo 愛宕神社, 静岡 秋葉山本宮）were
  never used as evidence for a Niigata row.
- Where a same-name shrine elsewhere in Niigata was returned（e.g. 阿賀野 旦飯野神社 for the 秋葉区 row,
  胎内 荒川神社 for the 新発田 row）, it was **not** attributed. This is noted in `screening_basis`.
- **C = 70 mostly reflects reach, not value**（policy §5.1）. The 70 rows had no shrine-specific result in
  web search. Many are ujigami-scale shrines whose records are more likely to be in 市町村誌 or the 神社庁
  directory than on the web. They are `DEFERRED_FOR_NOW`. **Bulk deep-source research is not required.**
  A row is re-screened only when a policy §5.1 trigger applies.

`IDENTITY_SOURCE = STRONG` for all 80: each is a frozen official-Source row with exact name and address.
The 13 `HUMAN_REVIEW_RELEASED` rows（愛宕神社 ×10, 雷神社 ×3）were released by Mother Ship M5 as distinct
from the returned Production collision row.

## 4. Screening table

Columns follow the policy fields. `[Sn]` refers to §7 Sources.

| handoff | source_position | raw_name | raw_address | identity_source | position_likelihood | deity_evidence | history_evidence | benefit_evidence | independent_source | recommendation_distinctiveness | model_risk | priority_class | screening_basis | uncertainty |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| H005 | page003-row001 | 赤田神社 | 刈羽郡刈羽村大字赤田北方561番地 | STRONG | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | PRIORITY_C | web search（name + municipality + locality）: no shrine-specific deity / history / benefit result | deep sources（神社庁 directory, 市町村誌）not checked |
| H005 | page003-row002 | 赤玉神社 | 佐渡市赤玉516番地の2 | STRONG | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | PRIORITY_C | web search（name + municipality + locality）: no shrine-specific deity / history / benefit result | deep sources（神社庁 directory, 市町村誌）not checked |
| H005 | page003-row003 | 赤塚神社 | 新潟市西区赤塚2709番地 | STRONG | UNKNOWN | UNKNOWN | YES | UNKNOWN | NO | UNKNOWN | UNKNOWN | PRIORITY_B | 新潟市 文化資源 PDF（西区）: 稚児舞 revived 2010-04, offered at 赤塚神社 春季大祭 [S1] | deity / founding unknown; relation to 赤塚の神明社（伝・船江神社, 式内）not confirmed |
| H005 | page003-row004 | 秋成神社 | 中魚沼郡津南町大字秋成943番地 | STRONG | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | PRIORITY_C | web search（name + municipality + locality）: no shrine-specific deity / history / benefit result | deep sources（神社庁 directory, 市町村誌）not checked |
| H005 | page003-row005 | 秋葉社 | 長岡市与板町与板乙1423ノ4番地 | STRONG | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | PRIORITY_C | web search: only 秋葉三尺坊大権現（長岡市 秋葉公園, a different site）returned; not attributed | 与板 shrine itself not found; deep sources not checked |
| H006 | page003-row006 | 秋葉神社 | 新潟市中央区古町通11番町1688番地 | STRONG | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | PRIORITY_C | web search（name + municipality + locality）: no shrine-specific deity / history / benefit result | deep sources（神社庁 directory, 市町村誌）not checked |
| H006 | page003-row007 | 秋葉神社 | 新潟市秋葉区秋葉3丁目8番19号 | STRONG | HIGH | YES | YES | UNKNOWN | NO | MEDIUM | UNKNOWN | PRIORITY_A | 新潟市 文化資源ガイド（秋葉区）[S2]: 秋葉3-8-19; 祭神 大己貴神 with 大物主命・菅原道真; former 桂家 guardian, transferred to 秋葉町内 1964, 250th year 2013, halls rebuilt 明治3 | single municipal source; summary gives 明治3年 as 1872（明治3 = 1870）; benefit not stated |
| H006 | page003-row008 | 秋葉神社 | 新発田市下山田459番地 | STRONG | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | PRIORITY_C | web search（name + municipality + locality）: no shrine-specific deity / history / benefit result | deep sources（神社庁 directory, 市町村誌）not checked |
| H006 | page003-row009 | 秋葉神社 | 糸魚川市大字鉄炮140番地 | STRONG | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | PRIORITY_C | web search（name + municipality + locality）: no shrine-specific deity / history / benefit result（combined query with another same-name row） | deep sources（神社庁 directory, 市町村誌）not checked |
| H006 | page003-row010 | 秋葉神社 | 糸魚川市大字横町58番地 | STRONG | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | PRIORITY_C | web search（name + municipality + locality）: no shrine-specific deity / history / benefit result（combined query with another same-name row） | deep sources（神社庁 directory, 市町村誌）not checked |
| H007 | page004-row001 | 秋葉神社 | 南魚沼市思川662番地 | STRONG | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | PRIORITY_C | web search（name + municipality + locality）: no shrine-specific deity / history / benefit result | deep sources（神社庁 directory, 市町村誌）not checked |
| H007 | page004-row002 | 秋葉社 | 小千谷市上ノ山1丁目5番35号 | STRONG | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | PRIORITY_C | web search（name + municipality + locality）: no shrine-specific deity / history / benefit result | deep sources（神社庁 directory, 市町村誌）not checked |
| H007 | page004-row003 | 秋葉神社 | 長岡市寺泊志戸橋792番地乙 | STRONG | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | PRIORITY_C | web search（name + municipality + locality）: no shrine-specific deity / history / benefit result | deep sources（神社庁 directory, 市町村誌）not checked |
| H007 | page004-row004 | 秋葉神社 | 村上市久保多町4番27号 | STRONG | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | PRIORITY_C | web search（name + municipality + locality）: no shrine-specific deity / history / benefit result（combined query with another same-name row） | deep sources（神社庁 directory, 市町村誌）not checked |
| H007 | page004-row005 | 秋葉神社 | 村上市長井町2番16号 | STRONG | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | PRIORITY_C | web search（name + municipality + locality）: no shrine-specific deity / history / benefit result（combined query with another same-name row） | deep sources（神社庁 directory, 市町村誌）not checked |
| H008 | page004-row006 | 秋葉神社 | 五泉市村松甲2328番地 | STRONG | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | PRIORITY_C | web search（name + municipality + locality）: no shrine-specific deity / history / benefit result | deep sources（神社庁 directory, 市町村誌）not checked |
| H008 | page004-row007 | 秋葉神社 | 魚沼市青島3743番地 | STRONG | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | PRIORITY_C | web search（name + municipality + locality）: no shrine-specific deity / history / benefit result | deep sources（神社庁 directory, 市町村誌）not checked |
| H008 | page004-row008 | 明口神社 | 小千谷市大字川井58番地 | STRONG | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | PRIORITY_C | web search（name + municipality + locality）: no shrine-specific deity / history / benefit result | deep sources（神社庁 directory, 市町村誌）not checked |
| H008 | page004-row009 | 旦飯野神社 | 阿賀野市宮下195番地 | STRONG | UNKNOWN | YES | YES | NO | NO | LOW | UNKNOWN | PRIORITY_B | 新潟県観光協会 spot / blog [S3]: 祭神 誉田別命, at current site since 寛政4（1792）, hereditary 鈴木氏 priests, 御神霊石 | tourism / power-spot copy only; benefit only generic（諸願成就）; '1700 years' unsupported; lot 宮下195 not in source |
| H008 | page004-row010 | 旦飯野神社 | 新潟市秋葉区朝日535番地 | STRONG | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | PRIORITY_C | web search: only the 阿賀野市 旦飯野神社 returned; same-name evidence not attributed | 秋葉区朝日 shrine itself not found; deep sources not checked |
| H009 | page005-row001 | 朝倉社 | 燕市大船渡30番地 | STRONG | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | PRIORITY_C | web search（name + municipality + locality）: no shrine-specific deity / history / benefit result | deep sources（神社庁 directory, 市町村誌）not checked |
| H009 | page005-row002 | 淺原神社 | 小千谷市片貝町6548番地 | STRONG | UNKNOWN | UNKNOWN | YES | UNKNOWN | YES | HIGH | UNKNOWN | PRIORITY_B | Tohoku tourism / tabi-mag / JR East media [S4]: 片貝まつり fireworks are the autumn 例大祭 offering to this shrine（玉送り, 筒引き）; called 王子権現（熊野信仰）in the 神仏習合 era | deity name not found（A blocked on deity）; fireworks origin dated differently by source（early / mid Edo） |
| H009 | page005-row003 | 旭稲荷神社 | 新潟市中央区水道町2丁目808番地ノ60 | STRONG | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | PRIORITY_C | web search（name + municipality + locality）: no shrine-specific deity / history / benefit result | deep sources（神社庁 directory, 市町村誌）not checked |
| H009 | page005-row004 | 朝日神社 | 長岡市朝日554番地 | STRONG | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | PRIORITY_C | web search（name + municipality + locality）: no shrine-specific deity / history / benefit result | deep sources（神社庁 directory, 市町村誌）not checked |
| H009 | page005-row005 | 淺間社 | 上越市吉川区大賀1131番地 | STRONG | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | PRIORITY_C | web search（name + municipality + locality）: no shrine-specific deity / history / benefit result | deep sources（神社庁 directory, 市町村誌）not checked |
| H010 | page005-row006 | 芦ケ崎神社 | 中魚沼郡津南町大字芦ケ崎甲1601番地 | STRONG | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | PRIORITY_C | web search（name + municipality + locality）: no shrine-specific deity / history / benefit result | deep sources（神社庁 directory, 市町村誌）not checked |
| H010 | page005-row007 | 安土神社 | 五泉市小面谷331番地 | STRONG | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | PRIORITY_C | web search（name + municipality + locality）: no shrine-specific deity / history / benefit result | deep sources（神社庁 directory, 市町村誌）not checked |
| H010 | page005-row008 | 愛宕社 | 長岡市与板町与板乙2番地 | STRONG | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | PRIORITY_C | web search（name + municipality + locality）: no shrine-specific deity / history / benefit result | deep sources（神社庁 directory, 市町村誌）not checked |
| H010 | page005-row009 | 愛宕神社 | 新潟市中央区古町通2番町495番地乙 | STRONG | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | PRIORITY_C | web search（name + municipality + locality）: no shrine-specific deity / history / benefit result | deep sources（神社庁 directory, 市町村誌）not checked; M5: distinct from the returned Production collision row |
| H010 | page005-row010 | 愛宕神社 | 新潟市西蒲区巻甲527番地 | STRONG | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | PRIORITY_C | web search（name + municipality + locality）: no shrine-specific deity / history / benefit result | deep sources（神社庁 directory, 市町村誌）not checked; M5: distinct from the returned Production collision row |
| H011 | page006-row001 | 愛宕神社 | 長岡市寺泊一枚田5501番地 | STRONG | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | PRIORITY_C | web search（name + municipality + locality）: no shrine-specific deity / history / benefit result | deep sources（神社庁 directory, 市町村誌）not checked; M5: distinct from the returned Production collision row |
| H011 | page006-row002 | 愛宕神社 | 長岡市愛宕1丁目6番3号 | STRONG | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | PRIORITY_C | web search（name + municipality + locality）: no shrine-specific deity / history / benefit result | deep sources（神社庁 directory, 市町村誌）not checked; M5: distinct from the returned Production collision row |
| H011 | page006-row003 | 愛宕神社 | 長岡市塩新町562番地子 | STRONG | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | PRIORITY_C | web search（name + municipality + locality）: no shrine-specific deity / history / benefit result | deep sources（神社庁 directory, 市町村誌）not checked; M5: distinct from the returned Production collision row |
| H011 | page006-row004 | 愛宕神社 | 新発田市中央町3丁目1番15号 | STRONG | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | PRIORITY_C | web search（name + municipality + locality）: no shrine-specific deity / history / benefit result | deep sources（神社庁 directory, 市町村誌）not checked; M5: distinct from the returned Production collision row |
| H011 | page006-row005 | 愛宕神社 | 十日町市下条1丁目697番地 | STRONG | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | PRIORITY_C | web search（name + municipality + locality）: no shrine-specific deity / history / benefit result | deep sources（神社庁 directory, 市町村誌）not checked; M5: distinct from the returned Production collision row |
| H012 | page006-row006 | 愛宕神社 | 村上市菅沼68番地 | STRONG | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | PRIORITY_C | web search（name + municipality + locality）: no shrine-specific deity / history / benefit result | deep sources（神社庁 directory, 市町村誌）not checked; M5: distinct from the returned Production collision row |
| H012 | page006-row007 | 愛宕神社 | 糸魚川市大字田中3102番地 | STRONG | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | PRIORITY_C | web search（name + municipality + locality）: no shrine-specific deity / history / benefit result | deep sources（神社庁 directory, 市町村誌）not checked; M5: distinct from the returned Production collision row |
| H012 | page006-row008 | 愛宕神社 | 五泉市村松甲3326番地 | STRONG | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | PRIORITY_C | web search（name + municipality + locality）: no shrine-specific deity / history / benefit result | deep sources（神社庁 directory, 市町村誌）not checked; M5: distinct from the returned Production collision row |
| H012 | page006-row009 | 愛宕神社 | 上越市大字愛宕国分769番地 | STRONG | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | PRIORITY_C | web search（name + municipality + locality）: no shrine-specific deity / history / benefit result | deep sources（神社庁 directory, 市町村誌）not checked; M5: distinct from the returned Production collision row |
| H012 | page006-row010 | 熱串彦神社 | 佐渡市長江854番地 | STRONG | UNKNOWN | YES | YES | UNKNOWN | NO | HIGH | UNKNOWN | PRIORITY_A | 新潟県観光協会 spot [S5]: 式内社（佐渡国 九社の一）, early-Heian founding, hall 正徳4（1714）, thatched 能舞台 of the 安永 era（市文化財）; main deity = 加茂氏 祖神, 金山彦命 配祀 | single publisher; main deity named only as '加茂氏の祖神'; benefit not stated; lot 長江854 not in source |
| H013 | page007-row001 | 熱田社 | 柏崎市大字西長鳥甲126番地 | STRONG | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | PRIORITY_C | web search（name + municipality + locality）: no shrine-specific deity / history / benefit result | deep sources（神社庁 directory, 市町村誌）not checked |
| H013 | page007-row002 | 熱田社 | 佐渡市竹田36番地 | STRONG | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | PRIORITY_C | web search（name + municipality + locality）: no shrine-specific deity / history / benefit result（combined query with another same-name row） | deep sources（神社庁 directory, 市町村誌）not checked |
| H013 | page007-row003 | 熱田神社 | 妙高市大字青田909番地 | STRONG | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | PRIORITY_C | web search（name + municipality + locality）: no shrine-specific deity / history / benefit result | deep sources（神社庁 directory, 市町村誌）not checked |
| H013 | page007-row004 | 熱田神社 | 佐渡市秋津1135番地 | STRONG | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | PRIORITY_C | web search（name + municipality + locality）: no shrine-specific deity / history / benefit result（combined query with another same-name row） | deep sources（神社庁 directory, 市町村誌）not checked |
| H013 | page007-row005 | 阿比多神社 | 上越市大字長浜904番地，878番地 | STRONG | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | PRIORITY_C | web search（name + municipality + locality）: no shrine-specific deity / history / benefit result | deep sources（神社庁 directory, 市町村誌）not checked |
| H014 | page007-row006 | 天津神社 | 糸魚川市一の宮1丁目3番34号 | STRONG | HIGH | YES | YES | UNKNOWN | YES | HIGH | POSSIBLE | PRIORITY_A | 文化遺産オンライン + 新潟県観光協会 [S6]: 糸魚川・能生の舞楽 = 重要無形民俗文化財（1980-01-28, 天津神社舞楽会）, 春大祭 けんか祭り; precinct has two honden 天津神社・奴奈川神社; deity: PRIMARY_PAGE_VERIFIED by Mother Ship（2026-10-18, §6.1） | deity name / source reference NOT_SUPPLIED_IN_REPO（to be recorded before G1）; two-honden（天津神社・奴奈川神社）structure remains a G1 / G3 MODEL_RISK question |
| H014 | page007-row007 | 天津神社 | 上越市大字東京田34番地1 | STRONG | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | PRIORITY_C | web search（name + municipality + locality）: no shrine-specific deity / history / benefit result | deep sources（神社庁 directory, 市町村誌）not checked |
| H014 | page007-row008 | 天照大神社 | 柏崎市大字旧広田388番地 | STRONG | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | PRIORITY_C | web search（name + municipality + locality）: no shrine-specific deity / history / benefit result | deep sources（神社庁 directory, 市町村誌）not checked |
| H014 | page007-row009 | 天照大神社諏訪社合殿 | 新潟市西蒲区真木1587番地 | STRONG | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | POSSIBLE | PRIORITY_C | web search（name + municipality + locality）: no shrine-specific deity / history / benefit result; name states 合殿 | 合殿 implies more than one principal enshrinement（G3 question）; deep sources not checked |
| H014 | page007-row010 | 荒川神社 | 新発田市荒川5431番地 | STRONG | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | PRIORITY_C | web search: only the 胎内市桃崎浜 荒川神社 returned; not attributed | deep sources（神社庁 directory, 市町村誌）not checked |
| H015 | page008-row001 | 荒川神社 | 村上市小岩内463番地 | STRONG | UNKNOWN | UNKNOWN | YES | UNKNOWN | NO | UNKNOWN | UNKNOWN | PRIORITY_B | 村上市 PDF citing 神林村誌 [S7]: 小岩内; oral founding 大同4（809）, described as 式内社, 4th rebuilding 元治元（1864） | founding is oral tradition; 式内社 claim not cross-checked; deity unknown |
| H015 | page008-row002 | 荒川神社 | 村上市荒川542番地 | STRONG | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | PRIORITY_C | web search（name + municipality + locality）: no shrine-specific deity / history / benefit result | deep sources（神社庁 directory, 市町村誌）not checked |
| H015 | page008-row003 | 荒川神社 | 胎内市桃崎浜187番地 | STRONG | UNKNOWN | YES | YES | YES | YES | HIGH | UNKNOWN | PRIORITY_A | 新潟県（新発田地域振興局）北前船 page + 新潟県観光協会 + 胎内市 [S8]: 祭神 天鈿女命; 荒川三湊 桃崎浜; 船絵馬 86 offered by shipowners praying for safe voyages; 模型和船2隻 = 国 重要有形民俗文化財（1970）; 社殿 登録有形文化財（令和元年） | summary gives '天保12年(1814年)'（天保12 = 1841）; lot 桃崎浜187 not in source |
| H015 | page008-row004 | 荒貴神社 | 佐渡市泉甲395番地 | STRONG | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | PRIORITY_C | web search（name + municipality + locality）: no shrine-specific deity / history / benefit result（combined query with another same-name row） | deep sources（神社庁 directory, 市町村誌）not checked |
| H015 | page008-row005 | 荒崎神社 | 佐渡市椿260番地2 | STRONG | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | PRIORITY_C | web search（name + municipality + locality）: no shrine-specific deity / history / benefit result（combined query with another same-name row） | deep sources（神社庁 directory, 市町村誌）not checked |
| H016 | page008-row006 | 荒沢神社 | 三条市大字荒沢337番地3 | STRONG | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | PRIORITY_C | web search（name + municipality + locality）: no shrine-specific deity / history / benefit result | deep sources（神社庁 directory, 市町村誌）not checked |
| H016 | page008-row007 | 顯見前神社 | 柏崎市西山町礼拝368番地 | STRONG | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | PRIORITY_C | web search（name + municipality + locality）: no shrine-specific deity / history / benefit result | deep sources（神社庁 directory, 市町村誌）not checked |
| H016 | page008-row008 | 荒御崎四柱神社 | 新発田市丑首59番地 | STRONG | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | POSSIBLE | PRIORITY_C | web search（name + municipality + locality）: no shrine-specific deity / history / benefit result; name states 四柱 | 四柱 implies a deity group（Collective model question for G3）; deep sources not checked |
| H016 | page008-row009 | 新屋敷神社 | 新発田市新屋敷213番地 | STRONG | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | PRIORITY_C | web search（name + municipality + locality）: no shrine-specific deity / history / benefit result（combined query with another same-name row） | deep sources（神社庁 directory, 市町村誌）not checked |
| H016 | page008-row010 | 新屋神社 | 村上市新屋775番地甲 | STRONG | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | PRIORITY_C | web search（name + municipality + locality）: no shrine-specific deity / history / benefit result（combined query with another same-name row） | deep sources（神社庁 directory, 市町村誌）not checked |
| H017 | page009-row001 | 粟ケ嶽神社 | 加茂市大字宮寄上1089番地2 | STRONG | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | PRIORITY_C | web search（name + municipality + locality）: no shrine-specific deity / history / benefit result | deep sources（神社庁 directory, 市町村誌）not checked |
| H017 | page009-row002 | 粟島神社 | 五泉市粟島1番23号 | STRONG | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | PRIORITY_C | web search（name + municipality + locality）: no shrine-specific deity / history / benefit result | deep sources（神社庁 directory, 市町村誌）not checked |
| H017 | page009-row003 | 淡島神社 | 胎内市新栄町5番90号 | STRONG | UNKNOWN | UNKNOWN | YES | UNKNOWN | NO | UNKNOWN | UNKNOWN | PRIORITY_B | 文化遺産オンライン [S9]: 淡島神社拝殿 = 登録有形文化財（入母屋造, 龍彫刻）, 旧中条町 | cultural-property address 新栄町3601-2 ≠ frozen 新栄町5番90号（G1 must reconcile）; deity unknown |
| H017 | page009-row004 | 井伊神社 | 長岡市与板町与板甲305番地 | STRONG | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | PRIORITY_C | web search（name + municipality + locality）: no shrine-specific deity / history / benefit result | deep sources（神社庁 directory, 市町村誌）not checked |
| H017 | page009-row005 | 飯縄社 | 糸魚川市大字東中1409番地 | STRONG | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | PRIORITY_C | web search（name + municipality + locality）: no shrine-specific deity / history / benefit result（combined query with another same-name row） | deep sources（神社庁 directory, 市町村誌）not checked |
| H018 | page009-row006 | 飯綱社 | 柏崎市大字大清水1505番地 | STRONG | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | PRIORITY_C | web search（name + municipality + locality）: no shrine-specific deity / history / benefit result（combined query with another same-name row） | deep sources（神社庁 directory, 市町村誌）not checked |
| H018 | page009-row007 | 飯持神社 | 佐渡市飯持236番地 | STRONG | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | PRIORITY_C | web search（name + municipality + locality）: no shrine-specific deity / history / benefit result | deep sources（神社庁 directory, 市町村誌）not checked |
| H018 | page009-row008 | 醫王神社 | 長岡市松尾975番地 | STRONG | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | PRIORITY_C | web search（name + municipality + locality）: no shrine-specific deity / history / benefit result | deep sources（神社庁 directory, 市町村誌）not checked |
| H018 | page009-row009 | 雷神社 | 村上市吉浦2126番地 | STRONG | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | PRIORITY_C | web search（name + municipality + locality）: no shrine-specific deity / history / benefit result（combined query with another same-name row） | deep sources（神社庁 directory, 市町村誌）not checked; M5: distinct from the returned Production collision row |
| H018 | page009-row010 | 雷神社 | 村上市大場沢1236番地 | STRONG | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | PRIORITY_C | web search（name + municipality + locality）: no shrine-specific deity / history / benefit result（combined query with another same-name row） | deep sources（神社庁 directory, 市町村誌）not checked; M5: distinct from the returned Production collision row |
| H019 | page010-row001 | 雷神社 | 岩船郡関川村大字八ツ口225番地1 | STRONG | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | PRIORITY_C | web search（name + municipality + locality）: no shrine-specific deity / history / benefit result（combined query with another same-name row） | deep sources（神社庁 directory, 市町村誌）not checked; M5: distinct from the returned Production collision row |
| H019 | page010-row002 | 雷土神社 | 南魚沼市雷土484番地 | STRONG | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | PRIORITY_C | web search（name + municipality + locality）: no shrine-specific deity / history / benefit result（combined query with another same-name row） | deep sources（神社庁 directory, 市町村誌）not checked |
| H019 | page010-row003 | 雷土神社 | 南魚沼市雷土新田129番地 | STRONG | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | PRIORITY_C | web search（name + municipality + locality）: no shrine-specific deity / history / benefit result（combined query with another same-name row） | deep sources（神社庁 directory, 市町村誌）not checked |
| H019 | page010-row004 | 五十嵐神社 | 三条市大字飯田2283番地 | STRONG | HIGH | YES | YES | UNKNOWN | YES | HIGH | UNKNOWN | PRIORITY_A | ja.wikid.org（Wikipedia mirror）+ 陸上自衛隊新潟地本 PR PDF [S10]: 飯田2283; 祭神 五十日帯彦命; 式内社 伊加良志神社 比定（majority view, 八木神社 = 論社）; deity brought 治水・農耕 to 下田郷, origin of the 五十嵐川 name; 全国五十嵐会 gathers here | both publishers are secondary; 式内社 identification is a scholarly view; benefit not stated |
| H019 | page010-row005 | 五十君神社 | 上越市三和区所山田550番地 | STRONG | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | PRIORITY_C | web search（name + municipality + locality）: no shrine-specific deity / history / benefit result | deep sources（神社庁 directory, 市町村誌）not checked |
| H020 | page010-row006 | 伊久礼神社 | 三条市井栗1丁目24番22号 | STRONG | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | PRIORITY_C | web search（name + municipality + locality）: no shrine-specific deity / history / benefit result | deep sources（神社庁 directory, 市町村誌）not checked |
| H020 | page010-row007 | 池ケ原神社 | 小千谷市大字池ケ原126番地 | STRONG | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | PRIORITY_C | web search（name + municipality + locality）: no shrine-specific deity / history / benefit result | deep sources（神社庁 directory, 市町村誌）not checked |
| H020 | page010-row008 | 池尻神社 | 十日町市池尻579番地 | STRONG | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | PRIORITY_C | web search（name + municipality + locality）: no shrine-specific deity / history / benefit result | deep sources（神社庁 directory, 市町村誌）not checked |
| H020 | page010-row009 | 池部神社 | 上越市大字下池部1299番地 | STRONG | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | PRIORITY_C | web search（name + municipality + locality）: no shrine-specific deity / history / benefit result | deep sources（神社庁 directory, 市町村誌）not checked |
| H020 | page010-row010 | 石井神社 | 柏崎市西本町2丁目3番6号 | STRONG | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | PRIORITY_C | web search（name + municipality + locality）: no shrine-specific deity / history / benefit result | deep sources（神社庁 directory, 市町村誌）not checked |

## 5. PROPOSED_NEXT_HANDOFF（PRIORITY_A only; not frozen, not registered）

**5** rows meet PRIORITY_A. Ranks 1–4 are ordered by evidence strength. Rank 5（天津神社）was moved
B → A after Mother Ship primary-source deity verification（§6.1）. The membership is frozen as
`NIIGATA-001-VPG001`（`docs/audit/niigata-001-vpg001-freeze.md`）. Not registered at G0.

| rank | source_position | candidate | why this shrine（source-backed at SEARCH_SUMMARY level） | before freezing |
|---|---|---|---|---|
| 1 | page008-row003 | 荒川神社（胎内市桃崎浜187番地） | 北前船 port shrine. Shipowners' 船絵馬 votives for safe voyages, 国 重要有形民俗文化財 model ships, deity 天鈿女命. Deity, history and benefit all YES, from three publishers | primary-page check; resolve 天保12 vs 1814 |
| 2 | page010-row004 | 五十嵐神社（三条市大字飯田2283番地） | deity 五十日帯彦命 as the 下田郷 pioneer of 治水・農耕, origin of the 五十嵐川 name, 式内社 伊加良志神社 比定 | primary / official source（both current sources are secondary） |
| 3 | page006-row010 | 熱串彦神社（佐渡市長江854番地） | 佐渡国 式内社, 加茂氏 ancestral deity with 金山彦命, Edo-era thatched noh stage（市文化財） | second publisher; name the main deity |
| 4 | page003-row007 | 秋葉神社（新潟市秋葉区秋葉3丁目8番19号） | an 秋葉 shrine enshrining 大己貴神 with 大物主命・菅原道真, not the usual fire deity; former 桂家 guardian | second publisher; distinctiveness only MEDIUM |
| 5 | page007-row006 | 天津神社（糸魚川市一の宮1丁目3番34号） | 糸魚川・能生の舞楽（重要無形民俗文化財, 天津神社舞楽会）, けんか祭り; deity confirmed by Mother Ship primary-source verification | record deity name / source reference; two-honden（天津神社・奴奈川神社）structure stays a G1 / G3 MODEL_RISK question |

Strongest remaining B row（high distinctiveness, deity not yet found）, recommended for **targeted deity
research before** any further A selection. It is not proposed for the handoff:

- page005-row002 淺原神社（小千谷市片貝町）: 片貝まつり fireworks offered to this shrine; former 王子権現.

## 6. Decisions for Mother Ship

1. **Accept or revise the B / C operational line**（policy §5.1: C = no shrine-specific signal found）. The
   alternative is treating every no-result row as B. That keeps C empty, but then B means nothing.
2. **How to form the next handoff.** The five A rows come from five different frozen handoffs（H006, H012,
   H014, H015, H019）. The frozen handoff plan is Source-order, max 5. Picking across it needs an explicit
   Mother Ship decision: a new value-selected handoff, or re-ordering whole frozen handoffs.
3. **C rows:** `PRIORITY_C = DEFERRED_FOR_NOW`, `bulk deep-source research = NOT REQUIRED`. Re-screen only on a
   policy §5.1 trigger（new shrine-specific source, Recommendation supply expansion, coverage goal,
   scheduled cycle）.
4. **Network access** for primary-page verification（`pref.niigata.lg.jp`, `city.*.niigata.jp` /
   `city.*.lg.jp`, `online.bunka.go.jp`, `niigata-kankou.or.jp`, `niigata-jinjacho.jp`）, if verification
   should happen in this environment.

### 6.1 Next targeted research

```text
天津神社（page007-row006, 糸魚川市一の宮1丁目3番34号）   RESOLVED → PRIORITY_A
淺原神社（page005-row002, 小千谷市片貝町6548番地）       OPEN（PRIORITY_B）
```

Purpose: try to confirm **deity evidence** for each, and determine whether either can move
**B → A**. Both already have HIGH distinctiveness, and history YES from independent publishers. Deity is the
only missing A condition（policy §5: at least 2 of deity / history / benefit = YES）.

**天津神社 — resolved.** Mother Ship verified the enshrined deity against a primary source and approved
PRIORITY_A.

```text
DEITY_EVIDENCE                  = YES
HISTORY_EVIDENCE                = YES
RECOMMENDATION_DISTINCTIVENESS  = HIGH
MODEL_RISK                      = POSSIBLE
PRIORITY_CLASS                  = PRIORITY_A
deity evidence level            = PRIMARY_PAGE_VERIFIED（Mother Ship, 2026-10-18）
deity name / source reference   = NOT_SUPPLIED_IN_REPO（to be recorded before G1）
```

This satisfies the policy §6 rule 7 primary-page requirement for the deity fact only. The history facts
stay at SEARCH_SUMMARY level. The precinct has two honden（天津神社・奴奈川神社）. Whether that is one
candidate entity, and whether current Knowledge models can represent it without meaning loss, **remains
open as a G1 / G3 MODEL_RISK question**. The reclassification does not decide it.

Google Maps screenshots supplied by Mother Ship are noted **only as future G2 preflight visual evidence**.
No coordinate is adopted from them, and POSITION_LIKELIHOOD is unchanged（HIGH）.

**淺原神社 — still open.** It stays PRIORITY_B until deity evidence is found.

Counts after this update: A 5 / B 5 / C 70. No other row changed.

## 7. Sources（SEARCH_SUMMARY level; not opened）

- [S1] 新潟市 文化資源（西区）: https://www.city.niigata.lg.jp/kanko/bunka/shinko/bunkashigen/bunkaisannintei2.files/nishiku.pdf ; 西区ガイドマップ: https://www.city.niigata.lg.jp/oyakudachi/guidebook.files/nishikugaidomap2-1.pdf
- [S2] 新潟市 文化資源（秋葉区）: https://www.city.niigata.lg.jp/kanko/bunka/shinko/bunkashigen/bunkaisannintei2.files/akihaku.pdf
- [S3] 新潟県観光協会: https://niigata-kankou.or.jp/spot/42269 ; https://niigata-kankou.or.jp/blog/37
- [S4] 東北観光推進機構: https://www.tohokukanko.jp/zh_TW/attractions/detail_10071.html ; tabi-mag: https://tabi-mag.jp/katagaifes/ ; JR東日本: https://media.jreast.co.jp/articles/1771
- [S5] 新潟県観光協会: https://niigata-kankou.or.jp/spot/42601
- [S6] 文化遺産オンライン: https://online.bunka.go.jp/heritages/detail/159278 ; 新潟県観光協会: https://niigata-kankou.or.jp/event/12429 ; https://weathernews.jp/hatsumoude/area/niigata/15216/
- [S7] 村上市: https://www.city.murakami.lg.jp/uploaded/attachment/17337.pdf
- [S8] 新潟県: https://www.pref.niigata.lg.jp/site/shibata/kitamaebune02.html ; 新潟県観光協会: https://niigata-kankou.or.jp/spot/7288 ; 胎内市: https://www.city.tainai.niigata.jp/tayori/documents/tainai20250301.pdf
- [S9] 文化遺産オンライン（胎内市）: https://online.bunka.go.jp/heritages/region/15/15227
- [S10] ja.wikid.org: https://ja.wikid.org/%E4%BA%94%E5%8D%81%E5%B5%90%E7%A5%9E%E7%A4%BE ; 自衛隊新潟地本: https://www.mod.go.jp/pco/niigata/HP/03-sho/04-kamo/kamo-member4/kamo-member4-6.pdf

## 8. Not changed

```text
Candidate Master / handoff fixture / identity manifest   NONE
Base Seed / Knowledge Seed                               NONE
candidate IDs                                            NONE created
G1 / G2 / coordinates / Product Surface                  NONE
recommendation ranking / scoring / eligibility           NONE
Production                                               NONE（no connection）
H004 G1 / PR #3258                                       unchanged
```
