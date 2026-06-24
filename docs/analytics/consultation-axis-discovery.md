# Consultation Axis Discovery

## 目的

直近100件の相談ログから user role の相談文のみを抽出し、今後 `consultation_axis` 候補を発見するための監査用データセットを作る。

このドキュメントでは taxonomy は確定しない。LLMクラスタ分析の実API実行も行わない。

## 取得元

- 主取得元: `temples_conciergemessage` / `temples_conciergethread`
- 相談文: `ConciergeMessage.role = user` の `content`
- `need_tags`: `temples_concierge_recommendation_log.need_tags` を優先。未取得時は `ConciergeThread.tags` を補助参照。
- `matched_need_tags`: `ConciergeThread.recommendations_v2` または `recommendations` 内の `breakdown.matched_need_tags` / `_explanation_payload.matched_need_tags`
- `history_theme`: `ConciergeThread.recommendations_v2` または `recommendations` 内の `history_theme` / `_explanation_payload.history_context.theme`
- 実行DB alias: `default`（実データDBの環境変数で実行する。SQLite固定ではない）
- 抽出上限: `100`

## 抽出条件

- user role の発話のみを抽出する。
- 新しい順に `created_at DESC, id DESC` で最大100件を対象にする。
- docsにはユーザーID、anonymous_id、thread_id、message_id、メールアドレス等の識別情報を出さない。
- 取得できない項目は `未取得` と記録する。
- DBスキーマ、migration、recommendation score 実装は変更しない。

## 取得状況

- `temples_conciergemessage`: `あり`
- `temples_conciergethread`: `あり`
- `temples_concierge_recommendation_log`: `あり`
- `ConciergeThread.recommendations_v2`: `あり`
- `ConciergeThread.recommendations`: `あり`
- `ConciergeRecommendationLog.need_tags`: `あり`
- 抽出件数: `100`

## 直近相談ログ一覧

