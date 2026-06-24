export type UserProfile = {
  birthday?: string;
  birthTime?: string;
  birthPlace?: string;
  worshipStyle?: string;
};

export type DerivedProfile = {
  kyusei?: string;
  gogyo?: string;
  lifePath?: string;
};

export type DirectionProfile = {
  luckyDirection?: string;
  source?: "placeholder" | "calculated";
};
