import AsyncStorage from "@react-native-async-storage/async-storage";

import type { UserProfile } from "../types/profile";

export const LEGACY_BIRTHDAY_STORAGE_NAME = "sanpai:profile:birthday";

const BIRTHDAY_PATTERN = /^\d{4}-\d{2}-\d{2}$/;

export type LegacyBirthdayMigrationResult =
  | "migrated"
  | "skipped_existing"
  | "skipped_missing"
  | "skipped_invalid"
  | "failed";

type LegacyBirthdayMigrationOptions = {
  userProfile: UserProfile;
  setBirthday: (value: string) => void;
  profileStorageName: string;
  profileStorageVersion: number;
};

export async function migrateLegacyBirthdayIfNeeded({
  userProfile,
  setBirthday,
  profileStorageName,
  profileStorageVersion,
}: LegacyBirthdayMigrationOptions): Promise<LegacyBirthdayMigrationResult> {
  if (typeof userProfile.birthday === "string" && userProfile.birthday.trim().length > 0) {
    return "skipped_existing";
  }

  let legacyBirthday: string | null;
  try {
    legacyBirthday = await AsyncStorage.getItem(LEGACY_BIRTHDAY_STORAGE_NAME);
  } catch {
    return "failed";
  }

  if (legacyBirthday === null) return "skipped_missing";

  const normalizedBirthday = legacyBirthday.trim();
  if (!normalizedBirthday) return "skipped_missing";
  if (!BIRTHDAY_PATTERN.test(normalizedBirthday)) return "skipped_invalid";

  const nextUserProfile = { ...userProfile, birthday: normalizedBirthday };
  try {
    await AsyncStorage.setItem(
      profileStorageName,
      JSON.stringify({ state: { userProfile: nextUserProfile }, version: profileStorageVersion }),
    );
  } catch {
    return "failed";
  }

  setBirthday(normalizedBirthday);

  try {
    await AsyncStorage.removeItem(LEGACY_BIRTHDAY_STORAGE_NAME);
  } catch {
    // The persisted profile is already authoritative; leaving the legacy value is safe.
  }

  return "migrated";
}
