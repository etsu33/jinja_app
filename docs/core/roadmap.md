# 🚀 開発ロードマップ（ポストMVP / ゼロコスト運用版）

本ドキュメントは **返金待ち期間〜β公開** までを **月額¥0** を前提に進めるためのロードマップです。
既存のロードマップを、無料プロバイダ運用・安全装置・低コストCIに合わせて更新しています。

---

## 🎯 ゴール

- **MVP完成を維持**しつつ、**無料API（OSM/Nominatim/ORS）＋強力なキャッシュ＋UI抑制**で開発を継続。
- 無料のCI/CDと観測性で**不具合を早期検出**、**課金事故を再発させない**。
- Web（Vercel無料）でβ配信 → 反応を見てモバイル展開を判断。

---

## 🧭 指針（Guidelines）

1. **USE_GOOGLE=false** を既定にし、Google API は明示的に切り替えたときだけ使用。
2. **キャッシュ・レート制限・サーキットブレーカー**を全外部APIに装備。
3. **フロントはデバウンス/スロットリング**を徹底（無駄な呼び出しゼロ）。
4. **テストは録画再生（VCR）**で実APIを叩かない。
5. **Secrets/鍵は常にローカルの .env**（`.env.example` のみ共有＆コミット）。

---

## 🗂 マイルストーン（チェックリスト）
### Recommendation Engine v2: score_v2 / behavior_signal 運用方針

#### Recommendation Score v2 の軸

主軸:

- 相談内容
- history_theme
- ご利益
- 神社固有文脈
- 神社タイプ

補助軸:

- 生年月日との相性
- astro_elements
- direction_bonus
- 行動ログ補正

将来モード:

- 吉方位入力UI
- 方位計算
- 九星接続
- 旅行モード連携

運用メモ:

- `direction_bonus` は Recommendation Score v2 の補助加点として扱う。
- `direction_bonus` は主軸を上書きしない。
- 吉方位入力UI / 方位計算 / 九星接続 / 旅行モード連携は MVP 外の将来モードとして隔離する。
- UI 文言では吉方位を主理由にせず、必要な場合も方位の補助要素として弱く扱う。

- [x] `score_v2` を推薦生成時点の評価スナップショットとして扱う
- [x] 保存済み thread の `score_v2` は再計算・再ランキングしない
- [x] `action_state` は現在DBにもとづく状態として表示する
- [x] `behavior_signal` は Favorite / Visit / ShrineReflection などの行動データを数値化する
- [x] `ranking_applied=false` の間は、`score_v2` を観測・説明用として扱う
- [ ] `behavior_signal` の分布を継続監査する
- [ ] `behavior_signal` を `score_total_ranked` に加算する重みを設計する
- [ ] 新規 recommendation 生成時のみ `ranking_applied=true` を有効化する
- [ ] 保存済み thread の履歴再現性と、現在の `action_state` 表示を両立する

運用方針:

- `score_v2`: 推薦生成時点の評価値。履歴の再現性を優先し、保存後は変更しない。
- `behavior_signal`: ユーザー行動を推薦改善に使うための観測値。初期対象は Favorite / Visit / ShrineReflection とする。
- `ranking_applied`: `score_v2` を実際の推薦順位へ反映したかを示すフラグ。true 化は新規推薦生成時のみ対象とする。
- `action_state`: saved / visited / reflected / none など、現在DBにもとづく状態表示。保存済み `score_v2` と一致しない場合がある。

次フェーズでは、`behavior_signal` を直接ランキングへ反映する前に、分布・偏り・重みの妥当性を確認する。

### 完了: Premium 体験境界の明文化

- [x] Premium 価値を Map/Search ではなく、パーソナル理由・相性・継続分析・保存/記録拡張に固定
- [x] free / premium の価値境界を `docs/pricing.md` に追加
- [x] Premium 体験境界を `docs/premium-experience.md` に追加
- [x] 神社詳細の情報レイヤを `docs/shrine-detail-layer.md` に追加

### 完了: auth-state-boundary の整理

- [x] `AuthProvider + /api/users/me/` を認証状態の source of truth に固定
- [x] `AuthState / ProfileState / ConciergeSessionState` を分離
- [x] 表示名優先順位を `sessionNickname > profile.nickname > あなた` に固定
- [x] `/auth/login?returnTo=...` `/auth/register?returnTo=...` を正規認証導線に統一
- [x] `/login` `/signup` を互換リダイレクトへ変更
- [x] `/concierge` は guest 利用可、保存系のみ auth required に整理
- [x] `/mypage` の未ログイン時表示を `AuthProvider` 起点に統一
- [x] 旧 `/login?next=` 参照を解消
- [x] `/mypage` 未ログイン時の `/api/users/me/` 発火を AuthProvider 由来の1回に抑制

### M0: 事故再発防止（今すぐ）

- [x] `.env` をコミット対象から除外（`.env.example` のみ共有）
- [x] **APIキーのローテーション**（Google / OpenAI）
- [x] **Google Geocoding/Places のクォータ**（per-day / per-minute / per-user）設定
- [x] **APIキー制限**（HTTPリファラ / IP / iOS/Android 証明書）

### M1: 無料プロバイダ切替（Backend）

