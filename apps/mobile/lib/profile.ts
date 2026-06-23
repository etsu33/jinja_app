import type { DerivedProfile, UserProfile } from "../types/profile";

export function buildDerivedProfile(_userProfile: UserProfile): DerivedProfile {
  return {
    kyusei: undefined,
    gogyo: undefined,
    lifePath: undefined,
  };
}
