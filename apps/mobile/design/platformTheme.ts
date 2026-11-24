// 実行時だけPlatformを参照する。色の定義・契約・テストはtheme.tsに集約する。
import { Platform } from "react-native";
import { homeIndigo, selectAppTheme } from "./theme";

export * from "./theme";

const presentation = selectAppTheme(Platform.OS);
export const isIndigoIOS = Platform.OS === "ios";
export const appColors = presentation.colors;
export const appSemanticTheme = presentation.semantic;
export const dawn = presentation.splash;
export const statusBarStyle = presentation.statusBarStyle;
export const primaryActionText = presentation.primaryActionText;
// 既存TextInputの値・イベント・アクセシビリティ指定には触れない。
export const inputAppearance = isIndigoIOS
  ? { keyboardAppearance: "dark" as const, selectionColor: homeIndigo.action }
  : {};