- [ ] **Nominatim ジオコーダ**実装（30日キャッシュ・逆ジオ対応）
- [ ] **ORS ルーティング/Matrix**実装（徒歩・複数候補一括計算）
- [ ] フォールバック（通信不可時にスタブを返す）
- [ ] 自前 **RateLimiter（10〜20 req/min）** と **CircuitBreaker** 実装

### M2: UI 抑制（Frontend）

- [ ] 入力 **デバウンス 700ms**
- [ ] マップ移動 **停止後500msで1回だけ**発火
- [ ] 同一検索の **重複呼び出し禁止**（キーで排他）
- [ ] 結果ソート/ページングは **フロント側で** 処理

### M3: 無料CI/CD・観測性

- [ ] GitHub Actions（lint / test / build）※**実APIコール禁止**
- [ ] 失敗時のログ/アーティファクト保持
- [ ] Webは **Vercel（Hobby）** で自動デプロイ（スケルトンでも可）
- [ ] 予算監視ドキュメント（Budgets & Alerts 設定手順）

### M4: β公開に向けた品質担保

- [ ] E2E（検索→お気に入り→御朱印投稿→ルート表示）
- [ ] 空状態/エラーステート/スケルトンの整備
- [ ] パフォーマンス予算（LCP/CLS）と遅延読み込み

---

## 🔒 セキュリティ / コンプライアンス（最小構成）

- [ ] Dependabot（セキュリティアラート）を有効化
- [ ] 画像アップロードの **拡張子/MIME/サイズ** 検証と **EXIF除去**
- [ ] CORS/CSRF/JWT の基本設定見直し
- [ ] プライバシーポリシー/利用規約のドラフト

---

## 🧭 運用の安全装置（Hardening）

- **バックエンド**:
  - RateLimiter: 10〜20 req/min（環境変数で可変）
  - CircuitBreaker: 5連続失敗で 30s Open
  - リトライ最大1回・指数バックオフ（<=2s）
- **キャッシュ**:
  - ジオコード結果/ルート/Matrixは **30日** キャッシュ
  - キャッシュキーは入出力で決定（例: `dir:foot:lat1,lng1->lat2,lng2`）
- **UX制御**:
  - 入力 <3 文字では検索開始しない
  - 連続中はスピナーではなく **「入力を停止して検索」** 誘導

---

## 📦 リリース（ゼロコスト手順）

1. **Web版** を Vercel Hobby にデプロイ（環境変数は Vercel 側に登録）
2. βテスターを募集し、**利用ログ（匿名・集計）** を解析
3. 反応が良ければ **Expo（無料）** でモバイルに展開（審査費用が掛かる段で意思決定）

---

## 📈 KPI（無料運用で追うべき指標）

- 検索→ルート生成の **成功率（>= 99%）**
- 外部API呼び出し **1ユーザー1日あたり回数**
- キャッシュ **ヒット率（>= 70%）**
- エラー率（429/5xx）・平均レイテンシ

---

## 🧱 リスクと回避策

| リスク | 回避策 |
|---|---|
| 無料APIのレート制限 | RateLimiter＋キャッシュ＋UI抑制（最初に対策済み） |
| OSM精度のばらつき | 手動補正レイヤ/神社マスタで吸収 |
| 返金不成立 | コストゼロ設計で継続、Webのみでβ→判断 |

---

## 📌 ブランチ/PR計画（小さく安全に）

- `chore/secure-env-and-profiles`（完了）
- `feat/geocode-nominatim-cache`（Nominatim＋キャッシュ）
- `feat/routes-ors-osrm`（ORS/OSRM＋Matrix）
- `feat/ui-debounce-throttle`（UI抑制）
- `feat/rate-limit-circuit-breaker`（安全装置）
- `docs/cost-playbook`（運用ガイド）
- `chore/dependabot-updates`（依存の脆弱性解消）

---

## 🧾 付録：Short-term（運用に直結する小タスク）

- お気に入りカードに「＋DBへ取り込む」実装
- マイページの未保存お気に入り → 一括取込
- Places Details のキャッシュ/レート制御（※今後Google使用時のみ）


## Shrine Submission
- [x] docs で submission pipeline を固定
- [x] ShrineSubmission モデル作成
- [x] migration 作成・適用
- [x] review service 作成
- [x] approve / duplicate / reject の service 動作確認
- [x] Django admin 経由の approve / reject 確認
- [x] submission API 作成
- [x] duplicate_candidate 契約の正本を `docs/shrine-submission-flow.md` に固定
- [x] `docs/architecture.md` を責務境界 + 正本参照ハブに整理
- [x] `docs/auth-flow.md` に submission auth 復帰を追記
- [x] submission 投稿画面UIの最終化

### Phase 2: 投稿後体験と回遊
- [ ] duplicate_candidate 複数候補ケースのテスト追加
- [ ] duplicateCandidates UI の複数候補表示確認
- [ ] submission 後の search 復帰導線（`submitted=1&status=pending`）の確認
- [ ] pending状態の可視化（mypage / banner）
  - [ ] 投稿直後に受付バナーを表示（returnTo先で）
  - [ ] mypage に「審査中」セクションを追加
  - [ ] 投稿名・状態（pending）を表示
  - [ ] pending中は検索結果には表示しない（ghost表示なし）

### Phase 3: データ成長導線
- [ ] 投稿履歴の表示（mypage）
- [ ] 投稿→お気に入り / 回遊導線の強化
- [ ] 投稿貢献の可視化（ランキング / バッジなど）
