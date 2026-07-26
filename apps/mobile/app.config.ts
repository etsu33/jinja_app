import type { ConfigContext, ExpoConfig } from "expo/config";

// app.jsonから移行。process.env参照(react-native-mapsのAndroid Google Maps APIキー)を
// 使うためにはapp.config.ts(動的config)が必要で、静的なapp.jsonはprocess.envを解決できない
// (app.json内の"process.env.X"はビルド時に置換されず、生成AndroidManifest.xmlへ
// リテラル文字列のまま書き込まれてしまう)。
export default ({ config }: ConfigContext): ExpoConfig => ({
  ...config,
  name: "KAMI MUSUBI",
  slug: "jinja-app",
  scheme: "ai-sanpai-navi",
  plugins: [
    "expo-router",
    [
      "expo-location",
      {
        locationWhenInUsePermission: "使用中に位置情報を利用します。近場の人気神社の提案に使われます。",
        locationAlwaysAndWhenInUsePermission: "常に、または使用中のみで位置情報を利用します。",
      },
    ],
    [
      "react-native-maps",
      {
        // iosGoogleMapsApiKeyは意図的に渡さない。未指定の場合、react-native-mapsの
        // config pluginはiOS側にGoogle Maps SDKを組み込まず、既定のApple Mapsのままにする
        // (node_modules/react-native-maps/plugin/build/ios.jsのwithMapsIOSで確認済み)。
        androidGoogleMapsApiKey: process.env.EXPO_PUBLIC_ANDROID_GOOGLE_MAPS_API_KEY,
      },
    ],
  ],
  ios: {
    infoPlist: {
      NSLocationWhenInUseUsageDescription: "近場の人気神社を提案するため、アプリ使用中に位置情報を利用します。",
      NSLocationAlwaysAndWhenInUseUsageDescription: "バックグラウンド含め近場の神社提案や現在地更新に位置情報を利用します。",
      ITSAppUsesNonExemptEncryption: false,
    },
    bundleIdentifier: "com.morietsu.kamimusubi",
  },
  android: {
    package: "com.morietsu.kamimusubi",
    permissions: ["ACCESS_COARSE_LOCATION", "ACCESS_FINE_LOCATION"],
  },
  extra: {
    router: {},
    eas: {
      projectId: "a6cd458a-bdb6-4a5b-8b44-2939d4848b39",
    },
  },
  owner: "morietsu",
});