| # | 相談文 | need_tags | matched_need_tags | history_theme |
|---:|---|---|---|---|
| 1 | お金が欲しい | money | money | 勝負 / 再出発 |
| 2 | 年収を上げたい | - | - | 勝負 / 縁 |
| 3 | もっと稼ぎたい | - | - | 勝負 / 縁 |
| 4 | お金が欲しい | money | money | 勝負 / 再出発 |
| 5 | 会社に縛られたくない | - | - | 勝負 / 縁 |
| 6 | 好きな仕事をしたい | career | career | 勝負 / 学び |
| 7 | 自由に働きたい | - | - | 勝負 / 縁 |
| 8 | 経営者になりたい | money | money | 勝負 / 再出発 |
| 9 | 事業を大きくしたい | money | money | 勝負 / 再出発 |
| 10 | 売上を増やしたい | money | money | 勝負 / 再出発 |
| 11 | 収入を増やしたい | money | money | 勝負 / 再出発 |
| 12 | お金を増やしたい | money | money | 勝負 / 再出発 |
| 13 | 事業を大きくしたい | money | money | 勝負 / 再出発 |
| 14 | 会社を作りたい | - | - | 勝負 / 縁 |
| 15 | 起業したい | career | career | 勝負 / 学び |
| 16 | 副業したい | - | - | 勝負 / 縁 |
| 17 | 独立したい | career | career | 勝負 / 学び |
| 18 | 独立したい | career | career | 勝負 / 学び |
| 19 | 今の仕事を辞めたい | career | career | 勝負 / 学び |
| 20 | 転職したい | career | career | 勝負 / 学び |
| 21 | 収入を増やしたい | money | money | 勝負 / 再出発 |
| 22 | お金の不安がある | money / mental | money / mental | 勝負 / 再出発 |
| 23 | 金運を上げたい | money | money | 勝負 / 再出発 |
| 24 | 金運を上げたい | money | money | 勝負 / 再出発 |
| 25 | 金運 | money | money | 勝負 / 再出発 |
| 26 | 最近ちょっと疲れていて、落ち着ける神社がいいです | mental / rest | mental / rest | 勝負 / 縁 / 守り |
| 27 | 最近ちょっと疲れていて、落ち着ける神社がいいです | mental / rest | mental / rest | 勝負 / 縁 / 守り |
| 28 | 最近ちょっと疲れていて、落ち着ける神社がいいです | mental / rest | mental / rest | 勝負 / 縁 / 守り |
| 29 | 人が少なくて静かな場所でお参りしたいです | rest | rest | 縁 / 勝負 |
| 30 | 気持ちを切り替えて前向きになれる参拝がしたいです | - | - | 勝負 / 縁 / 再出発 |
| 31 | 最近ちょっと疲れていて、落ち着ける神社がいいです | mental / rest | mental / rest | 勝負 / 縁 / 守り |
| 32 | 人が少なくて静かな場所でお参りしたいです | rest | - | 勝負 / 守り |
| 33 | 気持ちを切り替えて前向きになれる参拝がしたいです | - | - | 勝負 / 再出発 |
| 34 | 最近ちょっと疲れていて、落ち着ける神社がいいです | mental / rest | mental | 勝負 / 守り |
| 35 | 最近ちょっと疲れていて、落ち着ける神社がいいです | mental / rest | mental | 勝負 / 守り |
| 36 | 最近ちょっと疲れていて、落ち着ける神社がいいです | mental / rest | mental | 勝負 / 守り |
| 37 | 人が少なくて静かな場所でお参りしたいです | rest | - | - |
| 38 | 最近ちょっと疲れていて、落ち着ける神社がいいです | mental / rest | mental | - |
| 39 | 気持ちを切り替えて前向きになれる参拝がしたいです | - | - | - |
| 40 | 最近ちょっと疲れていて、落ち着ける神社がいいです | mental / rest | mental | - |
| 41 | 気持ちを切り替えて前向きになれる参拝がしたいです | - | - | - |
| 42 | 最近ちょっと疲れていて、落ち着ける神社がいいです | mental / rest | mental | - |
| 43 | 最近ちょっと疲れていて、落ち着ける神社がいいです | mental / rest | mental | - |
| 44 | 最近ちょっと疲れていて、落ち着ける神社がいいです | mental / rest | mental | - |
| 45 | 最近ちょっと疲れていて、落ち着ける神社がいいです | mental / rest | mental | - |
| 46 | 最近ちょっと疲れていて、落ち着ける神社がいいです | mental / rest | mental | - |
| 47 | 最近ちょっと疲れていて、落ち着ける神社がいいです | mental / rest | mental | - |
| 48 | 最近ちょっと疲れていて、落ち着ける神社がいいです | mental / rest | mental | - |
| 49 | 最近ちょっと疲れていて、落ち着ける神社がいいです | mental / rest | mental | - |
| 50 | 気持ちを切り替えて前向きになれる参拝がしたいです | - | - | - |
| 51 | 気持ちを切り替えて前向きになれる参拝がしたいです | - | - | - |
| 52 | 最近ちょっと疲れていて、落ち着ける神社がいいです | mental / rest | mental | - |
| 53 | 最近ちょっと疲れていて、落ち着ける神社がいいです | mental / rest | mental | - |
| 54 | 最近ちょっと疲れていて、落ち着ける神社がいいです | mental / rest | mental | - |
| 55 | 最近ちょっと疲れていて、落ち着ける神社がいいです | mental / rest | mental | - |
| 56 | 最近ちょっと疲れていて、落ち着ける神社がいいです | mental / rest | mental | - |
| 57 | 金運を上げたい | money | money | - |
| 58 | 仕事運を上げたい | career | career | - |
| 59 | 最近ちょっと疲れていて、落ち着ける神社がいいです | mental / rest | mental | - |
| 60 | 人が少なくて静かな場所でお参りしたいです | rest | - | - |
| 61 | 人が少なくて静かな場所でお参りしたいです | rest | - | - |
| 62 | 気持ちを切り替えて前向きになれる参拝がしたいです | - | - | - |
| 63 | 気持ちを切り替えて前向きになれる参拝がしたいです | - | - | - |
| 64 | 最近ちょっと疲れていて、落ち着ける神社がいいです | mental / rest | mental | - |
| 65 | 人が少なくて静かな場所でお参りしたいです | rest | - | - |
| 66 | 気持ちを切り替えて前向きになれる参拝がしたいです | - | - | - |
| 67 | 最近ちょっと疲れていて、落ち着ける神社がいいです | mental / rest | mental | - |
| 68 | 最近ちょっと疲れていて、落ち着ける神社がいいです | mental / rest | mental | - |
| 69 | 気持ちを切り替えて前向きになれる参拝がしたいです | - | - | - |
| 70 | 最近ちょっと疲れていて、落ち着ける神社がいいです | mental / rest | mental | - |
| 71 | 最近ちょっと疲れていて、落ち着ける神社がいいです | mental / rest | mental | - |
| 72 | 人が少なくて静かな場所でお参りしたいです | rest | - | - |
| 73 | 人が少なくて静かな場所でお参りしたいです | rest | - | - |
| 74 | 人が少なくて静かな場所でお参りしたいです | rest | - | - |
| 75 | 人が少なくて静かな場所でお参りしたいです | rest | - | - |
| 76 | 人が少なくて静かな場所でお参りしたいです | rest | - | - |
| 77 | 人が少なくて静かな場所でお参りしたいです | rest | - | - |
| 78 | 人が少なくて静かな場所でお参りしたいです | rest | - | - |
| 79 | 自然を感じながら参拝したい | rest | - | - |
| 80 | 合格祈願をしたい | study | study | - |
| 81 | 合格祈願をしたい | study | study | - |
| 82 | 仕事運を上げたい | career | career | - |
| 83 | 気持ちを切り替えたい | - | - | - |
| 84 | 自然を感じながら参拝したい | rest | - | - |
| 85 | 合格祈願をしたい | study | study | - |
| 86 | 静かな場所で参拝したい | rest | - | - |
| 87 | 仕事運を上げたい | career | career | - |
| 88 | 静かな場所で参拝したい | rest | - | - |
| 89 | 自然を感じながら参拝したい | rest | - | - |
| 90 | 気持ちを切り替えたい | - | - | - |
| 91 | 自然を感じながら参拝したい | rest | - | - |
| 92 | 合格祈願をしたい | study | study | - |
| 93 | 合格祈願をしたい | study | study | - |
| 94 | 気持ちを切り替えたい | - | - | - |
| 95 | 自然を感じながら参拝したい | rest | - | - |
| 96 | 自然を感じながら参拝したい | rest | - | - |
| 97 | 合格祈願をしたい | study | study | - |
| 98 | 気持ちを切り替えたい | - | - | - |
| 99 | 自然を感じながら参拝したい | rest | - | - |
| 100 | 合格祈願をしたい | study | study | - |

