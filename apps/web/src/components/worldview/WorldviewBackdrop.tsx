// apps/web/src/components/worldview/WorldviewBackdrop.tsx
//
// KAMI MUSUBI 共通の背景モチーフ — "Japanese Modern Classic / Luminous Path"
//
// 「静かな暗さの中に、次へ進むための小さな光が差す」を、
// 写真・画像を一切使わず CSS gradient と inline SVG だけで構成する。
// 旧 features/home/components/HomeBackdrop を、Home以外の画面でも使える形へ
// 昇格させたもの。home variant の出力は旧 HomeBackdrop と同一である。
//
// ■ 構成（下から上へ）
//   1. 地      : Deep Ink Navy (--kt-world-ground)
//   2. 大気    : 上方からの光 + 下部の藍のニュアンス
//   3. 参道    : 波線（variantごとに本数が異なる）
//   4. 光      : 主線上のMain Orb（home variantのみ）
//
// ■ Variant
//   home     : Home専用の構図。波線3本 + Main Orb。Homeの本文カラムの実測に合わせた配置。
//   standard : Home 以外の全画面の既定。上部に波線2本、Orbなし、brassの暖かみなし、
//              下部の depth なし。見出し帯の背後にだけ参道を通す。
//   quiet    : 線が主要タスクを視覚的に妨げると確認できた画面だけに使う。地と上方の光のみ。
// Home 以外の画面へは components/worldview/WorldviewFrame を通して適用する。
//
// ■ 色
// 色はすべて KAMI MUSUBI Worldview Token (--kt-world-*, styles/tokens.css) を参照する。
// Home専用の --home-* には依存しない。hex等の実値をここへ書かない。
//
// ■ Accessibility
// 全体が装飾。aria-hidden で screen reader から外し、SVGにも
// title/desc を持たせない（不要な読み上げを出さない）。
// pointer-events-none で操作も一切奪わない。
// Animationは持たないため、prefers-reduced-motion で失われる情報もない。
//
// ■ Client Boundary
// 本Componentは Server Component である（"use client" を持たない）。
// hooks / state / event handler / browser API のいずれも使わない純粋な静的マークアップのため、
// 装飾レイヤーの分だけClient bundleを増やさない。この境界を保つこと。
// 将来Animationやinteractionを足す場合は、動く部分だけを別のClient Componentへ切り出す。
//
// ■ 使い方
// 親は `relative isolate` を持ち、本文側を `relative z-10` で上に重ねる。
// 1ページに1つだけ置く（SVG gradient の id が variant 単位で固定のため）。

export const WORLDVIEW_BACKDROP_VARIANTS = ["home", "standard", "quiet"] as const;
export type WorldviewBackdropVariant = (typeof WORLDVIEW_BACKDROP_VARIANTS)[number];

/** 参道の金。brass = Warm Brass / lit = Champagne Gold。 */
const PATH = "var(--kt-world-path)";
const PATH_LIT = "var(--kt-world-path-lit)";

/*
 * 大気の層。上から順に重なる（CSS background の先頭が最前面）。
 *   lit    : 上方から差す光（本文カラムを持ち上げる面の光）
 *   warmth : brass のごく薄い暖かみ（7%）。光源の色を地に一滴だけ落とす
 *   depth  : 下部に藍の面。青一色にせず、Surfaceの色相と地を繋ぐ
 *   ground : 地そのもの
 */
const ATMOSPHERE = {
  lit: "radial-gradient(122% 46% at 50% -8%, var(--kt-world-ground-lit) 0%, transparent 66%)",
  warmth: `radial-gradient(56% 22% at 50% 0%, color-mix(in oklab, ${PATH} 7%, transparent) 0%, transparent 74%)`,
  depth:
    "radial-gradient(150% 52% at 50% 106%, color-mix(in oklab, var(--kt-world-surface-elevated) 58%, transparent) 0%, transparent 72%)",
  ground: "var(--kt-world-ground)",
} as const;

type AtmosphereLayer = keyof typeof ATMOSPHERE;

type GradientStop = {
  offset: string;
  /** brass (path) か champagne (lit) か */
  tone: "path" | "lit";
  opacity: number;
};

type PathSpec = {
  /** gradient id の一部。variant内で一意 */
  key: string;
  d: string;
  strokeWidth: number;
  stops: readonly GradientStop[];
};

type OrbSpec = {
  /** 主線の通過点 (viewBox座標) */
  x: number;
  y: number;
  size: number;
};

type BandSpec = {
  /** 親の上端からの距離 (px)。帯の高さは実寸で固定し、横方向にだけ伸ばす。 */
  top: number;
  height: number;
  viewWidth: number;
  /** 描画順 = 配列順。弱い線から先に描き、主線を最後に置く。 */
  paths: readonly PathSpec[];
  orb?: OrbSpec;
};

type VariantSpec = {
  atmosphere: readonly AtmosphereLayer[];
  band?: BandSpec;
};

