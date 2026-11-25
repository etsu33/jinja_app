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
  // アプリアイコン。1024x1024 / アルファ無し / 角丸無しで置く。
  // 角丸はOSがマスクする(iOSは連続角丸、Androidはランチャー依存)ため自分では付けない。
  // アルファを含むとApp Store Connectのアップロードで弾かれる。
  // 図柄は注連縄の円に水引の蝶結び。地は紺(#010E28)で、画面の骨格色である
  // 深藍(#172A40)と同系。決定記録: docs/design/color-direction-v1.md
  icon: "./assets/icon.png",
  scheme: "ai-sanpai-navi",
  // App Storeに表示されるバージョン。機能の追加・修正を出すたびに上げる。
  // ビルド番号(ios.buildNumber)はEASのautoIncrementが上げるため、ここでは触らない。
  version: "1.0.0",
  // 本文カラムは max-width 430 の1カラムで、横向きのレイアウトを持たない。
  // 未指定だと全向き許容になり、横向きで左右が余白色で埋まる。
  orientation: "portrait",
  // 画面は明基調(kamimusubiLight)のみ。これを指定しないと、端末をダークに
  // している利用者で、OSが用意するキーボード・アラート・アクションシートだけが
  // 暗く出る。決定記録: docs/design/color-direction-v1.md
  userInterfaceStyle: "light",
  plugins: [
    "expo-router",
    // SDK 58 では expo-font / expo-splash-screen / expo-status-bar が config plugin を
    // 持つようになり、`expo install --fix` がここへの明示を要求する。
    // app.config.ts は動的configのためCLIが自動で書けず、非ゼロ終了していた。
    "expo-font",
    [
      "expo-splash-screen",
      {
        // plugin の既定は #ffffff。素のまま足すとネイティブの起動画面に白が焼き込まれ、
        // 直後に出る DawnSplash(濃藍から始まる朝焼け)との間で白が一瞬差し込む。
        // design/theme.ts の dawn.colors[0] と同値にして、継ぎ目を無くす。
        backgroundColor: "#16213C",
      },
    ],
    "expo-status-bar",
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
    // iPhone専用。iPadでは互換モードで動作する。
    supportsTablet: false,
    // EAS Buildのautoincrement(eas.json)が提出ごとに上げる。初回の基準値。
    buildNumber: "1",
    infoPlist: {
      NSLocationWhenInUseUsageDescription: "近場の人気神社を提案するため、アプリ使用中に位置情報を利用します。",
      NSLocationAlwaysAndWhenInUseUsageDescription: "バックグラウンド含め近場の神社提案や現在地更新に位置情報を利用します。",
      ITSAppUsesNonExemptEncryption: false,
    },
    bundleIdentifier: "com.morietsu.kamimusubi",
  },
  android: {
    package: "com.morietsu.kamimusubi",
    // Androidのアダプティブアイコンは、108dpのうち中央72dp(66%)しか必ず見える保証が
    // 無い。元画像は紋が81%を占めるため、そのまま使うと縁が切れる。
    // assets/adaptive-icon.png は画像全体を76%へ縮めて紋を約62%に収めてある。
    adaptiveIcon: {
      foregroundImage: "./assets/adaptive-icon.png",
      backgroundColor: "#010E28",
    },
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
