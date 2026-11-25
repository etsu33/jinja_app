// 検索画面が参照するローカルの神社データ。
//
// 写真・評価値・お気に入り数は持たない。
// 以前は imageUrl に picsum.photos のランダム画像を入れており、実在の神社とは
// 無関係な写真をその神社の写真として表示していた。rating / favorites も実測値では
// なく手で置いた数字だった。どちらも「架空の画像を実在神社の写真として扱わない」
// という方針に反するため外した。
//
// 写真を載せるのは、出典と使用権利が確認できたものが用意できてから。
// その時は imageUrl を設定すれば、画面側は自動で表示に切り替わる
// (値が無い間は画像枠そのものを出さない)。
export type Shrine = {
  id: string;
  name: string;
  tags: string[]; // ご利益など
  prefecture?: string;
  description?: string;
  // 出典と権利を確認した写真がある場合のみ設定する。
  imageUrl?: string;
};

export const SHRINES: Shrine[] = [
  {
    id: "meiji",
    name: "明治神宮",
    tags: ["縁結び", "厄除け"],
    prefecture: "東京都",
    description: "都会の杜に包まれた静謐な神域。初詣で賑わう都内屈指の神社。",
  },
  {
    id: "fushimi",
    name: "伏見稲荷大社",
    tags: ["商売繁盛", "金運"],
    prefecture: "京都府",
    description: "千本鳥居で有名な全国の稲荷神社の総本宮。",
  },
  {
    id: "kanda",
    name: "神田明神",
    tags: ["商売繁盛", "厄除け", "IT守護"],
    prefecture: "東京都",
    description: "江戸総鎮守。近年はIT関連の祈願でも人気。",
  },
];
