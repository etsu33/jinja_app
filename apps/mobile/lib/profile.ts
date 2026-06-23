import type { DerivedProfile, DirectionProfile, UserProfile } from "../types/profile";

// ライフパス：生年月日の全桁を1桁になるまで繰り返し足す（11, 22はマスターナンバーとして保持）
export function calculateLifePath(birthday: string): string {
  const digits = birthday.replace(/-/g, "");
  let sum = digits.split("").reduce((acc, d) => acc + parseInt(d, 10), 0);
  while (sum > 9 && sum !== 11 && sum !== 22) {
    sum = sum.toString().split("").reduce((acc, d) => acc + parseInt(d, 10), 0);
  }
  return String(sum);
}

// 九星気学：生まれ年の九星（節分基準を簡略化し1月1日基準で計算）
// 九星は (11 - (year % 9)) % 9 で求め、0を9に補正
export function calculateKyusei(birthday: string): string {
  const year = parseInt(birthday.slice(0, 4), 10);
  const star = ((11 - (year % 9)) % 9) || 9;
  const names = ["", "一白水星", "二黒土星", "三碧木星", "四緑木星", "五黄土星", "六白金星", "七赤金星", "八白土星", "九紫火星"];
  return names[star];
}

// 五行：九星気学の星から五行を導出
const KYUSEI_TO_GOGYO: Record<string, string> = {
  "一白水星": "水",
  "二黒土星": "土",
  "三碧木星": "木",
  "四緑木星": "木",
  "五黄土星": "土",
  "六白金星": "金",
  "七赤金星": "金",
  "八白土星": "土",
  "九紫火星": "火",
};

export function calculateGogyo(birthday: string): string {
  const kyusei = calculateKyusei(birthday);
  return KYUSEI_TO_GOGYO[kyusei] ?? "不明";
}

export function buildDirectionProfile(userProfile: UserProfile): DirectionProfile {
  if (!userProfile.birthday) {
    return {};
  }
  return {
    luckyDirection: "東",
    source: "placeholder",
  };
}

export function buildDerivedProfile(userProfile: UserProfile): DerivedProfile {
  const { birthday } = userProfile;
  if (!birthday) {
    return { kyusei: undefined, gogyo: undefined, lifePath: undefined };
  }
  return {
    kyusei: calculateKyusei(birthday),
    gogyo: calculateGogyo(birthday),
    lifePath: calculateLifePath(birthday),
  };
}
