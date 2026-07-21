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

import { buildDerivedProfile, buildDirectionProfile } from "../profile";
import { useProfileStore } from "../../store/profileStore";

const STORAGE_NAME = "kamimusubi:mobile:profile:v1";

function resetInMemoryState() {
  useProfileStore.setState({
    userProfile: {},
    derivedProfile: buildDerivedProfile({}),
    directionProfile: buildDirectionProfile({}),
  });
}

beforeEach(async () => {
  asyncStorage.values.clear();
  vi.clearAllMocks();
  resetInMemoryState();
  await useProfileStore.persist.rehydrate();
});

describe("profileStore persistence", () => {
  it("uses the existing empty profile as its initial state when storage has no value", () => {
    const state = useProfileStore.getState();

    expect(state.userProfile).toEqual({});
    expect(state.derivedProfile).toEqual(buildDerivedProfile({}));
    expect(state.directionProfile).toEqual(buildDirectionProfile({}));
  });

  it("persists every user-entered profile field without functions or derived values", async () => {
    const state = useProfileStore.getState();
    state.setBirthday("1990-04-01");
    state.setBirthTime("08:30");
    state.setBirthPlace("東京都");
    state.setWorshipStyle("朝参り");

    await vi.waitFor(() => expect(asyncStorage.setItem).toHaveBeenCalled());

    const saved = JSON.parse(asyncStorage.values.get(STORAGE_NAME) ?? "null");
    expect(saved).toEqual({
      state: {
        userProfile: {
          birthday: "1990-04-01",
          birthTime: "08:30",
          birthPlace: "東京都",
          worshipStyle: "朝参り",
        },
      },
      version: 1,
    });
  });

  it("rehydrates the saved profile and recomputes its derived profiles", async () => {
    const userProfile = {
      birthday: "1984-05-15",
      birthTime: "12:15",
      birthPlace: "京都府",
      worshipStyle: "夕参り",
    };
    resetInMemoryState();
    asyncStorage.values.set(STORAGE_NAME, JSON.stringify({ state: { userProfile }, version: 1 }));

    await useProfileStore.persist.rehydrate();

    const state = useProfileStore.getState();
    expect(state.userProfile).toEqual(userProfile);
    expect(state.derivedProfile).toEqual(buildDerivedProfile(userProfile));
    expect(state.directionProfile).toEqual(buildDirectionProfile(userProfile));
    expect(state.setBirthday).toBeTypeOf("function");
  });

  it("keeps the initial profile usable when persisted JSON is corrupted", async () => {
    resetInMemoryState();
    asyncStorage.values.set(STORAGE_NAME, "not-json");

    await useProfileStore.persist.rehydrate();

    expect(useProfileStore.getState().userProfile).toEqual({});
    expect(() => useProfileStore.getState().setBirthPlace("大阪府")).not.toThrow();
    expect(useProfileStore.getState().userProfile.birthPlace).toBe("大阪府");
  });

  it("keeps profile setters usable when persistence fails", async () => {
    asyncStorage.setItem.mockRejectedValueOnce(new Error("storage unavailable"));

    expect(() => useProfileStore.getState().setBirthday("2000-01-01")).not.toThrow();
    await Promise.resolve();

    expect(useProfileStore.getState().userProfile.birthday).toBe("2000-01-01");
    expect(useProfileStore.getState().derivedProfile).toEqual(buildDerivedProfile({ birthday: "2000-01-01" }));
  });
});
