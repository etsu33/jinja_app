> **Status: Reference**
>
> 本ドキュメントは、参拝後振り返り導線のFunnel KPI・PostHogダッシュボード設計を補足するReference文書である。
>
> Visit / Reflectionのイベント・保存責務は `docs/product/visit-reflection-flow.md` を正本とする。

# Reflection Funnel Dashboard

## Goal

参拝後の振り返り導線が実際に利用されているかを可視化する。

---

## Funnel

```text
shrine_detail_view
↓
visit_done
↓
reflection_prompt_view
↓
reflection_saved
```

---

## KPI

### 1. shrine_detail_view → visit_done率

```text
visit_done / shrine_detail_view
```

目的：
神社詳細を見たユーザーが実際に参拝完了を記録した割合。

---

### 2. visit_done → reflection_prompt_view率

```text
reflection_prompt_view / visit_done
```

目的：
参拝完了後に振り返り導線が正常表示されているか確認する。

---

### 3. reflection_prompt_view → reflection_saved率

```text
reflection_saved / reflection_prompt_view
```

目的：
振り返り入力完了率を確認する。

最重要指標。

---

## Breakdown

### historyTheme別

確認項目：

- reflection_saved数
- reflection_saved率
- historyTheme別CVR

例：

- 静寂
- 再出発
- 縁
- 復興
- 学び

---

### shrine別

確認項目：

- shrine別 reflection_saved数
- shrine別 reflection_saved率
- 上位神社ランキング

---

## PostHog Dashboard

### Funnel Widget

```text
shrine_detail_view
→ visit_done
→ reflection_prompt_view
→ reflection_saved
```

---

### Insight Widget

```text
Event: reflection_saved
Breakdown: historyTheme
```

---

### Insight Widget

```text
Event: reflection_saved
Breakdown: shrineId
```

---

## Observation Period

初回計測期間：

```text
7日間
```

確認事項：

- どこで離脱するか
- どのhistoryThemeで振り返りされるか
- どの神社で振り返りされるか

---

## Success Criteria

- dashboard作成完了
- funnel表示確認
- historyTheme breakdown確認
- shrine breakdown確認
- 1週間観測開始

---

## 関連ドキュメント

- `docs/product/README.md`
- `docs/product/visit-reflection-flow.md`
- `docs/product/history-theme-taxonomy.md`

---

## 更新ルール

- 本書はReflection Funnelのダッシュボード設計・KPI定義のみを管理する。
- Visit / ReflectionのEvent名・Payload契約は本書で重複管理しない。
- historyThemeのカテゴリ名称は `docs/product/history-theme-taxonomy.md` の定義に従う。
- ダッシュボード構成またはKPI定義が変更された場合のみ更新する。
- 実装進捗、作業履歴は本書へ記載しない。
