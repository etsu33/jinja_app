import { Text, View } from "react-native";
import { kamimusubiDark } from "../theme";

export default function MyPageScreen() {
  return (
    <View
      style={{
        flex: 1,
        backgroundColor: kamimusubiDark.background,
        padding: 24,
        justifyContent: "center",
      }}
    >
      <Text
        style={{
          color: kamimusubiDark.gold,
          fontSize: 22,
          fontWeight: "700",
        }}
      >
        マイページ
      </Text>
      <Text
        style={{ color: kamimusubiDark.text, marginTop: 12, fontSize: 15 }}
      >
        プロフィール・設定・課金状態を確認する場所です。
      </Text>
    </View>
  );
}
