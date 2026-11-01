# Google Places API Cost Audit — 2026-11-01

> **Status: Point-in-time evidence recorded / Final billing PENDING**
>
> 本記録は2026年11月1日時点のGoogle Cloud画面で確認した情報を固定するもの。APIキーの秘密値や本番環境変数の値は記録しない。

## 確認結果

| 項目 | 値 | 判定 |
| --- | --- | --- |
| Project | `strong-imagery-467113-s5` | CONFIRMED |
| API | Places API (Legacy) | CONFIRMED |
| Requests (last 7 days) | **3** | CONFIRMED |
| API Key 2 Usage | **UNKNOWN** | NOT VERIFIED |
| API Key 3 Usage | **UNKNOWN** | NOT VERIFIED |
| Posted Cost (2026-11-01) | **JPY 0** | CONFIRMED AS DISPLAYED |
| Final Billing | **PENDING** | NOT FINAL |
| Legacy SKU Breakdown | **PENDING** | NO ITEMIZED COST DISPLAYED |
| Budget Alert | **JPY 1,000/month** | CONFIGURED |
| Next Billing Review | **2026-11-04** | SCHEDULED REVIEW |

## 事実と制約

- Google Maps Platform Metricsで、`strong-imagery-467113-s5` の Places API (Legacy) の直近7日間リクエスト数 **3件** を確認。
- Google Cloud Billingの `My Billing Account` で、対象プロジェクトを **My Project（`strong-imagery-467113-s5`）のみ** に絞った2026年11月1日時点の計上済み費用表示は **JPY 0**。
- 同時点の請求レポートにはLegacy APIのSKU別明細が表示されていない。請求反映に遅延があるため、**JPY 0を確定請求額とは扱わない**。
- Google Maps Platformの認証情報別フィルター／グループ化を操作できず、APIキー2とAPIキー3の使用件数はどちらも **UNKNOWN**。実際に使用された本番キーもこの証拠だけでは特定できない。
- 直近7日間のリクエスト数は10月分を含む可能性があり、3件すべてを11月の費用に帰属させることはできない。
- 月額予算JPY 1,000は通知のための予算であり、請求の強制停止上限ではない。

## Conclusion

Usage is measured, but key-level attribution remains unverified. Posted billing is not final.

## Follow-up

- [ ] 2026-11-04に、`My Billing Account` → `strong-imagery-467113-s5` → 2026年11月の請求レポートでPlaces API (Legacy)のSKU別費用を再確認する。
- [ ] 請求データが未反映であれば、`PENDING` を維持し、確認日を追記する。
- [ ] APIキー2・3の件数は根拠が得られるまで `UNKNOWN` を維持する。

本監査は読み取り専用。APIキー、Google Cloud、Render、Vercel、および本番DBの設定変更なし。
