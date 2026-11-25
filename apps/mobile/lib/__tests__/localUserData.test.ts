import { readdirSync, readFileSync, statSync } from "node:fs";
import { dirname, join, relative, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { beforeEach, describe, expect, it, vi } from "vitest";

const multiRemoveMock = vi.fn();
const resetProfileMock = vi.fn();

vi.mock("@react-native-async-storage/async-storage", () => ({
  default: {
    getItem: vi.fn(),
    setItem: vi.fn(),
    removeItem: vi.fn(),
    multiRemove: (...args: unknown[]) => multiRemoveMock(...args),
  },
}));

vi.mock("../../store/profileStore", () => ({
  PROFILE_STORAGE_NAME: "kamimusubi:mobile:profile:v1",
  useProfileStore: { getState: () => ({ resetProfile: resetProfileMock }) },
}));

import { KEY_ACCESS, KEY_REFRESH } from "../authTokens";
import { LEGACY_BIRTHDAY_STORAGE_NAME } from "../profileMigration";
import { keys as storageKeys } from "../storage";
import { clearLocalUserData, getLocalUserDataStorageKeys } from "../localUserData";

const mobileRoot = resolve(dirname(fileURLToPath(import.meta.url)), "../..");

function listSourceFiles(dir: string): string[] {
  return readdirSync(dir).flatMap((name) => {
    const full = join(dir, name);
    if (name === "__tests__" || name === "node_modules") return [];
    if (statSync(full).isDirectory()) return listSourceFiles(full);
    return /\.(ts|tsx)$/.test(name) ? [full] : [];
  });
}

describe("getLocalUserDataStorageKeys", () => {
  it("端末内の利用者データのキーを網羅する", () => {
    const result = getLocalUserDataStorageKeys();

    expect(result).toEqual(
      expect.arrayContaining([
        KEY_ACCESS,
        KEY_REFRESH,
        storageKeys.stamps,
        storageKeys.favorites,
        storageKeys.visits,
        storageKeys.profile,
        storageKeys.recents,
        "kamimusubi:mobile:profile:v1",
        LEGACY_BIRTHDAY_STORAGE_NAME,
      ]),
    );
    // lib/storage.ts の keys に追加されたキーも漏れなく含む
    for (const key of Object.values(storageKeys)) {
      expect(result).toContain(key);
    }
    expect(new Set(result).size).toBe(result.length);
  });

  it("AsyncStorageを使うファイルが一覧の対象として把握済みである", () => {
    // 新しくAsyncStorageを使うファイルが増えたらこのテストが失敗する。
    // そのファイルのキーを getLocalUserDataStorageKeys に追加するか、対象外の理由を明記してから更新すること。
    const users = ["app", "components", "lib", "store"]
      .flatMap((dir) => listSourceFiles(resolve(mobileRoot, dir)))
      .filter((file) => readFileSync(file, "utf8").includes("@react-native-async-storage/async-storage"))
      .map((file) => relative(mobileRoot, file))
      .sort();

    expect(users).toEqual([
      "lib/authTokens.ts", // KEY_ACCESS / KEY_REFRESH
      "lib/localUserData.ts", // 消去処理そのもの
      "lib/posthogAnalyticsProvider.ts", // 対象外: PostHog SDKが管理する匿名IDなど
      "lib/profileMigration.ts", // LEGACY_BIRTHDAY_STORAGE_NAME
      "lib/storage.ts", // keys
      "store/profileStore.ts", // PROFILE_STORAGE_NAME
    ]);
  });
});

describe("clearLocalUserData", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("一覧のキーをAsyncStorageから消去し、メモリ上のプロフィールも初期化する", async () => {
    await clearLocalUserData();

    expect(resetProfileMock).toHaveBeenCalledTimes(1);
    expect(multiRemoveMock).toHaveBeenCalledWith(getLocalUserDataStorageKeys());
  });
});
