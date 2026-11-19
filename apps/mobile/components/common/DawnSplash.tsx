import * as React from "react";
import { AccessibilityInfo, Animated, StyleSheet, Text, View } from "react-native";
import { LinearGradient } from "expo-linear-gradient";
import * as SplashScreen from "expo-splash-screen";

import { dawn } from "../../design/theme";
import { typography } from "../../design/typography";

// ios-ui-spec-v2.md 10節: Splash はロゴのみ。余計なコピー・ボタン・機能説明を置かない。
// 和の朝焼け(design/theme.ts の dawn)を、夜明け前の濃藍から地平の光へ上から下へ敷く。
//
// ロゴは画面上から32%の位置に置く。そこでの地の色は #334663 で、白文字との
// コントラストは 9.56。44%より下は 4.5 を割るため文字を置かない。
const MARK_TOP = "32%";

// 26節/37節: 区切りは1〜2秒以内、Fade は180〜300ms。
const HOLD_MS = 1100;
const FADE_MS = 280;

type Props = { onDone: () => void };

export function DawnSplash({ onDone }: Props) {
  const opacity = React.useRef(new Animated.Value(1)).current;

  React.useEffect(() => {
    let cancelled = false;
    // 自前のSplashが出てからネイティブのSplashを隠す。白い瞬きを挟まないため。
    // 失敗してもネイティブSplashに留まらないよう、必ず握りつぶす。
    void SplashScreen.hideAsync().catch(() => undefined);

    const finish = () => {
      if (!cancelled) onDone();
    };

    const timer = setTimeout(() => {
      void AccessibilityInfo.isReduceMotionEnabled()
        .then((reduceMotion) => {
          if (cancelled) return;
          if (reduceMotion) {
            finish();
            return;
          }
          Animated.timing(opacity, {
            toValue: 0,
            duration: FADE_MS,
            useNativeDriver: true,
          }).start(finish);
        })
        .catch(finish);
    }, HOLD_MS);

    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, [onDone, opacity]);

  return (
    <Animated.View pointerEvents="none" style={[StyleSheet.absoluteFill, styles.root, { opacity }]}>
      <LinearGradient
        colors={dawn.colors}
        locations={dawn.locations}
        start={{ x: 0.5, y: 0 }}
        end={{ x: 0.5, y: 1 }}
        style={StyleSheet.absoluteFill}
      />
      <View accessibilityRole="header" style={styles.mark}>
        <Text style={styles.brandName}>神結び</Text>
        <Text style={styles.brandRuby}>KAMI MUSUBI</Text>
      </View>
    </Animated.View>
  );
}

const styles = StyleSheet.create({
  root: {
    zIndex: 20,
  },
  mark: {
    position: "absolute",
    top: MARK_TOP,
    left: 0,
    right: 0,
    alignItems: "center",
    gap: 10,
  },
  brandName: {
    ...typography.display,
    color: "#FFFFFF",
    letterSpacing: 6,
  },
  brandRuby: {
    ...typography.eyebrow,
    color: "#FFFFFF",
    letterSpacing: 7,
    opacity: 0.92,
  },
});
