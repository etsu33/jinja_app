import type { DerivedProfile, DirectionProfile, UserProfile } from "../types/profile";

export type ConciergeContext = {
  userProfile?: UserProfile;
  derivedProfile?: DerivedProfile;
  directionProfile?: DirectionProfile;
};
