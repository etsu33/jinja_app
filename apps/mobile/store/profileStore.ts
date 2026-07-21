import AsyncStorage from "@react-native-async-storage/async-storage";
import { create } from "zustand";
import { createJSONStorage, persist } from "zustand/middleware";
import { buildDerivedProfile, buildDirectionProfile } from "../lib/profile";
import type { DerivedProfile, DirectionProfile, UserProfile } from "../types/profile";

type ProfileState = {
  userProfile: UserProfile;
  derivedProfile: DerivedProfile;
  directionProfile: DirectionProfile;
  setBirthday: (value: string) => void;
  setBirthTime: (value: string) => void;
  setBirthPlace: (value: string) => void;
  setWorshipStyle: (value: string) => void;
  resetProfile: () => void;
};

const initialUserProfile: UserProfile = {};
const PROFILE_STORAGE_NAME = "kamimusubi:mobile:profile:v1";
const PROFILE_STORAGE_VERSION = 1;

function recompute(userProfile: UserProfile): { derivedProfile: DerivedProfile; directionProfile: DirectionProfile } {
  return {
    derivedProfile: buildDerivedProfile(userProfile),
    directionProfile: buildDirectionProfile(userProfile),
  };
}

const profileStorage = createJSONStorage(() => ({
  getItem: async (name: string) => {
    try {
      return await AsyncStorage.getItem(name);
    } catch {
      return null;
    }
  },
  setItem: async (name: string, value: string) => {
    try {
      await AsyncStorage.setItem(name, value);
    } catch {
      // Profile updates remain available in memory when persistence fails.
    }
  },
  removeItem: async (name: string) => {
    try {
      await AsyncStorage.removeItem(name);
    } catch {
      // A storage cleanup failure must not make the profile unusable.
    }
  },
}));

export const useProfileStore = create<ProfileState>()(
  persist(
    (set) => ({
      userProfile: initialUserProfile,
      ...recompute(initialUserProfile),

      setBirthday: (value) =>
        set((s) => {
          const next = { ...s.userProfile, birthday: value };
          return { userProfile: next, ...recompute(next) };
        }),

      setBirthTime: (value) =>
        set((s) => {
          const next = { ...s.userProfile, birthTime: value };
          return { userProfile: next, ...recompute(next) };
        }),

      setBirthPlace: (value) =>
        set((s) => {
          const next = { ...s.userProfile, birthPlace: value };
          return { userProfile: next, ...recompute(next) };
        }),

      setWorshipStyle: (value) =>
        set((s) => {
          const next = { ...s.userProfile, worshipStyle: value };
          return { userProfile: next, ...recompute(next) };
        }),

      resetProfile: () =>
        set({ userProfile: initialUserProfile, ...recompute(initialUserProfile) }),
    }),
    {
      name: PROFILE_STORAGE_NAME,
      storage: profileStorage,
      version: PROFILE_STORAGE_VERSION,
      partialize: (state) => ({ userProfile: state.userProfile }),
      merge: (persistedState, currentState) => {
        const userProfile = (persistedState as Pick<ProfileState, "userProfile"> | undefined)?.userProfile ??
          initialUserProfile;
        return { ...currentState, userProfile, ...recompute(userProfile) };
      },
    },
  ),
);
