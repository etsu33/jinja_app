import * as React from "react";
import { StyleSheet } from "react-native";
import Svg, { Circle, Defs, G, LinearGradient, Mask, Path, Pattern, Rect, Stop } from "react-native-svg";

// 和の文様。青海波(せいがいは)と流水を、藍の地の上に薄く敷く。
//
// 参考にした意匠は、グラデーションそのものより文様と金が効いていた
// (実測: 参考画像の上下の色差はわずかで、ほぼ均一だった)。
//
// 文様を自分で描く理由は2つ。
//  1. 青海波・流水は古くからある文様で、特定の誰かの著作物ではない。
//     ストック画像を貼ると、神社写真と同じ使用権利の確認が要る。
//  2. 画像を持たないので、どの寸法でも崩れない。
//
// 文字の下へは敷かない。上端から下へ向けて消す。参考にした壁紙は文字を
// 載せる前提ではなく、同じ濃さで敷くと見出しと進捗が柄に負ける。

/** 青海波を敷く高さ。画面上端からこの範囲だけ。 */
const SEIGAIHA_HEIGHT = 200;
/** 文様の一単位。 */
const TILE_W = 44;
const TILE_H = 22;
/** 金の線。地に対して主張しない濃さに留める。 */
const GOLD = "#C8A96A";
/** 流水の線。生成りを薄く。 */
const STREAM = "#F5EEDC";

type Props = {
  /** 描画域の高さ。画面いっぱいに敷くときは画面の高さ。 */
  height: number;
  /** 流水を出すか。帯のように低い領域では出さない。 */
  withStream?: boolean;
};

/** 青海波の一単位。中心をずらした同心円を3つ並べて波に見せる。 */
function SeigaihaTile() {
  const radii = [21, 15, 9, 3.5];
  return (
    <G fill="none" stroke={GOLD} strokeWidth={1}>
      {[0, TILE_W / 2, TILE_W].map((cx) =>
        radii.map((r) => <Circle key={`${cx}-${r}`} cx={cx} cy={TILE_H} r={r} />),
      )}
    </G>
  );
}

export function WaPattern({ height, withStream = true }: Props) {
  const width = 400;

  return (
    <Svg
      style={[StyleSheet.absoluteFill]}
      width="100%"
      height="100%"
      viewBox={`0 0 ${width} ${height}`}
      preserveAspectRatio="xMidYMin slice"
      pointerEvents="none"
    >
      <Defs>
        <Pattern id="seigaiha" width={TILE_W} height={TILE_H} patternUnits="userSpaceOnUse">
          <SeigaihaTile />
        </Pattern>
        {/* 上端だけ出して下へ消す。文字の下に柄を残さないため。 */}
        <LinearGradient id="fade" x1="0" y1="0" x2="0" y2="1">
          <Stop offset="0" stopColor="#FFFFFF" stopOpacity="0.30" />
          <Stop offset="1" stopColor="#FFFFFF" stopOpacity="0" />
        </LinearGradient>
        <Mask id="fadeMask">
          <Rect width={width} height={SEIGAIHA_HEIGHT} fill="url(#fade)" />
        </Mask>
      </Defs>

      <Rect width={width} height={SEIGAIHA_HEIGHT} fill="url(#seigaiha)" mask="url(#fadeMask)" />

      {/* 流水。画面下部の、文字が来ない帯に置く。 */}
      {withStream ? (
        <G opacity={0.16} fill="none" stroke={STREAM} strokeWidth={7} strokeLinecap="round">
          <Path d={`M-12 ${height - 92} h86 a18 18 0 0 1 0 36 h-48 a18 18 0 0 0 0 36 h150`} />
          <Path d={`M232 ${height - 196} h74 a16 16 0 0 1 0 32 h-36 a16 16 0 0 0 0 32 h146`} />
        </G>
      ) : null}
    </Svg>
  );
}
