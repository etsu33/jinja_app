import type { DerivedProfile, UserProfile } from "../types/profile";

export type ConciergeContext = {
  userProfile?: UserProfile;
  derivedProfile?: DerivedProfile;
};
