import { Modal, Pressable, ScrollView, StyleSheet, Text, View } from "react-native";
import { kamimusubiDark as theme } from "../../app/theme";
import { radius } from "../../design/radius";

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
            <Pressable onPress={onClose} accessibilityRole="button" accessibilityLabel="閉じる">
              <Text style={styles.close}>閉じる</Text>
            </Pressable>
          </View>
          <ScrollView style={styles.options} contentContainerStyle={styles.optionsContent}>
            {options.map((option) => {
              const selected = option.value === selectedValue;
              return (
                <Pressable
                  key={option.value}
                  style={[styles.option, selected && styles.optionSelected]}
                  onPress={() => {
                    onClose();
                    onSelect(option.value);
                  }}
                >
                  <Text style={[styles.optionText, selected && styles.optionTextSelected]}>{option.label}</Text>
                  {selected ? <Text style={styles.check}>✓</Text> : null}
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
  backdrop: { flex: 1, backgroundColor: "rgba(0,0,0,0.68)", justifyContent: "flex-end" },
  sheet: { maxHeight: "72%", backgroundColor: theme.surface, borderTopLeftRadius: radius.lg, borderTopRightRadius: radius.lg, padding: 20 },
  header: { flexDirection: "row", alignItems: "center", justifyContent: "space-between", marginBottom: 12 },
  title: { color: theme.text, fontSize: 18, fontWeight: "900" },
  close: { color: theme.gold, fontSize: 14, fontWeight: "800", padding: 8 },
  options: { flexGrow: 0 },
  optionsContent: { paddingBottom: 24 },
  option: { minHeight: 48, paddingHorizontal: 14, flexDirection: "row", alignItems: "center", justifyContent: "space-between", borderBottomWidth: 1, borderBottomColor: theme.borderHeader },
  optionSelected: { backgroundColor: "rgba(221, 178, 82, 0.12)" },
  optionText: { color: theme.text, fontSize: 15 },
  optionTextSelected: { color: theme.gold, fontWeight: "800" },
  check: { color: theme.gold, fontSize: 18, fontWeight: "900" },
});
