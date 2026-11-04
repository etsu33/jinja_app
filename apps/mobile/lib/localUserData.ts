import AsyncStorage from "@react-native-async-storage/async-storage";

import { KEY_ACCESS, KEY_REFRESH } from "./authTokens";
import { LEGACY_BIRTHDAY_STORAGE_NAME } from "./profileMigration";
import { keys as storageKeys } from "./storage";
import { PROFILE_STORAGE_NAME, useProfileStore } from "../store/profileStore";

/**
 * 退会時に端末から消去する AsyncStorage のキー一覧。
 *
 * - 認証トークン（lib/authTokens.ts）
 * - 御朱印・お気に入り・参拝回数・プロフィール・最近見た神社（lib/storage.ts の keys）
 * - プロフィールストア（store/profileStore.ts の zustand persist）
 * - 旧形式の生年月日（lib/profileMigration.ts）
 *
 * 相談履歴・振り返り・参拝記録・お気に入り(サーバー側)は lib/consultationHistory.ts 等が
 * API から都度取得しており、端末には保存していない。
 * PostHog の匿名ID等（lib/posthogAnalyticsProvider.ts）はSDKが管理するキーのため対象外。
 *
 * AsyncStorage を使うファイルを追加した場合は、
 * lib/__tests__/localUserData.test.ts の網羅テストが失敗するので、ここも合わせて更新すること。
 */
export function getLocalUserDataStorageKeys(): string[] {
  return [
    KEY_ACCESS,
    KEY_REFRESH,
    ...Object.values(storageKeys),
    PROFILE_STORAGE_NAME,
    LEGACY_BIRTHDAY_STORAGE_NAME,
  ];
}

/** 端末内の利用者データを消去する。メモリ上のプロフィールも初期化する。 */
export async function clearLocalUserData(): Promise<void> {
  useProfileStore.getState().resetProfile();
  await AsyncStorage.multiRemove(getLocalUserDataStorageKeys());
}
