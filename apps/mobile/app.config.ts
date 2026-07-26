import type { ConfigContext, ExpoConfig } from "expo/config";

// app.jsonから移行。process.env参照(react-native-mapsのAndroid Google Maps APIキー)を
// 使うためにはapp.config.ts(動的config)が必要で、静的なapp.jsonはprocess.envを解決できない
// (app.json内の"process.env.X"はビルド時に置換されず、生成AndroidManifest.xmlへ
// リテラル文字列のまま書き込まれてしまう)。
// Android Maps APIキーは一度だけ読み取る。react-native-mapsプラグインへは
// 従来通り実値を渡す(AndroidManifestへのネイティブ注入に必要)一方、
// JavaScript側の表示判定(Search画面)へは実値を渡さず、extra.androidMapsEnabled
// というbooleanのみを公開する。process.env.EXPO_PUBLIC_*はMetroバンドル生成時に
// インライン化されるが、EAS BuildのGradle経由バンドル生成では確実に伝播しない
// ことが確認されたため(READ_APP_CONFIG/AndroidManifestへは伝播するが、
// Gradleが起動するJSバンドル生成には伝播しない場合がある)、JS側の判定は
// ビルド時に確定済みのextra(Constants.expoConfig経由で実行時も安定して取得できる)
// を参照する設計にしている。
const androidGoogleMapsApiKey = process.env.EXPO_PUBLIC_ANDROID_GOOGLE_MAPS_API_KEY;

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
        androidGoogleMapsApiKey,
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
    androidMapsEnabled: Boolean(androidGoogleMapsApiKey),
  },
  owner: "morietsu",
});
