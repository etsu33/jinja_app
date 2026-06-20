import { Text, View } from "react-native";
import { kamimusubiDark } from "./theme";

export default function HomeScreen() {
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
          fontSize: 24,
          fontWeight: "700",
        }}
      >
        KAMI MUSUBI
      </Text>
      <Text
        style={{ color: kamimusubiDark.text, marginTop: 12, fontSize: 16 }}
      >
        今の相談から、向かう神社を見つける
      </Text>
    </View>
  );
}
