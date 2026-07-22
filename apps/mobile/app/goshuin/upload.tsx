// apps/mobile/src/app/goshuin/upload.tsx
import * as React from "react";
import * as ImagePicker from "expo-image-picker";
import { View, Text, Pressable, Image, StyleSheet, Alert, ScrollView } from "react-native";
import { useRouter } from "expo-router";
import { pushStamp } from "../../lib/storage";
import Button from "../../components/ui/Button";
import { kamimusubiDark as theme } from "../../design/theme";

export default function GoshuinUpload() {
  const router = useRouter();
  const [uri, setUri] = React.useState<string | null>(null);
  const [saving, setSaving] = React.useState(false);
  const savingRef = React.useRef(false);

  const ask = React.useCallback(async () => {
    await ImagePicker.requestCameraPermissionsAsync();
    await ImagePicker.requestMediaLibraryPermissionsAsync();
  }, []);

  React.useEffect(() => {
    ask();
  }, [ask]);

  const goBack = React.useCallback(() => {
    if (router.canGoBack()) {
      router.back();
    } else {
      router.replace("/records");
    }
  }, [router]);

  const pickFromLibrary = async () => {
    const res = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      quality: 0.9,
    });
    if (!res.canceled) setUri(res.assets[0].uri);
  };

  const takePhoto = async () => {
    const res = await ImagePicker.launchCameraAsync({ quality: 0.9 });
    if (!res.canceled) setUri(res.assets[0].uri);
  };

  const save = async () => {
    if (!uri || savingRef.current) return;

    savingRef.current = true;
    setSaving(true);
    try {
      const savedItem = await pushStamp(uri);
      if (!savedItem) return;

      Alert.alert("保存しました");
      goBack();
    } catch (error) {
      if (__DEV__) {
        console.warn("[GoshuinUpload] failed to save stamp", error);
      }
    } finally {
      savingRef.current = false;
      setSaving(false);
    }
  };

  return (
    <ScrollView style={styles.screen} contentContainerStyle={styles.container}>
      <View style={styles.header}>
        <Pressable onPress={goBack} style={styles.backBtn}>
          <Text style={styles.backBtnText}>← 戻る</Text>
        </Pressable>
      </View>

      <View style={styles.titleBlock}>
        <Text style={styles.lead}>参拝の記録</Text>
        <Text style={styles.title}>御朱印を登録</Text>
        <Text style={styles.subtitle}>カメラで撮影、またはアルバムから選択してください。</Text>
      </View>

      <View style={styles.pickRow}>
        <Pressable onPress={takePhoto} style={({ pressed }) => [styles.pickBtn, pressed && styles.pressed]}>
          <Text style={styles.pickBtnIcon}>□</Text>
          <Text style={styles.pickBtnText}>カメラ</Text>
        </Pressable>
        <Pressable onPress={pickFromLibrary} style={({ pressed }) => [styles.pickBtn, pressed && styles.pressed]}>
          <Text style={styles.pickBtnIcon}>□</Text>
          <Text style={styles.pickBtnText}>アルバム</Text>
        </Pressable>
      </View>

      {uri ? (
        <View style={styles.previewBlock}>
          <Image source={{ uri }} style={styles.previewImage} />
          <Button
            title="この御朱印を保存する"
            variant="primary"
            onPress={save}
            loading={saving}
            accessibilityLabel="この御朱印を保存する"
          />
        </View>
      ) : (
        <View style={styles.placeholder}>
          <Text style={styles.placeholderIcon}>□</Text>
          <Text style={styles.placeholderTitle}>画像を選択してください</Text>
          <Text style={styles.placeholderText}>結んだご縁を、あとから振り返れる形で残します。</Text>
        </View>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  screen: {
    flex: 1,
    backgroundColor: theme.outside,
  },
  container: {
    width: "100%",
    maxWidth: 430,
    alignSelf: "center",
    minHeight: "100%",
    backgroundColor: theme.background,
    paddingHorizontal: 20,
    paddingTop: 22,
    paddingBottom: 48,
  },
  header: {
    marginBottom: 28,
  },
  backBtn: {
    alignSelf: "flex-start",
    paddingVertical: 8,
    paddingHorizontal: 13,
    borderRadius: 999,
    borderWidth: 1,
    borderColor: theme.borderGold,
    backgroundColor: "transparent",
  },
  backBtnText: {
    color: theme.gold,
    fontSize: 13,
    fontWeight: "800",
  },
  titleBlock: {
    marginBottom: 24,
  },
  lead: {
    color: theme.mutedSoft,
    fontSize: 14,
    fontWeight: "800",
    letterSpacing: 1,
    marginBottom: 10,
  },
  title: {
    color: theme.text,
    fontSize: 30,
    fontWeight: "900",
    lineHeight: 40,
    letterSpacing: 1,
  },
  subtitle: {
    color: theme.muted,
    fontSize: 13,
    lineHeight: 20,
    fontWeight: "600",
    marginTop: 10,
  },
  pickRow: {
    flexDirection: "row",
    gap: 12,
    marginBottom: 24,
  },
  pickBtn: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    gap: 8,
    paddingVertical: 20,
    borderRadius: 20,
    backgroundColor: theme.surface,
    borderWidth: 1,
    borderColor: theme.border,
  },
  pickBtnIcon: {
    color: theme.gold,
    fontSize: 24,
    fontWeight: "900",
  },
  pickBtnText: {
    color: theme.text,
    fontSize: 14,
    fontWeight: "900",
  },
  pressed: {
    opacity: 0.75,
  },
  previewBlock: {
    gap: 16,
  },
  previewImage: {
    width: "100%",
    aspectRatio: 3 / 4,
    borderRadius: 22,
    borderWidth: 1,
    borderColor: theme.border,
    backgroundColor: theme.surface,
  },
  placeholder: {
    alignItems: "center",
    justifyContent: "center",
    gap: 10,
    paddingVertical: 58,
    paddingHorizontal: 20,
    borderRadius: 24,
    borderWidth: 1,
    borderColor: theme.borderSoft,
    borderStyle: "dashed",
    backgroundColor: theme.surface,
  },
  placeholderIcon: {
    color: theme.gold,
    fontSize: 34,
    fontWeight: "900",
  },
  placeholderTitle: {
    color: theme.text,
    fontSize: 17,
    fontWeight: "900",
  },
  placeholderText: {
    color: theme.mutedDark,
    fontSize: 14,
    lineHeight: 22,
    fontWeight: "600",
    textAlign: "center",
  },
});
