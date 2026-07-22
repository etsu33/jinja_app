import * as React from "react";
import { Pressable, StyleSheet, Text, TextInput, View } from "react-native";
import { get } from "../lib/http";
import { kamimusubiDark as theme } from "../app/theme";
import { ProfilePickerModal } from "./profile/ProfilePickerModal";
import {
  originSearchAnnouncement,
  originSelectionAnnouncement,
  type OriginSearchStatus,
} from "../../../packages/shared/directionAccessibility";
import { PREFECTURE_ORIGINS, prefectureOrigin, type OriginMode, type UserOrigin } from "../../../packages/shared/userOrigin";
import { trackMobileDirection } from "../lib/directionEvents";

type Candidate = { place_id: string; name: string | null; lat: number; lng: number; type?: string };
const modes: Array<[OriginMode, string]> = [
  ["device", "現在地を使用"],
  ["manual", "駅名・住所から指定"],
  ["prefecture", "都道府県から指定"],
  ["disabled", "方位情報を使用しない"],
];

export function MobileOriginSelector({
  origin,
  onChange,
  onUseDevice,
  locationStatus = "idle",
  disabled,
}: {
  origin: UserOrigin | null;
  onChange: (value: UserOrigin | null) => void;
  onUseDevice: () => void;
  locationStatus?: "idle" | "loading" | "ready" | "error";
  disabled?: boolean;
}) {
  const [mode, setMode] = React.useState<OriginMode>(
    origin?.source === "device" ? "device" : origin?.source === "prefecture" ? "prefecture" : origin ? "manual" : "none",
  );
  const [query, setQuery] = React.useState("");
  const [items, setItems] = React.useState<Candidate[]>([]);
  const [status, setStatus] = React.useState<OriginSearchStatus>("idle");
  const [picker, setPicker] = React.useState(false);
  const requestId = React.useRef(0);

  React.useEffect(() => {
    if (mode !== "manual" || query.trim().length < 2) {
      setItems([]);
      setStatus("idle");
      return;
    }
    const id = ++requestId.current;
    const timer = setTimeout(async () => {
      setStatus("searching");
      try {
        const data = await get<{ items?: Candidate[] }>(`/geocodes/search/?q=${encodeURIComponent(query.trim())}&limit=5&lang=ja`);
        if (id !== requestId.current) return;
        const next = Array.isArray(data.items) ? data.items : [];
        setItems(next);
        setStatus(next.length ? "idle" : "empty");
      } catch {
        if (id === requestId.current) {
          setItems([]);
          setStatus("error");
        }
      }
    }, 400);
    return () => clearTimeout(timer);
  }, [mode, query]);

  const switchMode = (next: OriginMode) => {
    requestId.current++;
    setMode(next);
    onChange(null);
    setItems([]);
    setStatus("idle");
    if (next === "disabled") trackMobileDirection("direction_origin_result", { origin_type: "disabled", result: "selected" });
    if (next === "device") onUseDevice();
  };

  const searchAnnouncement = originSearchAnnouncement(status, items.length);

  return (
    <View style={styles.wrap} accessibilityLabel="出発地点の指定">
      <View style={styles.row}>
        {modes.map(([value, label]) => {
          const selected = mode === value;
          return (
            <Pressable
              disabled={disabled}
              key={value}
              onPress={() => switchMode(value)}
              style={({ pressed }) => [styles.button, selected && styles.active, pressed && styles.pressed]}
              accessibilityRole="radio"
              accessibilityLabel={label}
              accessibilityState={{ checked: selected, disabled: !!disabled }}
            >
              <Text style={[styles.text, selected && styles.activeText]}>{selected ? `✓ ${label}` : label}</Text>
            </Pressable>
          );
        })}
      </View>

      {mode === "manual" ? (
        <>
          <TextInput
            accessibilityLabel="駅名または住所"
            accessibilityHint="2文字以上入力すると候補を検索します"
            value={query}
            onChangeText={(value) => { setQuery(value); onChange(null); }}
            placeholder="駅名または住所を入力"
            placeholderTextColor={theme.mutedDark}
            style={styles.input}
          />
          {searchAnnouncement ? <Text accessibilityLiveRegion="polite" style={status === "error" ? styles.error : styles.note}>{searchAnnouncement}</Text> : null}
          {items.map((item) => (
            <Pressable
              key={item.place_id}
              onPress={() => {
                onChange({ latitude: item.lat, longitude: item.lng, source: item.type === "station" ? "station" : "address", displayName: item.name ?? query, accuracy: "precise" });
                setItems([]);
                setStatus("idle");
              }}
              style={({ pressed }) => [styles.result, pressed && styles.pressed]}
              accessibilityRole="button"
              accessibilityLabel={`${item.name ?? query}を出発地点に設定`}
            >
              <Text style={styles.text}>{item.name}</Text>
            </Pressable>
          ))}
        </>
      ) : null}

      {mode === "prefecture" ? (
        <>
          <Pressable
            onPress={() => setPicker(true)}
            style={({ pressed }) => [styles.input, pressed && styles.pressed]}
            accessibilityRole="button"
            accessibilityLabel="都道府県を選択"
            accessibilityValue={{ text: origin?.source === "prefecture" ? origin.displayName : "未選択" }}
          >
            <Text style={styles.text}>{origin?.source === "prefecture" ? origin.displayName : "都道府県を選択"}</Text>
          </Pressable>
          {origin?.source === "prefecture" ? <Text style={styles.note}>{origin.displayName}のおおよその位置を出発地点として使用します。方位は参考情報です。</Text> : null}
        </>
      ) : null}

      {mode === "device" && locationStatus === "loading" ? <Text accessibilityLiveRegion="polite" style={styles.note}>現在地を取得中です。</Text> : null}
      {mode === "device" && locationStatus === "error" ? (
        <View accessibilityRole="alert" style={styles.errorBox}>
          <Text style={styles.error}>現在地を取得できませんでした。</Text>
          <Pressable onPress={() => switchMode("manual")} style={styles.fallbackButton} accessibilityRole="button" accessibilityLabel="駅名または住所から指定する">
            <Text style={styles.fallbackText}>駅名・住所から指定する</Text>
          </Pressable>
        </View>
      ) : null}
      <Text accessibilityLiveRegion="polite" style={styles.selected}>{originSelectionAnnouncement(origin)}</Text>

      <ProfilePickerModal
        visible={picker}
        title="都道府県"
        options={PREFECTURE_ORIGINS.map((prefecture) => ({ value: prefecture.name, label: prefecture.name }))}
        selectedValue={origin?.source === "prefecture" ? origin.displayName : undefined}
        onClose={() => setPicker(false)}
        onSelect={(value) => { onChange(prefectureOrigin(value)); setPicker(false); }}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: { gap: 10 },
  row: { flexDirection: "row", flexWrap: "wrap", gap: 8 },
  button: { minHeight: 44, minWidth: "47%", flexGrow: 1, borderWidth: 1, borderColor: theme.borderSoft, borderRadius: 12, paddingHorizontal: 10, paddingVertical: 10, justifyContent: "center" },
  active: { borderWidth: 2, borderColor: theme.goldSoft, backgroundColor: theme.surfaceSoft },
  pressed: { opacity: 0.72 },
  text: { color: theme.text, fontSize: 14, lineHeight: 20 },
  activeText: { color: theme.goldSoft, fontWeight: "800" },
  input: { minHeight: 44, borderWidth: 1, borderColor: theme.borderSoft, borderRadius: 12, paddingHorizontal: 12, paddingVertical: 10, color: theme.text, fontSize: 16, justifyContent: "center" },
  result: { minHeight: 44, paddingHorizontal: 12, paddingVertical: 10, justifyContent: "center", borderBottomWidth: 1, borderBottomColor: theme.borderSoft },
  note: { color: theme.muted, fontSize: 14, lineHeight: 21 },
  error: { color: "#fecaca", fontSize: 14, lineHeight: 21 },
  errorBox: { gap: 8, borderWidth: 1, borderColor: "#fca5a5", borderRadius: 12, padding: 10 },
  fallbackButton: { minHeight: 44, borderWidth: 1, borderColor: theme.goldSoft, borderRadius: 10, paddingHorizontal: 12, justifyContent: "center" },
  fallbackText: { color: theme.goldSoft, fontSize: 14, fontWeight: "800" },
  selected: { color: theme.goldSoft, fontSize: 14, lineHeight: 21, fontWeight: "700" },
});
