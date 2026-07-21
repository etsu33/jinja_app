export type AuthStatus = "unknown" | "authenticated" | "guest";

export type AuthUser = {
  id: number;
  email?: string | null;
  username?: string | null;
  nickname?: string | null;
  birthday?: string | null;
  profile?: {
    nickname?: string | null;
    is_public?: boolean | null;
    birthday?: string | null;
    birth_time?: string | null;
    birth_place?: string | null;
    worship_style?: string | null;
  } | null;
};

export type AuthState = {
  status: AuthStatus;
  user: AuthUser | null;
  isHydrating: boolean;
};

export type ProfileState = {
  nickname: string | null;
  birthday: string | null;
};

export function toProfileState(user: AuthUser | null): ProfileState {
  return {
    nickname: user?.nickname?.trim() || null,
    birthday: user?.birthday?.trim() || null,
  };
}