## consultation_axis候補欄

LLMクラスタ分析前のため未確定。現時点では候補を固定せず、下記の観点で後続分析する。

| 仮axis | 根拠相談文 | 関連need_tags | コメント |
|---|---|---|---|
| money_growth | お金が欲しい / 収入を増やしたい / 年収を上げたい / もっと稼ぎたい / 売上を増やしたい | money | 金運ではなく、収入・売上・経済成長の相談 |
| career_change | 転職したい / 今の仕事を辞めたい / 好きな仕事をしたい / 仕事運を上げたい | career | 仕事そのものの転機 |
| independence | 独立したい / 起業したい / 副業したい / 会社を作りたい / 会社に縛られたくない / 自由に働きたい | career / money | 自由・自立・働き方の相談 |
| rest_healing | 最近疲れている / 落ち着ける神社 / 静かな場所 / 人が少ない場所 | mental / rest | 回復・静けさ・落ち着き |
| restart_mindset | 気持ちを切り替えたい / 前向きになりたい | 未取得多め | need_tagsで拾えていない。重要な抜け |
| nature_reset | 自然を感じながら参拝したい | rest | 場所体験・環境条件寄り |
| study_success | 合格祈願をしたい | study | かなり明確 |

## Consultation Axis Taxonomy

### 目的

`consultation_axis` は、`need_tags` より一段深い相談意図の正規化レイヤーとして扱う。

`need_tags` は「願い・ご利益カテゴリ」を表し、`consultation_axis` は「ユーザーがなぜそれを求めているか」を表す。

```text
相談文
↓
consultation_axis
↓
need_tags
↓
recommendation
```

### Axis定義

