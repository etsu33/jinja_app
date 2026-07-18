# Deprecated Files Cleanup Audit

## Purpose

Phase7実装前に、Git管理されている一時ファイル・旧ファイル・生成物の混入状況を確認し、安全に削除できる対象を整理する。

## Result

削除対象は以下の2ファイルとする。

- backend/tmp_debug_api_concierge_flow.py
- backend/tmp_debug_simple.py

これらは一時デバッグ用スクリプトであり、実装コードからの参照は確認されなかった。

## Kept Files

以下は削除しない。

- migrations配下のlegacy/drop/cache関連ファイル
- backend/shrine_project/cache_keys.py
- backend/temples/api/views/place_cache.py
- backend/temples/services/place_cache_upsert.py
- backend/temples/tests/test_places_cache_and_throttle.py
- backend/temples/tests/test_places_service_cache.py
- apps/web/src/fonts配下のフォント
- apps/mobile/assets/placeholder.png

## Deferred

以下は別PRで判断する。

- backend/temples/_deprecated/
- apps/web/src/features/concierge/components/legacy/

---

## 後続対応

`backend/temples/_deprecated/`は、後続のDeadコード削除PRで参照0件を再確認した上で削除した。

削除前後でPackage Import Sweepを実行し、削除後もAPI URL、REST Framework設定およびSerializerのImportテストが成功することを確認した。

`apps/web/src/features/concierge/components/legacy/`については、本対応の対象外であり、引き続き別PRで扱う。
