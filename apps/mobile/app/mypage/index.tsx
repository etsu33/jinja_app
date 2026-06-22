import * as React from "react";
import { Pressable, ScrollView, StyleSheet, Text, View } from "react-native";
import { kamimusubiDark as theme } from "../theme";
import { getFavoriteShrines, getRecentViewed } from "../../lib/shrineStorage";
import { getCounts } from "../../lib/storage";

type MyPageCardProps = {
  title: string;
  description: string;
  meta?: string;
  iconText: string;
  actionLabel?: string;
};

type UsageStatProps = {
  label: string;
  value: string;
  helper: string;
};

function MyPageCard({ title, description, meta, iconText, actionLabel }: MyPageCardProps) {
  return (
    <View style={styles.card}>
      <View style={styles.iconBox}>
        <Text style={styles.iconText}>{iconText}</Text>
      </View>
      <View style={styles.cardBody}>
        <Text style={styles.cardTitle}>{title}</Text>
        <Text style={styles.cardDescription}>{description}</Text>
        {meta ? <Text style={styles.cardMeta}>{meta}</Text> : null}
      </View>
      {actionLabel ? (
        <Pressable style={styles.cardAction} accessibilityRole="button">
          <Text style={styles.cardActionText}>{actionLabel}</Text>
        </Pressable>
      ) : null}
    </View>
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
  const [favoriteCount, setFavoriteCount] = React.useState<number | null>(null);
  const [recentCount, setRecentCount] = React.useState<number | null>(null);
  const [visitCount, setVisitCount] = React.useState<number | null>(null);

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
          プロフィール、誕生日、Premium、設定をここから確認できます。
        </Text>
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>プロフィール</Text>
        <MyPageCard
          title="プロフィールカード"
          description="名前や表示情報を確認する場所です。"
          meta="表示名は今後プロフィール設定と連携します。"
          iconText="人"
          actionLabel="確認"
        />
        <MyPageCard
          title="誕生日"
          description="相性や条件提案の補助情報として使います。"
          meta="未設定"
          iconText="誕"
          actionLabel="設定"
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
        <Text style={styles.sectionTitle}>Premium</Text>
        <MyPageCard
          title="Premium"
          description="前回比較、深い振り返り、保存した相談の整理を使えるようにします。"
          meta="現在はFreeプラン"
          iconText="P"
          actionLabel="確認"
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
