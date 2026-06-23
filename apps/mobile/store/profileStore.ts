import { create } from "zustand";
import { buildDerivedProfile } from "../lib/profile";
import type { DerivedProfile, UserProfile } from "../types/profile";

type ProfileState = {
  userProfile: UserProfile;
  derivedProfile: DerivedProfile;
  setBirthday: (value: string) => void;
  setBirthTime: (value: string) => void;
  setBirthPlace: (value: string) => void;
  setWorshipStyle: (value: string) => void;
  resetProfile: () => void;
};

const initialUserProfile: UserProfile = {};

function derived(userProfile: UserProfile): DerivedProfile {
  return buildDerivedProfile(userProfile);
}

export const useProfileStore = create<ProfileState>((set) => ({
  userProfile: initialUserProfile,
  derivedProfile: derived(initialUserProfile),

  setBirthday: (value) =>
    set((s) => {
      const next = { ...s.userProfile, birthday: value };
      return { userProfile: next, derivedProfile: derived(next) };
    }),

  setBirthTime: (value) =>
    set((s) => {
      const next = { ...s.userProfile, birthTime: value };
      return { userProfile: next, derivedProfile: derived(next) };
    }),

  setBirthPlace: (value) =>
    set((s) => {
      const next = { ...s.userProfile, birthPlace: value };
      return { userProfile: next, derivedProfile: derived(next) };
    }),

  setWorshipStyle: (value) =>
    set((s) => {
      const next = { ...s.userProfile, worshipStyle: value };
      return { userProfile: next, derivedProfile: derived(next) };
    }),

  resetProfile: () =>
    set({ userProfile: initialUserProfile, derivedProfile: derived(initialUserProfile) }),
}));