/*
 * ■ home variant の波線帯の座標系
 *
 * SVGは preserveAspectRatio="none" で横方向にだけ伸ばし、
 * 線の太さは vector-effect="non-scaling-stroke" で固定する。
 * これにより:
 *   - x は常にビューポート幅に対する比率で解決する (164/390 = 42.05%)
 *   - y は帯の高さを実寸で固定するため 1px = 1 viewBox unit で一致する
 * 結果、375 / 390 / 430px のいずれでもOrbが主線上に正確に乗る。
 *
 * top は Home の内枠上端からの距離。375pxでの実測に基づく。
 *
 * ■ 3本をどこに通すか
 * 本文は電話幅の単一カラムで、Card / Input はいずれもマットな不透明面
 * (Glassmorphism禁止) である。したがってカードの裏を通る線は「無い線」に
 * なってしまい、3本の明るさの階層が読めない。
 * そこで実測した「背景が素で見える帯」に1本ずつ通し、3本すべてが
 * 実際に視認できるようにする。
 *   home基準の実測値:
 *     入力カード下端 ≈ 457 / チップ見出し ≈ 492  → 空き帯 (主線 + Orb)
 *     チップ群 ≈ 527〜672                        → pillの隙間 (副線2)
 *     条件を追加する 〜 ANOTHER WAY IN ≈ 720〜780 → 空き帯 (副線1)
 * 文字の上を通るのは最も低いopacityの副線2だけに限定する。
 *
 * ■ 線の形の制約（全variant共通）
 *   - 横方向〜緩やかな斜め方向へ流れる（左→右へ単調に下降する）
 *   - ループ / 渦 / 円環 / 結び目形状を作らない
 *   - 互いに交差させない（yの値域を分離し、交差ゼロで満たす）
 * いずれの path も y が単調増加する三次ベジエだけで構成し、
 * 制御点も進行方向の前方にしか置かない（折り返しを作らない）。
 * 画面外(-24 / viewWidth+24)から出入りさせ、線の端が画面内で切れないようにする。
 *   home: 主線 y 118→268 / 副線2 y 260→430 / 副線1 y 420→580
 */
const HOME_ORB = { x: 164, y: 190, size: 184 } as const;

const HOME_BAND: BandSpec = {
  top: 280,
  height: 660,
  viewWidth: 390,
  paths: [
    {
      /* 副線2: 最も細く、最も低いopacity。チップ群のpillの隙間を縫って奥行きだけを担う。
         文字の上を通る唯一の線なので、輪郭を主張させない強さに抑える。 */
      key: "sub-2",
      d: "M -24 260 C 56 266, 116 306, 180 330 C 252 357, 330 398, 414 430",
      strokeWidth: 0.8,
      stops: [
        { offset: "0%", tone: "path", opacity: 0.04 },
        { offset: "52%", tone: "path", opacity: 0.17 },
        { offset: "100%", tone: "path", opacity: 0.05 },
      ],
    },
    {
      /* 副線1: 主線より細く、中程度のopacity。「条件を追加する」下の空き帯を通る。
         主線より暗く、均一な明るさにしない。 */
      key: "sub-1",
      d: "M -24 420 C 60 428, 126 468, 190 490 C 262 515, 336 552, 414 580",
      strokeWidth: 1,
      stops: [
        { offset: "0%", tone: "path", opacity: 0.07 },
        { offset: "46%", tone: "path", opacity: 0.36 },
        { offset: "100%", tone: "path", opacity: 0.1 },
      ],
    },
    {
      /* 主線: 最も太く、最も視認性が高い。Orbの位置を通過点として持つ。
         発光は「一部だけ」。Orbのx位置(42%)へ向かって brass から
         champagne gold へ明度が上がり、その前後で静かに落ちる。 */
      key: "main",
      d: `M -24 118 C 48 120, 104 166, ${HOME_ORB.x} ${HOME_ORB.y} C 232 217, 292 246, 414 268`,
      strokeWidth: 1.6,
      stops: [
        { offset: "0%", tone: "path", opacity: 0.09 },
        { offset: "24%", tone: "path", opacity: 0.3 },
        { offset: "38%", tone: "lit", opacity: 0.7 },
        { offset: "44%", tone: "lit", opacity: 0.86 },
        { offset: "54%", tone: "path", opacity: 0.42 },
        { offset: "72%", tone: "path", opacity: 0.18 },
        { offset: "100%", tone: "path", opacity: 0.07 },
      ],
    },
  ],
  orb: HOME_ORB,
};

/*
 * ■ standard variant
 * 一般画面の見出し帯の背後だけに参道を通す、Homeより一段控えめな構図。
 *   - Orbは持たない（光の焦点はHomeの入口だけに置く）
 *   - champagne gold の発光を持たず、brass のみ・最大opacityもHome主線の半分以下
 *   - 帯は上端寄り (top 24 / 高さ 220) に限定し、本文の読み取り領域へ線を伸ばさない
 *   y: 主線 40→150 / 副線 132→214（値域を分離し交差しない）
 */
