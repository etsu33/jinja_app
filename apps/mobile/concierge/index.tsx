import * as React from "react";
import { KeyboardAvoidingView, Platform, View, Text, TextInput, Pressable, ScrollView, StyleSheet } from "react-native";
import { kamimusubiDark as theme } from "../app/theme";

type Msg = { id: string; role: "user" | "assistant"; content: string };

export default function Concierge() {
  const [input, setInput] = React.useState("");
  const [messages, setMessages] = React.useState<Msg[]>([
    { id: "sys1", role: "assistant", content: "こんにちは。今の気持ちや願いを、短くても大丈夫なので話してみてください。" }
  ]);

  const send = () => {
    if (!input.trim()) return;
    const userMsg: Msg = { id: String(Date.now()), role: "user", content: input.trim() };
    // いまはダミー応答
    const aiMsg: Msg = { id: String(Date.now()+1), role: "assistant", content: "受け取りました。あなたの言葉から、今の状態に合う神社とのご縁を探します。（ダミー）" };
    setMessages(prev => [...prev, userMsg, aiMsg]);
    setInput("");
  };

  return (
    <KeyboardAvoidingView
      style={styles.screen}
      behavior={Platform.OS === "ios" ? "padding" : undefined}
    >
      <ScrollView contentContainerStyle={styles.messagesContent}>
        {messages.map((m) => (
          <React.Fragment key={m.id}>
            <View style={[styles.bubble, m.role === "user" ? styles.user : styles.assistant]}>
              <Text style={[styles.messageText, m.role === "user" ? styles.userText : styles.assistantText]}>{m.content}</Text>
            </View>
          </React.Fragment>
        ))}
      </ScrollView>

      <View style={styles.inputBar}>
        <TextInput
          value={input}
          onChangeText={setInput}
          placeholder="今の気持ちや願いを書いてください"
          placeholderTextColor={theme.mutedDark}
          style={styles.input}
          multiline
        />
        <Pressable onPress={send} style={styles.sendBtn}>
          <Text style={styles.sendText}>↑</Text>
        </Pressable>
      </View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  screen: {
    flex: 1,
    backgroundColor: theme.background,
  },
  messagesContent: {
    width: "100%",
    maxWidth: 430,
    alignSelf: "center",
    paddingHorizontal: 20,
    paddingTop: 24,
    paddingBottom: 120,
    gap: 10,
  },
  bubble: {
    maxWidth: "84%",
    borderRadius: 18,
    paddingHorizontal: 14,
    paddingVertical: 12,
    marginBottom: 2,
  },
  user: {
    alignSelf: "flex-end",
    backgroundColor: theme.gold,
  },
  assistant: {
    alignSelf: "flex-start",
    backgroundColor: theme.surface,
    borderWidth: 1,
    borderColor: theme.border,
  },
  messageText: {
    fontSize: 15,
    lineHeight: 22,
    fontWeight: "700",
  },
  userText: {
    color: theme.background,
  },
  assistantText: {
    color: theme.text,
  },
  inputBar: {
    position: "absolute",
    left: 0,
    right: 0,
    bottom: 0,
    width: "100%",
    maxWidth: 430,
    alignSelf: "center",
    flexDirection: "row",
    alignItems: "flex-end",
    gap: 10,
    paddingHorizontal: 20,
    paddingTop: 12,
    paddingBottom: 18,
    backgroundColor: theme.background,
    borderTopWidth: 1,
    borderColor: theme.borderHeader,
  },
  input: {
    flex: 1,
    minHeight: 50,
    maxHeight: 120,
    backgroundColor: theme.surface,
    borderWidth: 1,
    borderColor: theme.border,
    borderRadius: 18,
    paddingHorizontal: 14,
    paddingVertical: 12,
    color: theme.text,
    fontSize: 15,
    lineHeight: 22,
  },
  sendBtn: {
    width: 54,
    height: 54,
    alignItems: "center",
    justifyContent: "center",
    borderRadius: 27,
    backgroundColor: theme.gold,
  },
  sendText: {
    color: theme.background,
    fontSize: 22,
    fontWeight: "900",
  },
});
