import * as React from "react";
import { Alert, Pressable, ScrollView, StyleSheet, Text, View, useWindowDimensions } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { useFocusEffect, useRouter } from "expo-router";
import * as Linking from "expo-linking";
import { LinearGradient } from "expo-linear-gradient";
import { WaPattern } from "../../../components/common/WaPattern";
import Ionicons from "@expo/vector-icons/Ionicons";

import { LEGAL_LABELS, openLegalDocument } from "../../../lib/legalLinks";
import { dawnNight } from "../../../design/theme";
import { getFavoriteShrines, getRecentViewed } from "../../../lib/shrineStorage";
import { getCounts } from "../../../lib/storage";
import { getAuthenticatedBillingStatus, isPremiumStatus, type BillingStatus } from "../../../lib/billing";
import { isUnauthenticatedError } from "../../../lib/http";
import { trackConsultationHistoryEntryClicked } from "../../../lib/consultationHistoryAnalytics";
import { isLoggedIn } from "../../../lib/authTokens";
import { ACCOUNT_DELETION_MESSAGES, deleteAccount } from "../../../lib/accountDeletion";
import { LOGOUT_MESSAGES, confirmLogout, fetchAccountUsername, logout } from "../../../lib/logout";
import { typography } from "../../../design/typography";

// ---- お問い合わせ (Mother Ship承認済みの契約) ----
// 宛先と件名は可読な定数として保持する。
const CONTACT_EMAIL = "j33db05@gmail.com";
const CONTACT_SUBJECT = "KAMI MUSUBI お問い合わせ";

// クエリ値は UTF-8 の完全な percent-encode とする。生の日本語を置くと
// URLの解釈がメーラー任せになり件名が化ける端末が出るため、
// 長いpercent文字列を手書きせず encodeURIComponent で構築して取りこぼしを防ぐ。
//
// 実際に生成される文字列:
//   mailto:j33db05@gmail.com?subject=KAMI%20MUSUBI%20%E3%81%8A%E5%95%8F%E3%81%84%E5%90%88%E3%82%8F%E3%81%9B
const CONTACT_MAILTO_URL = `mailto:${CONTACT_EMAIL}?subject=${encodeURIComponent(CONTACT_SUBJECT)}`;

// メールアプリが未設定の端末では openURL が reject する。
// UI(文言・レイアウト・カード構造)は変えない方針のため、ここでは
// rejectを未処理のまま残さないことだけを保証する
// (既存の app/shrines/[id].tsx と同じ扱い)。
function openContactMail() {
  Linking.openURL(CONTACT_MAILTO_URL).catch(() => {});
}

// 利用規約・プライバシーポリシーはWeb版のページを外部ブラウザで開く。
// App Store Review Guideline 3.1.2 が、自動更新サブスクリプションを持つアプリに
// 「機能する」リンクをバイナリ内へ置くことを求めるため、飾りのカードにしない。
function openTerms() {
  openLegalDocument("terms", Linking.openURL);
}

function openPrivacy() {
  openLegalDocument("privacy", Linking.openURL);
}

const SIGNED_IN_DESCRIPTION = "ログイン中です。別のアカウントに入り直すときは、ログアウトしてください。";

// ユーザー名が取れなかったことを、取れたときと同じ見た目にしない。
// 以前は失敗も成功も「ログイン中」と出ていたため、通信が死んでいることに
// 画面から気づけず、「ログイン中なのに何も開けない」という見え方になっていた。
type AccountNameState =
  | { kind: "loading" }
  | { kind: "ready"; username: string }
  | { kind: "unavailable" };

function describeAccount(state: AccountNameState): { title: string; description: string } {
  if (state.kind === "ready") {
    return { title: state.username, description: SIGNED_IN_DESCRIPTION };
  }

  if (state.kind === "unavailable") {
    return {
      title: LOGOUT_MESSAGES.signedInFallbackName,
      description: "アカウント情報を取得できませんでした。通信の状況をご確認ください。ログアウトして入り直すこともできます。",
    };
  }

  return { title: LOGOUT_MESSAGES.signedInFallbackName, description: SIGNED_IN_DESCRIPTION };
}

