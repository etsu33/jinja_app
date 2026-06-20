import { Text, View } from "react-native";
import { kamimusubiDark } from "../theme";

export default function RecordsScreen() {
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
        記録
      </Text>
      <Text
        style={{ color: kamimusubiDark.text, marginTop: 12, fontSize: 15 }}
      >
        お気に入り・御朱印・参拝履歴をまとめる場所です。
      </Text>
    </View>
  );
}