| axis | 定義 | 代表入力 | primary need_tags | 補助 need_tags |
|---|---|---|---|---|
| money_growth | 収入・年収・売上・事業拡大など、経済的な成長や増加を求める相談。単なる金運祈願ではなく、稼ぐ力や経済活動の前進に関する意図を扱う。 | お金が欲しい / 収入を増やしたい / 年収を上げたい / もっと稼ぎたい / 売上を増やしたい | money | career / courage |
| career_change | 転職・退職・仕事運・好きな仕事など、仕事そのものの方向転換や職業選択に関する相談。 | 転職したい / 今の仕事を辞めたい / 好きな仕事をしたい / 仕事運を上げたい | career | courage / mental |
| independence | 独立・起業・副業・自由な働き方・組織から離れることに関する相談。収入よりも、自立や裁量の獲得を主目的とする。 | 独立したい / 起業したい / 副業したい / 会社を作りたい / 会社に縛られたくない / 自由に働きたい | career | money / courage |
| rest_healing | 疲労・落ち着き・静けさ・人の少なさなど、回復や安心できる参拝体験を求める相談。 | 最近疲れている / 落ち着ける神社 / 静かな場所 / 人が少ない場所 | rest | mental |
| restart_mindset | 気持ちの切り替え・前向きさ・再出発など、心理的な転換点を求める相談。現状ログでは need_tags 未取得が多く、補強対象。 | 気持ちを切り替えたい / 前向きになりたい / 気持ちを切り替えて前向きになれる参拝がしたい | mental | courage / rest |
| nature_reset | 自然・緑・開放感など、場所体験を通じたリセットを求める相談。願望というより参拝環境の希望に近い。 | 自然を感じながら参拝したい | rest | mental |
| study_success | 合格祈願・資格試験・学業成就など、学習や試験の成果を求める相談。 | 合格祈願をしたい | study | focus / courage |
| other | 上記に分類できない相談。taxonomy確定前の逃げ道として使い、分類不能ケースを後続監査対象にする。 | 未分類相談 | - | - |

### axis → need_tag マッピング

| axis | need_tags | 備考 |
|---|---|---|
| money_growth | money / career / courage | moneyを主軸にしつつ、収入行動・挑戦文脈を補助する |
| career_change | career / courage / mental | 仕事の転機を主軸にし、決断不安を補助する |
| independence | career / money / courage | 自立・起業・副業はcareerだけに潰さず、moneyとcourageも持たせる |
| rest_healing | rest / mental | 回復体験を主軸にし、心理的負荷も扱う |
| restart_mindset | mental / courage / rest | 現状では未取得が多いため、need_tags補強候補 |
| nature_reset | rest / mental | 場所体験としての休息を扱う |
| study_success | study / focus / courage | studyを主軸にし、集中・継続・挑戦を補助する |
| other | - | 未分類として保存し、後続監査で見直す |

### axis判定ルール

| 優先順 | 条件 | axis |
|---:|---|---|
| 1 | 合格 / 試験 / 資格 / 受験 / 学業 | study_success |
| 2 | 独立 / 起業 / 副業 / 会社を作りたい / 自由に働きたい / 会社に縛られたくない / フリーランス | independence |
| 3 | 転職 / 仕事を辞めたい / 好きな仕事 / 天職 / 仕事運 | career_change |
| 4 | 年収 / 収入 / 稼ぎたい / 売上 / 収益 / お金を増やしたい / 金運 | money_growth |
| 5 | 気持ちを切り替えたい / 前向き / 再出発 / 流れを変えたい | restart_mindset |
| 6 | 疲れ / 落ち着きたい / 静か / 人が少ない / 休みたい | rest_healing |
| 7 | 自然 / 緑 / 開放感 / 散歩 / 空気 | nature_reset |
| 8 | どれにも該当しない | other |

### 注意点

- `consultation_axis` は神社側の `history_theme` とは分離する。
- `history_theme` は神社側の文脈、`consultation_axis` はユーザー側の相談軸として扱う。
- `need_tags` を削除するのではなく、`consultation_axis` から補助的に接続する。
- taxonomyは確定ではなく、今後の相談ログ増加に応じて更新する。

## 次にLLMクラスタ分析で見る観点

- 相談文が表す主目的: 仕事、金運、恋愛、人間関係、学業、健康、厄除け、移動安全など。
- 感情状態: 不安、疲労、迷い、背中を押してほしい、落ち着きたいなど。
- 時間軸: 今すぐの解決、節目、再出発、継続的な改善。
- 行動意図: 参拝先探し、気持ちの整理、意思決定、守り・浄化、縁づくり。
- 既存 `need_tags` と相談文のズレ: タグ化できていない自然文のまとまり。
- `history_theme` との混同リスク: 神社側の文脈タグとユーザー相談軸を分離できるか。

## 再生成コマンド

```bash
cd backend && ../.venv/bin/python manage.py export_consultation_axis_discovery --limit 100 --output ../docs/analytics/consultation-axis-discovery.md
```
