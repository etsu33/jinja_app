import { beforeEach, describe, expect, it, vi } from "vitest";

const asyncStorage = vi.hoisted(() => {
  const values = new Map<string, string>();
  return {
    values,
    getItem: vi.fn(async (key: string) => values.get(key) ?? null),
    setItem: vi.fn(async (key: string, value: string) => {
      values.set(key, value);
    }),
    removeItem: vi.fn(async (key: string) => {
      values.delete(key);
    }),
  };
});

vi.mock("@react-native-async-storage/async-storage", () => ({
  default: asyncStorage,
}));

import {
  LEGACY_BIRTHDAY_STORAGE_NAME,
  migrateLegacyBirthdayIfNeeded,
} from "../profileMigration";

const PROFILE_STORAGE_NAME = "kamimusubi:mobile:profile:v1";

function migrate(userProfile: { birthday?: string; birthTime?: string; birthPlace?: string; worshipStyle?: string }) {
  const setBirthday = vi.fn();
  const result = migrateLegacyBirthdayIfNeeded({
    userProfile,
    setBirthday,
    profileStorageName: PROFILE_STORAGE_NAME,
    profileStorageVersion: 1,
  });
  return { result, setBirthday };
}

beforeEach(() => {
  asyncStorage.values.clear();
  vi.clearAllMocks();
});

describe("legacy birthday migration", () => {
  it("migrates a valid legacy birthday when the profile birthday is empty", async () => {
    asyncStorage.values.set(LEGACY_BIRTHDAY_STORAGE_NAME, "1984-05-15");

    const { result, setBirthday } = migrate({ birthPlace: "京都府" });

    await expect(result).resolves.toBe("migrated");
    expect(setBirthday).toHaveBeenCalledWith("1984-05-15");
    expect(asyncStorage.values.has(LEGACY_BIRTHDAY_STORAGE_NAME)).toBe(false);
    expect(JSON.parse(asyncStorage.values.get(PROFILE_STORAGE_NAME) ?? "null")).toEqual({
      state: { userProfile: { birthday: "1984-05-15", birthPlace: "京都府" } },
      version: 1,
    });
  });

  it("never overwrites an existing profile birthday", async () => {
    asyncStorage.values.set(LEGACY_BIRTHDAY_STORAGE_NAME, "1984-05-15");

    const { result, setBirthday } = migrate({ birthday: "1990-01-01" });

    await expect(result).resolves.toBe("skipped_existing");
    expect(setBirthday).not.toHaveBeenCalled();
    expect(asyncStorage.values.get(LEGACY_BIRTHDAY_STORAGE_NAME)).toBe("1984-05-15");
  });

  it("does nothing when the legacy value is missing or empty", async () => {
    await expect(migrate({}).result).resolves.toBe("skipped_missing");

    asyncStorage.values.set(LEGACY_BIRTHDAY_STORAGE_NAME, "   ");
    await expect(migrate({}).result).resolves.toBe("skipped_missing");
  });

  it("does not migrate an invalid legacy value", async () => {
    asyncStorage.values.set(LEGACY_BIRTHDAY_STORAGE_NAME, "not-a-birthday");

    const { result, setBirthday } = migrate({});

    await expect(result).resolves.toBe("skipped_invalid");
    expect(setBirthday).not.toHaveBeenCalled();
    expect(asyncStorage.values.get(LEGACY_BIRTHDAY_STORAGE_NAME)).toBe("not-a-birthday");
  });

  it("continues initialization when reading the legacy value fails", async () => {
    asyncStorage.getItem.mockRejectedValueOnce(new Error("read failed"));

    await expect(migrate({}).result).resolves.toBe("failed");
  });

  it("keeps the legacy value and state unchanged when the new profile cannot be saved", async () => {
    asyncStorage.values.set(LEGACY_BIRTHDAY_STORAGE_NAME, "1984-05-15");
    asyncStorage.setItem.mockRejectedValueOnce(new Error("write failed"));

    const { result, setBirthday } = migrate({});

    await expect(result).resolves.toBe("failed");
    expect(setBirthday).not.toHaveBeenCalled();
    expect(asyncStorage.values.get(LEGACY_BIRTHDAY_STORAGE_NAME)).toBe("1984-05-15");
    expect(asyncStorage.removeItem).not.toHaveBeenCalled();
  });

  it("is idempotent when run repeatedly", async () => {
    asyncStorage.values.set(LEGACY_BIRTHDAY_STORAGE_NAME, "1984-05-15");
    const first = migrate({});
    await expect(first.result).resolves.toBe("migrated");

    const second = migrate({ birthday: "1984-05-15" });
    await expect(second.result).resolves.toBe("skipped_existing");
    expect(second.setBirthday).not.toHaveBeenCalled();
  });
});