type PremiumMetaState =
  | { kind: "loading" }
  | { kind: "unauthenticated" }
  | { kind: "error" }
  | { kind: "ready"; status: BillingStatus };

// billing.ts の isPremiumStatus をそのまま利用し、Free/Premium判定ロジックはここで持たない。
function describePremiumMeta(state: PremiumMetaState): string {
  if (state.kind === "loading") return "確認中...";
  if (state.kind === "unauthenticated") return "ログインすると確認できます";
  if (state.kind === "error") return "登録状況を確認できませんでした";
  return isPremiumStatus(state.status) ? "Premium登録済み" : "現在はFreeプラン";
}

type MyPageCardProps = {
  title: string;
  description: string;
  meta?: string;
  // 旧実装は円の中に漢字1文字(人・規・私・退…)を置いていた。意味の読み解きが要り、
  // Premium だけ "P" とラテン文字が混ざって体系が壊れていたため、タブバーと同じ
  // Ionicons へ揃える。
  icon: React.ComponentProps<typeof Ionicons>["name"];
  actionLabel?: string;
  onPress?: () => void;
};

type UsageStatProps = {
  label: string;
  value: string;
  helper: string;
  onPress: () => void;
};

function MyPageCard({ title, description, meta, icon, actionLabel, onPress }: MyPageCardProps) {
  return (
    <Pressable
      onPress={onPress}
      disabled={!onPress}
      style={({ pressed }) => [styles.card, pressed && styles.cardPressed]}
      accessibilityRole={onPress ? "button" : undefined}
    >
      <View style={styles.iconBox}>
        <Ionicons name={icon} size={CARD_ICON_SIZE} color={dawnNight.mark} />
      </View>
      <View style={styles.cardBody}>
        <Text style={styles.cardTitle}>{title}</Text>
        <Text style={styles.cardDescription}>{description}</Text>
        {meta ? <Text style={styles.cardMeta}>{meta}</Text> : null}
      </View>
      {actionLabel ? (
        <View style={styles.cardAction}>
          <Text style={styles.cardActionText}>{actionLabel}</Text>
        </View>
      ) : null}
    </Pressable>
  );
}

// 数字だけを見せて行き先が無いと、利用状況が行き止まりになる。
// 4つとも対応する一覧画面を持つため、カードごとそこへ繋ぐ。
function UsageStat({ label, value, helper, onPress }: UsageStatProps) {
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={`${label} ${value}。一覧を開く`}
      onPress={onPress}
      style={({ pressed }) => [styles.statCard, pressed && styles.cardPressed]}
    >
      <Text style={styles.statValue}>{value}</Text>
      <Text style={styles.statLabel}>{label}</Text>
      <Text style={styles.statHelper}>{helper}</Text>
    </Pressable>
  );
}

// カード左のアイコン。iconBox(46pt)の中に置く。
const CARD_ICON_SIZE = 22;

// 画面内コンテンツの上余白。safe area inset の内側に置く。
const CONTENT_TOP_PADDING = 24;

