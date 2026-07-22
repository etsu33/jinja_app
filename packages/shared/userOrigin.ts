export type UserOriginSource = "device" | "station" | "address" | "prefecture";
export type UserOrigin = { latitude: number; longitude: number; source: UserOriginSource; displayName?: string; accuracy: "precise" | "approximate" };
export type OriginMode = "none" | "device" | "manual" | "prefecture" | "disabled";
export const toOriginPayload = (origin: UserOrigin | null) => origin && Number.isFinite(origin.latitude) && Number.isFinite(origin.longitude) && Math.abs(origin.latitude) <= 90 && Math.abs(origin.longitude) <= 180 ? { lat: origin.latitude, lng: origin.longitude } : undefined;

const rows: Array<[string, number, number]> = [
  ["北海道",43.0642,141.3469],["青森県",40.8244,140.74],["岩手県",39.7036,141.1527],["宮城県",38.2688,140.8721],["秋田県",39.7186,140.1024],["山形県",38.2404,140.3633],["福島県",37.7503,140.4676],
  ["茨城県",36.3418,140.4468],["栃木県",36.5657,139.8836],["群馬県",36.3912,139.0609],["埼玉県",35.8569,139.6489],["千葉県",35.6047,140.1233],["東京都",35.6762,139.6503],["神奈川県",35.4478,139.6425],
  ["新潟県",37.9026,139.0232],["富山県",36.6953,137.2113],["石川県",36.5947,136.6256],["福井県",36.0652,136.2216],["山梨県",35.6642,138.5684],["長野県",36.6513,138.181],["岐阜県",35.3912,136.7223],["静岡県",34.9769,138.3831],["愛知県",35.1802,136.9066],
  ["三重県",34.7303,136.5086],["滋賀県",35.0045,135.8686],["京都府",35.0116,135.7681],["大阪府",34.6937,135.5023],["兵庫県",34.6913,135.183],["奈良県",34.6851,135.8048],["和歌山県",34.226,135.1675],
  ["鳥取県",35.5039,134.2377],["島根県",35.4723,133.0505],["岡山県",34.6618,133.9344],["広島県",34.3963,132.4596],["山口県",34.1859,131.4714],["徳島県",34.0658,134.5593],["香川県",34.3401,134.0434],["愛媛県",33.8416,132.7657],["高知県",33.5597,133.5311],
  ["福岡県",33.5904,130.4017],["佐賀県",33.2494,130.2988],["長崎県",32.7503,129.8779],["熊本県",32.7898,130.7417],["大分県",33.2382,131.6126],["宮崎県",31.9111,131.4239],["鹿児島県",31.5602,130.5581],["沖縄県",26.2124,127.6809],
];
export const PREFECTURE_ORIGINS = rows.map(([name, latitude, longitude]) => ({ name, latitude, longitude }));
export function prefectureOrigin(name: string): UserOrigin | null {
  const item = PREFECTURE_ORIGINS.find((row) => row.name === name);
  return item ? { latitude: item.latitude, longitude: item.longitude, source: "prefecture", displayName: item.name, accuracy: "approximate" } : null;
}
