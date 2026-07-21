import type { DerivedProfile, DirectionProfile, UserProfile } from "../types/profile";

export function normalizeBirthday(value?: string): string | undefined {
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
  ) {
    return undefined;
  }
  return `${String(year).padStart(4, "0")}-${String(month).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
}

// ライフパス：生年月日の全桁を1桁になるまで繰り返し足す（11, 22はマスターナンバーとして保持）
export function calculateLifePath(birthday: string): string {
  const normalized = normalizeBirthday(birthday);
  if (!normalized) return "";
  const digits = normalized.replace(/-/g, "");
  let sum = digits.split("").reduce((acc, d) => acc + parseInt(d, 10), 0);
  while (sum > 9 && sum !== 11 && sum !== 22) {
    sum = sum.toString().split("").reduce((acc, d) => acc + parseInt(d, 10), 0);
  }
  return String(sum);
}

// 九星気学：生まれ年の九星（節分基準を簡略化し1月1日基準で計算）
// 九星は (11 - (year % 9)) % 9 で求め、0を9に補正
export function calculateKyusei(birthday: string): string {
  const normalized = normalizeBirthday(birthday);
  if (!normalized) return "";
  const year = parseInt(normalized.slice(0, 4), 10);
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

type Direction = "北" | "北東" | "東" | "南東" | "南" | "南西" | "西" | "北西";
const PALACE_BY_DIRECTION: Record<Direction, number> = { 北: 1, 北東: 8, 東: 3, 南東: 4, 南: 9, 南西: 2, 西: 7, 北西: 6 };
const OPPOSITE: Record<Direction, Direction> = { 北: "南", 北東: "南西", 東: "西", 南東: "北西", 南: "北", 南西: "北東", 西: "東", 北西: "南東" };
const STAR_ELEMENT: Record<number, string> = { 1: "水", 2: "土", 3: "木", 4: "木", 5: "土", 6: "金", 7: "金", 8: "土", 9: "火" };
const GENERATES: Record<string, string> = { 木: "火", 火: "土", 土: "金", 金: "水", 水: "木" };
const DIRECTIONS = Object.keys(PALACE_BY_DIRECTION) as Direction[];

function kyuseiYear(date: Date): number {
  const year = date.getFullYear();
  return date.getMonth() < 1 || (date.getMonth() === 1 && date.getDate() < 4) ? year - 1 : year;
}

function starNumberForYear(year: number): number {
  return ((11 - (year % 9) - 1) % 9) + 1;
}

function annualStarAt(direction: Direction, centerStar: number): number {
  return ((centerStar + PALACE_BY_DIRECTION[direction] - 5 - 1 + 18) % 9) + 1;
}

function taisaiDirection(year: number): Direction {
  return (["北", "北東", "北東", "東", "南東", "南東", "南", "南西", "南西", "西", "北西", "北西"] as Direction[])[((year - 4) % 12 + 12) % 12];
}

export function calculateAnnualLuckyDirections(birthday: string, referenceDate = new Date()): DirectionProfile {
  const normalized = normalizeBirthday(birthday);
  if (!normalized) return {};
  const [birthYear, birthMonth, birthDay] = normalized.split("-").map(Number);
  const honmeiYear = birthMonth < 2 || (birthMonth === 2 && birthDay < 4) ? birthYear - 1 : birthYear;
  const honmeiStar = starNumberForYear(honmeiYear);
  const targetYear = kyuseiYear(referenceDate);
  const centerStar = starNumberForYear(targetYear);
  const starByDirection = Object.fromEntries(DIRECTIONS.map((direction) => [direction, annualStarAt(direction, centerStar)])) as Record<Direction, number>;
  const fiveYellow = DIRECTIONS.find((direction) => starByDirection[direction] === 5);
  const honmeiDirection = DIRECTIONS.find((direction) => starByDirection[direction] === honmeiStar);
  const exclusions = new Set<Direction>();
  if (fiveYellow) { exclusions.add(fiveYellow); exclusions.add(OPPOSITE[fiveYellow]); }
  if (honmeiDirection) { exclusions.add(honmeiDirection); exclusions.add(OPPOSITE[honmeiDirection]); }
  exclusions.add(OPPOSITE[taisaiDirection(targetYear)]);
  const honmeiElement = STAR_ELEMENT[honmeiStar];
  const luckyDirections = DIRECTIONS.filter((direction) => {
    if (exclusions.has(direction)) return false;
    const element = STAR_ELEMENT[starByDirection[direction]];
    return element === honmeiElement || GENERATES[element] === honmeiElement || GENERATES[honmeiElement] === element;
  });
  return {
    luckyDirection: luckyDirections[0], luckyDirections, targetYear,
    calculationMethod: "annual_kyusei_v1", excludedDirections: DIRECTIONS.filter((direction) => exclusions.has(direction)), source: "calculated",
  };
}

export function calculateGogyo(birthday: string): string {
  const kyusei = calculateKyusei(birthday);
  return KYUSEI_TO_GOGYO[kyusei] ?? "不明";
}

export function buildDirectionProfile(userProfile: UserProfile, referenceDate = new Date()): DirectionProfile {
  return calculateAnnualLuckyDirections(userProfile.birthday ?? "", referenceDate);
}

export function buildDerivedProfile(userProfile: UserProfile): DerivedProfile {
  const birthday = normalizeBirthday(userProfile.birthday);
  if (!birthday) {
    return { kyusei: undefined, gogyo: undefined, lifePath: undefined };
  }
  return {
    kyusei: calculateKyusei(birthday),
    gogyo: calculateGogyo(birthday),
    lifePath: calculateLifePath(birthday),
  };
}
