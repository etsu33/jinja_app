export type ProfileInput = {
  birthday?: string | null;
  birth_time?: string | null;
  birth_place?: string | null;
  worship_style?: string | null;
};

export type DerivedProfile = {
  kyusei?: string;
  gogyo?: string;
  lifePath?: string;
};

export function normalizeBirthday(value?: string | null): string | undefined {
  const match = value?.trim().match(/^(\d{4})[-/](\d{1,2})[-/](\d{1,2})$/);
  if (!match) return undefined;
  const year = Number(match[1]);
  const month = Number(match[2]);
  const day = Number(match[3]);
  const date = new Date(Date.UTC(year, month - 1, day));
  const today = new Date();
  const todayUtc = Date.UTC(today.getFullYear(), today.getMonth(), today.getDate());
  if (
    year < 1900 ||
    date.getTime() > todayUtc ||
    date.getUTCFullYear() !== year ||
    date.getUTCMonth() !== month - 1 ||
    date.getUTCDate() !== day
  ) return undefined;
  return `${String(year).padStart(4, "0")}-${String(month).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
}

export function calculateLifePath(birthday: string): string {
  const normalized = normalizeBirthday(birthday);
  if (!normalized) return "";
  let sum = normalized.replace(/-/g, "").split("").reduce((total, digit) => total + Number(digit), 0);
  while (sum > 9 && sum !== 11 && sum !== 22) {
    sum = String(sum).split("").reduce((total, digit) => total + Number(digit), 0);
  }
  return String(sum);
}

export function calculateKyusei(birthday: string): string {
  const normalized = normalizeBirthday(birthday);
  if (!normalized) return "";
  const year = Number(normalized.slice(0, 4));
  const star = ((11 - (year % 9)) % 9) || 9;
  return ["", "一白水星", "二黒土星", "三碧木星", "四緑木星", "五黄土星", "六白金星", "七赤金星", "八白土星", "九紫火星"][star];
}

const KYUSEI_TO_GOGYO: Record<string, string> = {
  一白水星: "水", 二黒土星: "土", 三碧木星: "木", 四緑木星: "木", 五黄土星: "土",
  六白金星: "金", 七赤金星: "金", 八白土星: "土", 九紫火星: "火",
};

export function buildDerivedProfile(profile: ProfileInput): DerivedProfile {
  const birthday = normalizeBirthday(profile.birthday);
  if (!birthday) return { kyusei: undefined, gogyo: undefined, lifePath: undefined };
  const kyusei = calculateKyusei(birthday);
  return { kyusei, gogyo: KYUSEI_TO_GOGYO[kyusei] ?? "不明", lifePath: calculateLifePath(birthday) };
}

export function buildProfileContext(profile: ProfileInput) {
  const derived = buildDerivedProfile(profile);
  return {
    user_profile: {
      birthday: normalizeBirthday(profile.birthday),
      birthdate: normalizeBirthday(profile.birthday),
      birthTime: profile.birth_time || undefined,
      birthPlace: profile.birth_place || undefined,
      worshipStyle: profile.worship_style || undefined,
    },
    derived_profile: derived,
    direction_profile: normalizeBirthday(profile.birthday) ? { luckyDirection: "東", source: "placeholder" } : {},
  };
}
