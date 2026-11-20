import * as React from "react";
import { StyleSheet } from "react-native";
import Svg, { G, Path } from "react-native-svg";

// 和の文様。流水(りゅうすい)を、藍の地の上下に薄く置く。
//
// 参考にした意匠は、グラデーションそのものより文様が効いていた
// (実測: 参考画像の上下の色差はわずかで、ほぼ均一だった)。
//
// 文様を自分で描く理由は2つ。
//  1. 流水は古くからある文様で、特定の誰かの著作物ではない。ストック画像を
//     貼ると、神社写真と同じ使用権利の確認が要る。参考に挙がった画像の1枚
//     には配布元の透かしが入っていた
//  2. 画像を持たないので、どの寸法でも崩れない
//
// 以前は上端に青海波(せいがいは)を敷いていたが、タイルが 44x22 と小さく
// 同心円が密に並ぶため、波ではなく鱗に見えた。実機で確認して流水だけにした。
//
// 文字の下へは敷かない。上下の縁に寄せ、中央は空ける。

/** 流水の線。生成りを薄く。 */
const STREAM = "#F5EEDC";
const STREAM_OPACITY = 0.16;
const STREAM_WIDTH = 7;

/** 描画の基準幅。実際の幅へは viewBox が合わせる。 */
const BASE_WIDTH = 400;

// 2本目を描くかどうかの境目。低い帯に2本置くと、間隔が詰まって見出しに重なる。
const SECOND_STREAM_MIN_HEIGHT = 320;

type Props = {
  /** 描画域の高さ。画面いっぱいに敷くときは画面の高さ。 */
  height: number;
  /** 上の縁に置くか。 */
  top?: boolean;
  /** 下の縁に置くか。 */
  bottom?: boolean;
};

/** 流水の一本。x から始まり、右へ2回折り返して流れる。 */
function stream(x: number, y: number, radius: number, run: number, tail: number): string {
  return (
    `M${x} ${y} h${run} ` +
    `a${radius} ${radius} 0 0 1 0 ${radius * 2} ` +
    `h${-(run * 0.55)} ` +
    `a${radius} ${radius} 0 0 0 0 ${radius * 2} ` +
    `h${tail}`
  );
}

export function WaPattern({ height, top = true, bottom = true }: Props) {
  const hasRoomForSecond = height >= SECOND_STREAM_MIN_HEIGHT;

  return (
    <Svg
      style={[StyleSheet.absoluteFill]}
      width="100%"
      height="100%"
      viewBox={`0 0 ${BASE_WIDTH} ${height}`}
      preserveAspectRatio="xMidYMid slice"
      pointerEvents="none"
    >
      <G
        opacity={STREAM_OPACITY}
        fill="none"
        stroke={STREAM}
        strokeWidth={STREAM_WIDTH}
        strokeLinecap="round"
      >
        {top ? (
          <>
            {/* 見出しより上の帯に収める。 */}
            <Path d={stream(-12, 26, 18, 86, 150)} />
            {hasRoomForSecond ? <Path d={stream(252, 70, 16, 74, 146)} /> : null}
          </>
        ) : null}
        {bottom ? (
          <>
            <Path d={stream(-12, height - 92, 18, 86, 150)} />
            {hasRoomForSecond ? <Path d={stream(252, height - 176, 16, 74, 146)} /> : null}
          </>
        ) : null}
      </G>
    </Svg>
  );
}
