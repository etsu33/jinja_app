import * as React from "react";
import { Alert, Pressable, ScrollView, StyleSheet, Text, View } from "react-native";
import { useFocusEffect, useRouter } from "expo-router";
import * as Linking from "expo-linking";
import { kamimusubiDark as theme } from "../../design/theme";
import { getFavoriteShrines, getRecentViewed } from "../../lib/shrineStorage";
import { getCounts } from "../../lib/storage";
import { getAuthenticatedBillingStatus, isPremiumStatus, type BillingStatus } from "../../lib/billing";
import { isUnauthenticatedError } from "../../lib/http";
import { trackConsultationHistoryEntryClicked } from "../../lib/consultationHistoryAnalytics";
import { isLoggedIn } from "../../lib/authTokens";
import { ACCOUNT_DELETION_MESSAGES, deleteAccount } from "../../lib/accountDeletion";
import { LOGOUT_MESSAGES, confirmLogout, fetchAccountUsername, logout } from "../../lib/logout";

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
  iconText: string;
  actionLabel?: string;
  onPress?: () => void;
};

type UsageStatProps = {
  label: string;
  value: string;
  helper: string;
};

function MyPageCard({ title, description, meta, iconText, actionLabel, onPress }: MyPageCardProps) {
  return (
    <Pressable
      onPress={onPress}
      disabled={!onPress}
      style={({ pressed }) => [styles.card, pressed && styles.cardPressed]}
      accessibilityRole={onPress ? "button" : undefined}
    >
      <View style={styles.iconBox}>
        <Text style={styles.iconText}>{iconText}</Text>
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

function UsageStat({ label, value, helper }: UsageStatProps) {
  return (
    <View style={styles.statCard}>
      <Text style={styles.statValue}>{value}</Text>
      <Text style={styles.statLabel}>{label}</Text>
      <Text style={styles.statHelper}>{helper}</Text>
    </View>
  );
}

export default function MyPageScreen() {
  const router = useRouter();
  const [favoriteCount, setFavoriteCount] = React.useState<number | null>(null);
  const [recentCount, setRecentCount] = React.useState<number | null>(null);
  const [visitCount, setVisitCount] = React.useState<number | null>(null);
  const [premiumMeta, setPremiumMeta] = React.useState<PremiumMetaState>({ kind: "loading" });
  const [loggedIn, setLoggedIn] = React.useState(false);
  const [accountUsername, setAccountUsername] = React.useState<string | null>(null);
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
            setAccountUsername(null);
            return;
          }
          // ログイン中だけ、アカウントの欄に出すユーザー名を取りにいく(取れなければ「ログイン中」)。
          void fetchAccountUsername().then((username) => {
            if (mounted) setAccountUsername(username);
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
    setAccountUsername(null);
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

  React.useEffect(() => {
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
  }, []);

  React.useEffect(() => {
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
      .then(({ visits }) => {
        if (mounted) setVisitCount(visits);
      })
      .catch(() => {
        if (mounted) setVisitCount(0);
      });

    return () => {
      mounted = false;
    };
  }, []);

  return (
    <ScrollView
      style={styles.screen}
      contentContainerStyle={styles.content}
      showsVerticalScrollIndicator={false}
    >
      <View style={styles.header}>
        <Text style={styles.eyebrow}>MY PAGE</Text>
        <Text style={styles.title}>マイページ</Text>
        <Text style={styles.subtitle}>
          プロフィール、Premium、設定をここから確認できます。
        </Text>
      </View>

      {loggedIn ? (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>アカウント</Text>
          <MyPageCard
            title={accountUsername ?? LOGOUT_MESSAGES.signedInFallbackName}
            description="ログイン中です。別のアカウントに入り直すときは、ログアウトしてください。"
            iconText="人"
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
            iconText="入"
            actionLabel="ログイン"
            onPress={() => router.push("/login")}
          />
          <MyPageCard
            title="新規登録"
            description="アカウントをお持ちでない方はこちらから作成できます。"
            iconText="新"
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
          iconText="人"
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
          />
          <UsageStat
            label="参拝回数"
            value={visitCount === null ? "..." : `${visitCount}`}
            helper="記録された参拝"
          />
          <UsageStat
            label="最近見た神社"
            value={recentCount === null ? "..." : `${recentCount}`}
            helper="閲覧履歴"
          />
          <UsageStat
            label="御朱印"
            value="0"
            helper="次フェーズで連携"
          />
        </View>
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>相談</Text>
        <MyPageCard
          title="相談履歴"
          description="これまでの相談と、当時推薦された神社を見返せます。"
          iconText="談"
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
          iconText="P"
          actionLabel="確認"
          onPress={() => router.push("/premium")}
        />
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>設定・サポート</Text>
        <MyPageCard
          title="設定"
          description="通知や表示設定を確認する場所です。"
          meta="準備中"
          iconText="設"
          actionLabel="開く"
        />
        {loggedIn ? (
          <MyPageCard
            title="退会する"
            description="アカウントと記録を削除します。この操作は取り消せません。"
            meta={deletingAccount ? "退会処理中..." : "Premiumをご利用中の場合、購読も停止されます。"}
            iconText="退"
            actionLabel="退会"
            onPress={deletingAccount ? undefined : confirmAccountDeletion}
          />
        ) : null}
        <MyPageCard
          title="利用規約"
          description="アプリの利用条件を確認できます。"
          iconText="規"
          actionLabel="確認"
        />
        <MyPageCard
          title="お問い合わせ"
          description="不具合や相談がある場合の連絡先です。"
          iconText="問"
          actionLabel="送る"
          onPress={openContactMail}
        />
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  screen: {
    flex: 1,
    backgroundColor: theme.background,
  },
  content: {
    padding: 24,
    paddingBottom: 48,
    gap: 22,
  },
  header: {
    gap: 8,
  },
  eyebrow: {
    color: theme.goldSoft,
    fontSize: 12,
    fontWeight: "800",
    letterSpacing: 1.4,
  },
  title: {
    color: theme.gold,
    fontSize: 26,
    fontWeight: "900",
    letterSpacing: 0.4,
  },
  subtitle: {
    color: theme.text,
    fontSize: 14,
    lineHeight: 22,
    fontWeight: "600",
  },
  section: {
    gap: 12,
  },
  sectionTitle: {
    color: theme.goldSoft,
    fontSize: 13,
    fontWeight: "800",
    letterSpacing: 0.6,
  },
  usageGrid: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 10,
  },
  statCard: {
    width: "48%",
    minHeight: 104,
    backgroundColor: theme.surface,
    borderWidth: 1,
    borderColor: theme.borderHeader,
    borderRadius: 18,
    paddingHorizontal: 14,
    paddingVertical: 14,
    justifyContent: "space-between",
  },
  statValue: {
    color: theme.gold,
    fontSize: 26,
    fontWeight: "900",
    letterSpacing: 0.2,
  },
  statLabel: {
    color: theme.text,
    fontSize: 13,
    fontWeight: "900",
    marginTop: 8,
  },
  statHelper: {
    color: theme.muted,
    fontSize: 11,
    lineHeight: 16,
    fontWeight: "600",
    marginTop: 4,
  },
  card: {
    flexDirection: "row",
    alignItems: "center",
    gap: 14,
    backgroundColor: theme.surface,
    borderWidth: 1,
    borderColor: theme.borderHeader,
    borderRadius: 18,
    paddingHorizontal: 16,
    paddingVertical: 15,
  },
  cardPressed: {
    opacity: 0.72,
  },
  iconBox: {
    width: 46,
    height: 46,
    borderRadius: 14,
    borderWidth: 1,
    borderColor: theme.borderGold,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: theme.surfaceSoft,
  },
  iconText: {
    color: theme.gold,
    fontSize: 18,
    fontWeight: "900",
  },
  cardBody: {
    flex: 1,
    gap: 4,
  },
  cardTitle: {
    color: theme.text,
    fontSize: 15,
    fontWeight: "900",
  },
  cardDescription: {
    color: theme.mutedSoft,
    fontSize: 13,
    lineHeight: 19,
    fontWeight: "600",
  },
  cardMeta: {
    color: theme.muted,
    fontSize: 12,
    lineHeight: 17,
    fontWeight: "600",
  },
  cardAction: {
    borderWidth: 1,
    borderColor: theme.borderGold,
    borderRadius: 999,
    paddingHorizontal: 10,
    paddingVertical: 6,
  },
  cardActionText: {
    color: theme.gold,
    fontSize: 11,
    fontWeight: "800",
  },
});
