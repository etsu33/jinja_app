import { create } from "zustand";
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

function recompute(userProfile: UserProfile): { derivedProfile: DerivedProfile; directionProfile: DirectionProfile } {
  return {
    derivedProfile: buildDerivedProfile(userProfile),
    directionProfile: buildDirectionProfile(userProfile),
  };
}

export const useProfileStore = create<ProfileState>((set) => ({
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
}));
