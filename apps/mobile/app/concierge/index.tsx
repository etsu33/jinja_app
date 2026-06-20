import { Text, View } from "react-native";
import { kamimusubiDark } from "../theme";

export default function ConciergeScreen() {
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
        相談
      </Text>
      <Text
        style={{ color: kamimusubiDark.text, marginTop: 12, fontSize: 15 }}
      >
        相談テーマから神社と出会う導線です。
      </Text>
    </View>
  );
}