const STANDARD_BAND: BandSpec = {
  top: 24,
  height: 220,
  viewWidth: 390,
  paths: [
    {
      key: "sub-1",
      d: "M -24 132 C 64 138, 140 166, 206 182 C 280 199, 344 208, 414 214",
      strokeWidth: 0.8,
      stops: [
        { offset: "0%", tone: "path", opacity: 0.03 },
        { offset: "50%", tone: "path", opacity: 0.14 },
        { offset: "100%", tone: "path", opacity: 0.04 },
      ],
    },
    {
      key: "main",
      d: "M -24 40 C 60 44, 128 82, 196 104 C 268 127, 332 142, 414 150",
      strokeWidth: 1.2,
      stops: [
        { offset: "0%", tone: "path", opacity: 0.05 },
        { offset: "40%", tone: "path", opacity: 0.3 },
        { offset: "100%", tone: "path", opacity: 0.06 },
      ],
    },
  ],
};

export const WORLDVIEW_BACKDROP_SPECS: Record<WorldviewBackdropVariant, VariantSpec> = {
  home: { atmosphere: ["lit", "warmth", "depth", "ground"], band: HOME_BAND },
  /* standard は下部の depth を持たない。Home 以外のフレームは本文の直後に
     RootLayout の LegalFooter（地のみ）が続くため、下端に藍の面が残ると
     フレームの終端で横一本の継ぎ目になる（App-wide rollout の実測で確認）。 */
  standard: { atmosphere: ["lit", "ground"], band: STANDARD_BAND },
  quiet: { atmosphere: ["lit", "ground"] },
};

/** variantの大気を CSS background の値として返す。 */
export function worldviewAtmosphere(variant: WorldviewBackdropVariant): string {
  return WORLDVIEW_BACKDROP_SPECS[variant].atmosphere.map((layer) => ATMOSPHERE[layer]).join(", ");
}

function gradientId(variant: WorldviewBackdropVariant, key: string): string {
  return `worldview-${variant}-path-${key}`;
}

/*
 * Main Orb。
 * 「光の玉」という物体ではなく、主線の途中に光が宿っているように見せる。
 *
 * SVGのfilterではなくCSSのradial-gradientで描く。SVGは横方向へ
 * 非等比に伸びるため、内部でぼかすと光が横に潰れる。実寸のdivで置けば
 * どの幅でも正円のまま、主線上の同じ点に乗る。
 *
 * 中心はやや不透明な champagne、外へ向かって brass が溶けて消える。
 * Neon / 強い白光 / レンズフレアにしないため、白は一切混ぜず最大opacityも抑える。
 */
const ORB_BACKGROUND = `radial-gradient(closest-side, color-mix(in oklab, ${PATH_LIT} 40%, transparent) 0%, color-mix(in oklab, ${PATH} 20%, transparent) 34%, color-mix(in oklab, ${PATH} 6%, transparent) 62%, transparent 100%)`;

type Props = {
  variant: WorldviewBackdropVariant;
};

export function WorldviewBackdrop({ variant }: Props) {
  const { band } = WORLDVIEW_BACKDROP_SPECS[variant];

  return (
    <div
      aria-hidden
      data-worldview-backdrop={variant}
      className="pointer-events-none absolute inset-0 z-0 overflow-hidden"
    >
      {/* 地 + 大気 */}
      <div
        data-worldview-layer="atmosphere"
        className="absolute inset-0"
        style={{ background: worldviewAtmosphere(variant) }}
      />

      {band ? (
        <>
          {/* 参道の波線。帯の高さを実寸で固定し、横方向にだけ伸ばす。 */}
          <svg
            data-worldview-layer="path"
            className="absolute inset-x-0"
            style={{ top: `${band.top}px`, height: `${band.height}px`, width: "100%" }}
            viewBox={`0 0 ${band.viewWidth} ${band.height}`}
            preserveAspectRatio="none"
            fill="none"
            focusable="false"
            aria-hidden
          >
            <defs>
              {band.paths.map((path) => (
                <linearGradient key={path.key} id={gradientId(variant, path.key)} x1="0" y1="0" x2="1" y2="0">
                  {path.stops.map((stop) => (
                    <stop
                      key={stop.offset}
                      offset={stop.offset}
                      stopColor={stop.tone === "lit" ? PATH_LIT : PATH}
                      stopOpacity={String(stop.opacity)}
                    />
                  ))}
                </linearGradient>
              ))}
            </defs>

            {band.paths.map((path) => (
              <path
                key={path.key}
                d={path.d}
                stroke={`url(#${gradientId(variant, path.key)})`}
                strokeWidth={String(path.strokeWidth)}
                strokeLinecap="round"
                vectorEffect="non-scaling-stroke"
              />
            ))}
          </svg>

          {band.orb ? (
            <div
              data-worldview-layer="orb"
              className="absolute"
              style={{
                left: `${(band.orb.x / band.viewWidth) * 100}%`,
                top: `${band.top + band.orb.y}px`,
                width: `${band.orb.size}px`,
                height: `${band.orb.size}px`,
                transform: "translate(-50%, -50%)",
                background: ORB_BACKGROUND,
              }}
            />
          ) : null}
        </>
      ) : null}
    </div>
  );
}