export default function MyPageScreen() {
  const router = useRouter();
  // タブ画面はネイティブヘッダーを持たないため、Dynamic Island / ステータスバーの
  // 高さを自分で避ける(下層画面はStackのヘッダーが避けている)。
  const insets = useSafeAreaInsets();
  const { height: screenHeight } = useWindowDimensions();
  const [favoriteCount, setFavoriteCount] = React.useState<number | null>(null);
  const [recentCount, setRecentCount] = React.useState<number | null>(null);
  const [visitCount, setVisitCount] = React.useState<number | null>(null);
  const [stampCount, setStampCount] = React.useState<number | null>(null);
  const [premiumMeta, setPremiumMeta] = React.useState<PremiumMetaState>({ kind: "loading" });
  const [loggedIn, setLoggedIn] = React.useState(false);
  const [accountName, setAccountName] = React.useState<AccountNameState>({ kind: "loading" });
  const [deletingAccount, setDeletingAccount] = React.useState(false);
  const deletingAccountRef = React.useRef(false);

  // タブ画面は表示中も破棄されないため、ログイン・新規登録から戻ったときに
  // ログイン状態を取り直せるよう、画面が表示されるたびに確認する。
  useFocusEffect(
    React.useCallback(() => {
        let mounted = true;
        isLoggedIn()
          .then((value) => {
            if (!mounted) return;
            setLoggedIn(value);
            if (!value) {
              setAccountName({ kind: "loading" });
              return;
            }
            // ログイン中だけ、アカウントの欄に出すユーザー名を取りにいく。
            // 取れなかったことは、取れたことと区別して出す(describeAccount)。
            void fetchAccountUsername().then((username) => {
              if (!mounted) return;
              setAccountName(username ? { kind: "ready", username } : { kind: "unavailable" });
            });
          })
          .catch(() => {
            if (mounted) setLoggedIn(false);
          });
        return () => {
          mounted = false;
        };
    }, []),
  );

  // ログアウトでは画面を移らないため、useFocusEffect の確かめ直しは動かない。
  // ログインの印を消したら、その場で表示を「ログイン」「新規登録」に切り替える。
  const runLogout = React.useCallback(async () => {
    await logout();
    setLoggedIn(false);
    setAccountName({ kind: "loading" });
  }, []);

  const confirmAndLogout = React.useCallback(() => {
    confirmLogout(Alert.alert, () => {
      void runLogout();
    });
  }, [runLogout]);

  const runAccountDeletion = React.useCallback(async () => {
    if (deletingAccountRef.current) return;
    deletingAccountRef.current = true;
    setDeletingAccount(true);

    try {
      const result = await deleteAccount();
      if (result.ok) {
        router.replace("/");
        Alert.alert(ACCOUNT_DELETION_MESSAGES.done);
        return;
      }
      Alert.alert(ACCOUNT_DELETION_MESSAGES.failed);
    } finally {
      deletingAccountRef.current = false;
      setDeletingAccount(false);
    }
  }, [router]);

  // 確認ダイアログは2段階（取り消せない旨 → Premium購読も停止される旨）。
  const confirmAccountDeletion = React.useCallback(() => {
    if (deletingAccountRef.current) return;
    Alert.alert(ACCOUNT_DELETION_MESSAGES.confirmTitle, ACCOUNT_DELETION_MESSAGES.confirmBody, [
      { text: "キャンセル", style: "cancel" },
      {
        text: "次へ",
        style: "destructive",
        onPress: () => {
          Alert.alert(ACCOUNT_DELETION_MESSAGES.finalConfirmTitle, ACCOUNT_DELETION_MESSAGES.finalConfirmBody, [
            { text: "キャンセル", style: "cancel" },
            {
              text: "退会する",
              style: "destructive",
              onPress: () => {
                void runAccountDeletion();
              },
            },
          ]);
        },
      },
    ]);
  }, [runAccountDeletion]);

  // Premium の登録状況も、ログイン状態と同じく画面に戻るたび取り直す。
  // 一度きりにしていたため、ログイン前にこのタブを開いていると、ログインして
  // 戻っても「ログインすると確認できます」のまま、アプリを再起動するまで
  // 直らなかった。ログイン欄だけが更新されて、Premium欄が取り残されていた。
  useFocusEffect(
    React.useCallback(() => {
      let mounted = true;

      getAuthenticatedBillingStatus()
        .then((status) => {
          if (!mounted) return;
          setPremiumMeta(status ? { kind: "ready", status } : { kind: "error" });
        })
        .catch((error) => {
          if (!mounted) return;
          setPremiumMeta(isUnauthenticatedError(error) ? { kind: "unauthenticated" } : { kind: "error" });
        });

      return () => {
        mounted = false;
      };
    }, []),
  );

  // 利用状況の数字も、参拝や保存をしてから戻ってきたときに古いままにしない。
  useFocusEffect(
    React.useCallback(() => {
      let mounted = true;

      getFavoriteShrines()
        .then((items) => {
          if (mounted) setFavoriteCount(items.length);
        })
        .catch(() => {
          if (mounted) setFavoriteCount(0);
        });

      getRecentViewed(20)
        .then((items) => {
          if (mounted) setRecentCount(items.length);
        })
        .catch(() => {
          if (mounted) setRecentCount(0);
        });

      getCounts()
        .then(({ visits, stamps }) => {
          if (!mounted) return;
          setVisitCount(visits);
          setStampCount(stamps);
        })
        .catch(() => {
          if (!mounted) return;
          setVisitCount(0);
          setStampCount(0);
        });

      return () => {
        mounted = false;
      };
    }, []),
  );

  const account = describeAccount(accountName);

  return (
    <View style={styles.screen}>
      {/* 地は相談フロー・ホーム・記録と同じ藍。タブ4画面で揃える。 */}
      <LinearGradient
        colors={dawnNight.colors}
        locations={dawnNight.locations}
        start={{ x: 0.5, y: 0 }}
        end={{ x: 0.5, y: 1 }}
        style={StyleSheet.absoluteFill}
      />
      <View style={StyleSheet.absoluteFill} pointerEvents="none">
        <WaPattern height={screenHeight} />
      </View>
      <View style={{ paddingTop: insets.top }} />
      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
        <View style={styles.header}>
          {/* 英語の小見出し(MY PAGE)はやめた。すぐ下の見出しが同じことを日本語で
              言っており、他の画面も日本語で揃えている。 */}
          <Text style={styles.title}>マイページ</Text>
          <Text style={styles.subtitle}>
            プロフィール、Premium、設定をここから確認できます。
          </Text>
        </View>

        {loggedIn ? (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>アカウント</Text>
            <MyPageCard
              title={account.title}
              description={account.description}
              icon="person"
              actionLabel="ログアウト"
              onPress={confirmAndLogout}
            />
          </View>
        ) : (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>アカウント</Text>
            <MyPageCard
              title="ログイン"
              description="記録や相談履歴を保存して、あとから見返せます。"
              icon="log-in"
              actionLabel="ログイン"
              onPress={() => router.push("/login")}
            />
            <MyPageCard
              title="新規登録"
              description="アカウントをお持ちでない方はこちらから作成できます。"
              icon="person-add"
              actionLabel="登録"
              onPress={() => router.push("/signup")}
            />
          </View>
        )}

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>プロフィール</Text>
          <MyPageCard
            title="プロフィールカード"
            description="生年月日や出生情報、参拝スタイルを設定できます。"
            meta="入力内容は神社提案の補助情報として使われます。"
            icon="id-card"
            actionLabel="確認"
            onPress={() => router.push("/profile")}
          />
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>利用状況</Text>
          <View style={styles.usageGrid}>
            <UsageStat
              label="お気に入り"
              value={favoriteCount === null ? "..." : `${favoriteCount}`}
              helper="保存した神社"
              onPress={() => router.push("/favorites")}
            />
            <UsageStat
              label="参拝回数"
              value={visitCount === null ? "..." : `${visitCount}`}
              helper="記録された参拝"
              onPress={() => router.push("/visit-history")}
            />
            <UsageStat
              label="最近見た神社"
              value={recentCount === null ? "..." : `${recentCount}`}
              helper="閲覧履歴"
              onPress={() => router.push("/recently-viewed")}
            />
            <UsageStat
              label="御朱印"
              value={stampCount === null ? "..." : `${stampCount}`}
              helper="登録した御朱印"
              onPress={() => router.push("/goshuin")}
            />
          </View>
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>相談</Text>
          <MyPageCard
            title="相談履歴"
            description="これまでの相談と、当時推薦された神社を見返せます。"
            icon="chatbubbles"
            actionLabel="開く"
            onPress={() => {
              trackConsultationHistoryEntryClicked();
              router.push("/consultation-history");
            }}
          />
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Premium</Text>
          <MyPageCard
            title="Premium"
            description="前回比較、深い振り返り、保存した相談の整理を使えるようにします。"
            meta={describePremiumMeta(premiumMeta)}
            icon="diamond"
            actionLabel="確認"
            onPress={() => router.push("/premium")}
          />
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>設定・サポート</Text>
          {loggedIn ? (
            <MyPageCard
              title="退会する"
              description="アカウントと記録を削除します。この操作は取り消せません。"
              meta={deletingAccount ? "退会処理中..." : "Premiumをご利用中の場合、購読も停止されます。"}
              icon="trash"
              actionLabel="退会"
              onPress={deletingAccount ? undefined : confirmAccountDeletion}
            />
          ) : null}
          <MyPageCard
            title={LEGAL_LABELS.terms}
            description="アプリの利用条件を確認できます。"
            icon="document-text"
            actionLabel="開く"
            onPress={openTerms}
          />
          <MyPageCard
            title={LEGAL_LABELS.privacy}
            description="取得する情報と取り扱いを確認できます。"
            icon="shield-checkmark"
            actionLabel="開く"
            onPress={openPrivacy}
          />
          <MyPageCard
            title="お問い合わせ"
            description="不具合や相談がある場合の連絡先です。"
            icon="mail"
            actionLabel="送る"
            onPress={openContactMail}
          />
        </View>
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  screen: {
    flex: 1,
    backgroundColor: dawnNight.colors[0],
  },
  content: {
    paddingHorizontal: 24,
    paddingTop: CONTENT_TOP_PADDING,
    paddingBottom: 48,
    gap: 22,
  },
  header: {
    gap: 8,
  },
  title: {
    ...typography.display,
    color: dawnNight.text,
  },
  subtitle: {
    ...typography.body,
    color: dawnNight.text,
    opacity: dawnNight.textBody,
  },
  section: {
    gap: 12,
  },
  sectionTitle: {
    ...typography.title,
    color: dawnNight.text,
    opacity: dawnNight.textBody,
  },
  usageGrid: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 10,
  },
  statCard: {
    width: "48%",
    minHeight: 104,
    backgroundColor: dawnNight.surface,
    borderWidth: 1,
    borderColor: dawnNight.border,
    borderRadius: 18,
    paddingHorizontal: 14,
    paddingVertical: 14,
    justifyContent: "space-between",
  },
  statValue: {
    color: dawnNight.mark,
    fontSize: 26,
    fontWeight: "900",
    letterSpacing: 0.2,
  },
  statLabel: {
    ...typography.footnoteStrong,
    color: dawnNight.text,
    marginTop: 8,
  },
  statHelper: {
    ...typography.caption,
    color: dawnNight.text,
    opacity: dawnNight.textMuted,
    marginTop: 4,
  },
  card: {
    flexDirection: "row",
    alignItems: "center",
    gap: 14,
    backgroundColor: dawnNight.surface,
    borderWidth: 1,
    borderColor: dawnNight.border,
    borderRadius: 18,
    paddingHorizontal: 16,
    paddingVertical: 15,
  },
  cardPressed: {
    opacity: dawnNight.textMuted,
  },
  iconBox: {
    width: 46,
    height: 46,
    borderRadius: 14,
    borderWidth: 1,
    borderColor: dawnNight.mark,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: dawnNight.selectedSurface,
  },
  cardBody: {
    flex: 1,
    gap: 4,
  },
  cardTitle: {
    ...typography.title,
    color: dawnNight.text,
  },
  cardDescription: {
    ...typography.subhead,
    color: dawnNight.text,
    opacity: dawnNight.textBody,
  },
  cardMeta: {
    ...typography.footnote,
    color: dawnNight.text,
    opacity: dawnNight.textMuted,
  },
  cardAction: {
    borderWidth: 1,
    borderColor: dawnNight.mark,
    borderRadius: 999,
    paddingHorizontal: 10,
    paddingVertical: 6,
  },
  cardActionText: {
    ...typography.caption,
    color: dawnNight.mark,
  },
});
