import { Modal, Pressable, ScrollView, StyleSheet, Text, View } from "react-native";
import { appColors as theme, appSemanticTheme } from "../../design/platformTheme";
import { radius } from "../../design/radius";
import { typography } from "../../design/typography";
import Ionicons from "@expo/vector-icons/Ionicons";

// 選択済みの印。旧実装は "✓" のグリフだった。
const CHECK_SIZE = 20;

type Option = { label: string; value: string };

export function ProfilePickerModal({
  visible,
  title,
  options,
  selectedValue,
  onSelect,
  onClose,
}: {
  visible: boolean;
  title: string;
  options: Option[];
  selectedValue?: string;
  onSelect: (value: string) => void;
  onClose: () => void;
}) {
  return (
    <Modal visible={visible} transparent animationType="fade" onRequestClose={onClose}>
      <Pressable style={styles.backdrop} onPress={onClose}>
        <Pressable style={styles.sheet} onPress={(event) => event.stopPropagation()}>
          <View style={styles.header}>
            <Text style={styles.title}>{title}</Text>
            <Pressable
              onPress={onClose}
              accessibilityRole="button"
              accessibilityLabel="閉じる"
              style={styles.closeButton}
            >
              <Text style={styles.close}>閉じる</Text>
            </Pressable>
          </View>
          <ScrollView style={styles.options} contentContainerStyle={styles.optionsContent}>
            {options.map((option) => {
              const selected = option.value === selectedValue;
              return (
                <Pressable
                  key={option.value}
                  accessibilityRole="radio"
                  accessibilityLabel={option.label}
                  accessibilityState={{ checked: selected }}
                  style={[styles.option, selected && styles.optionSelected]}
                  onPress={() => {
                    onClose();
                    onSelect(option.value);
                  }}
                >
                  <Text style={[styles.optionText, selected && styles.optionTextSelected]}>{option.label}</Text>
                  {selected ? <Ionicons name="checkmark" size={CHECK_SIZE} color={theme.accent} /> : null}
                </Pressable>
              );
            })}
          </ScrollView>
        </Pressable>
      </Pressable>
    </Modal>
  );
}

const styles = StyleSheet.create({
  backdrop: { flex: 1, backgroundColor: appSemanticTheme["overlay.default"], justifyContent: "flex-end" },
  sheet: { maxHeight: "72%", backgroundColor: theme.surface, borderTopLeftRadius: radius.lg, borderTopRightRadius: radius.lg, padding: 20 },
  header: { flexDirection: "row", alignItems: "center", justifyContent: "space-between", marginBottom: 12 },
  title: { ...typography.subheading, color: theme.text },
  // HIGの最小タップ領域44pt。余白をTextに持たせると37ptにしかならないため、
  // Pressable側で高さを確保する。
  closeButton: { minHeight: 44, justifyContent: "center", paddingHorizontal: 8 },
  close: { ...typography.label, color: theme.accent },
  options: { flexGrow: 0 },
  optionsContent: { paddingBottom: 24 },
  option: { minHeight: 48, paddingHorizontal: 14, flexDirection: "row", alignItems: "center", justifyContent: "space-between", borderBottomWidth: 1, borderBottomColor: theme.borderHeader },
  optionSelected: { backgroundColor: theme.surfaceSoft },
  optionText: { ...typography.label, color: theme.text },
  optionTextSelected: { color: theme.accent, fontWeight: "600" },
});
