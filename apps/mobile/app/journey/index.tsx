import { Pressable, ScrollView, Text, View } from "react-native";
import { useRouter } from "expo-router";

import { StateCard } from "../../components/common/StateCard";
import { kamimusubiDark as theme } from "../theme";
import { spacing } from "../design/spacing";

export default function JourneyScreen() {
  const router = useRouter();

  return (
    <ScrollView
      style={{ backgroundColor: theme.background, flex: 1 }}
      contentContainerStyle={{ padding: spacing.screenXWide, paddingBottom: spacing.bottomSpace, gap: spacing.lgGap }}
    >
      <View style={{ marginBottom: spacing.lgGap }}>
        <Pressable onPress={() => router.replace("/records")} style={{ marginBottom: spacing.xlGap }}>
          <Text style={{ color: theme.gold, fontSize: 13, fontWeight: "700" }}>← 記録へ戻る</Text>
        </Pressable>
        <Text style={{ color: theme.gold, fontSize: 26, fontWeight: "700" }}>ご縁の歩み</Text>
        <Text style={{ color: theme.text, fontSize: 15, lineHeight: 23, marginTop: spacing.mdGap }}>
          相談から提案、参拝、振り返りまでの出来事を時系列で見返せます。
        </Text>
      </View>

      <StateCard title="タイムラインは次フェーズで接続します" description="現在はご縁の歩みの入口だけを用意しています。" />
    </ScrollView>
  );
}
