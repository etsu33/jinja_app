import * as React from "react";
import { useLocalSearchParams, useRouter } from "expo-router";
import { View, Text, ScrollView, Pressable, Image, StyleSheet, Platform } from "react-native";
import { SHRINES } from "../../data/shrines";
import { kamimusubiDark as theme } from "../../design/theme";
import { spacing } from "../../design/spacing";
import { StateCard } from "../../components/common/StateCard";
import Button from "../../components/ui/Button";
import { ShrineSearchMap } from "../../components/search/ShrineSearchMap";
import { SelectedShrineMapCard } from "../../components/search/SelectedShrineMapCard";
import {
  fetchShrineMapPoints,
  findShrineMapPointById,
  isSearchMapSectionAvailable,
  type ShrineMapPoint,
} from "../../lib/shrineMap";
import { fetchPopularShrines, type PopularShrine } from "../../lib/popularShrines";
import { trackSearchScreenView, trackShrineCardClick } from "../../lib/searchAnalytics";
import { filterShrines, parseSearchFilters } from "../../lib/searchFilters";

const isMapSectionAvailable = isSearchMapSectionAvailable(
  Platform.OS,
  process.env.EXPO_PUBLIC_WEB_MAP_STYLE_URL,
  process.env.EXPO_PUBLIC_ANDROID_GOOGLE_MAPS_API_KEY,
);

export default function SearchPage() {
  const router = useRouter();
  const { q, filters } = useLocalSearchParams<{ q?: string; filters?: string }>();
  const selected = parseSearchFilters(filters);

  const [mapPoints, setMapPoints] = React.useState<ShrineMapPoint[]>([]);
  const [mapStatus, setMapStatus] = React.useState<"loading" | "ready" | "error">("loading");
  const [selectedShrineId, setSelectedShrineId] = React.useState<string | null>(null);
  const [popularShrines, setPopularShrines] = React.useState<PopularShrine[]>([]);
  const [popularStatus, setPopularStatus] = React.useState<"loading" | "ready" | "error">("loading");

  // 画面マウント中は1回だけ送る(依存配列を空にして再レンダーでの重複発火を避ける)。
  React.useEffect(() => {
    trackSearchScreenView();
  }, []);

  const loadMapPoints = React.useCallback(async () => {
    setMapStatus("loading");
    try {
      const points = await fetchShrineMapPoints({ query: q, limit: 50 });
      setMapPoints(points);
      setMapStatus("ready");
    } catch {
      setMapPoints([]);
      setMapStatus("error");
    }
  }, [q]);

  React.useEffect(() => {
    void loadMapPoints();
  }, [loadMapPoints]);

  // 「人気の神社」だけをloading/error対象にし、通常一覧・地図には影響させない。
  // loadMapPointsと同じ「マウント時に1回取得、再レンダーでは取得し直さない」契約に揃える。
  const loadPopularShrines = React.useCallback(async () => {
    setPopularStatus("loading");
    try {
      const shrines = await fetchPopularShrines();
      setPopularShrines(shrines.slice(0, 3));
      setPopularStatus("ready");
    } catch {
      setPopularShrines([]);
      setPopularStatus("error");
    }
  }, []);

  React.useEffect(() => {
    void loadPopularShrines();
  }, [loadPopularShrines]);

  React.useEffect(() => {
    if (selectedShrineId && !mapPoints.some((point) => point.id === selectedShrineId)) {
      setSelectedShrineId(null);
    }
  }, [mapPoints, selectedShrineId]);

  const selectedMapShrine = findShrineMapPointById(mapPoints, selectedShrineId);

  const filtered = filterShrines(SHRINES, { query: q, filters });

  // 人気の神社は実API(/populars/)由来のため、静的SHRINESとのID空間が重ならず
  // 重複除外の必要がない。神社一覧のフィルタ・ソート結果(filtered)はそのまま表示する。
  const visibleShrines = filtered;

  return (
    <ScrollView style={styles.screen} contentContainerStyle={styles.content}>
      <Pressable onPress={() => (router.canGoBack() ? router.back() : router.replace("/"))} style={styles.back}>
        <Text style={styles.backText}>← 戻る</Text>
      </Pressable>

      <View style={styles.hero}>
        <Text style={styles.heroLead}>神社を探す</Text>
        <Text style={styles.heroTitle}>今の気持ちに合う神社を、{`\n`}静かに見つける</Text>
        <Text style={styles.heroSub}>地域やご利益、気になる言葉から、参拝先との接点を確認できます。</Text>
      </View>

      <View style={styles.summaryCard}>
        <Text style={styles.summaryLabel}>検索条件</Text>
        <Text style={styles.summaryText}>キーワード: {q || "なし"}</Text>
        {selected.length > 0 ? (
          <View style={styles.tagRow}>
            {selected.map((c) => (
              <View key={c} style={styles.tag}>
                <Text style={styles.tagText}>{c}</Text>
              </View>
            ))}
          </View>
        ) : (
          <Text style={styles.summaryHint}>条件なしで、登録神社を一覧表示しています。</Text>
        )}
      </View>

      {/* 神社一覧: 主要探索UI(docs/product/mobile-user-flow.md 10節) */}
      {visibleShrines.length > 0 ? (
        <>
          <View style={styles.sectionHeader}>
            <Text style={styles.sectionTitle}>神社一覧</Text>
            <Text style={styles.sectionCount}>{visibleShrines.length}件</Text>
          </View>

          <View style={styles.list}>
            {visibleShrines.map((s) => {
              const existsOnMap = mapPoints.some((point) => point.id === s.id);
              const isSelectedOnMap = existsOnMap && selectedShrineId === s.id;
              return (
                <View key={s.id} style={styles.card}>
                  <Pressable
                    onPress={() => {
                      trackShrineCardClick({ shrineId: s.id, position: "list" });
                      router.push(`/shrines/${s.id}`);
                    }}
                    style={({ pressed }) => [styles.cardMain, pressed && styles.cardPressed]}
                  >
                    <Image source={{ uri: s.imageUrl }} style={styles.cardImage} />
                    <View style={styles.cardBody}>
                      <Text style={styles.cardName}>{s.name}</Text>
                      <Text style={styles.cardArea}>{s.prefecture}</Text>
                      <View style={styles.miniTagRow}>
                        {s.tags.slice(0, 3).map((t) => (
                          <View key={t} style={styles.miniTag}>
                            <Text style={styles.miniTagText}>{t}</Text>
                          </View>
                        ))}
                      </View>
                    </View>
                    <Text accessibilityElementsHidden style={styles.chevron}>
                      ›
                    </Text>
                  </Pressable>

                  <View style={styles.cardMapActionRow}>
                    <Button
                      title={isSelectedOnMap ? "地図で選択中" : "地図で選択"}
                      variant="outline"
                      size="compact"
                      disabled={!existsOnMap}
                      onPress={() => setSelectedShrineId(s.id)}
                      accessibilityLabel={
                        !existsOnMap
                          ? `${s.name}は地図に表示されていません`
                          : isSelectedOnMap
                            ? `${s.name}を地図で選択中`
                            : `${s.name}を地図で選択`
                      }
                    />
                  </View>
                </View>
              );
            })}
          </View>
        </>
      ) : (
        <View style={styles.list}>
          <StateCard
            title="条件に一致する神社が見つかりませんでした"
            description="条件を変えると、他の神社が見つかる場合があります。"
          />
        </View>
      )}

      {selectedMapShrine ? (
        <View style={styles.selectedShrineWrap}>
          <SelectedShrineMapCard
            shrine={selectedMapShrine}
            onDetail={() => {
              trackShrineCardClick({ shrineId: selectedMapShrine.id, position: "map" });
              router.push(`/shrines/${selectedMapShrine.id}`);
            }}
          />
        </View>
      ) : null}

      <View style={styles.popularSection}>
        <View style={styles.sectionHeader}>
          <Text style={styles.sectionTitle}>人気の神社</Text>
          <Text style={styles.sectionCount}>{popularStatus === "ready" ? `${popularShrines.length}件` : ""}</Text>
        </View>

        {popularStatus === "loading" ? (
          <StateCard title="人気の神社を読み込み中" description="しばらくお待ちください。" />
        ) : null}

        {popularStatus === "error" ? (
          <View style={styles.mapErrorWrap}>
            <StateCard title="人気の神社を読み込めませんでした" description="通信状況を確認して、もう一度お試しください。" />
            <Button
              title="もう一度試す"
              variant="outline"
              size="compact"
              onPress={() => void loadPopularShrines()}
              accessibilityLabel="人気の神社をもう一度読み込む"
            />
          </View>
        ) : null}

        {popularStatus === "ready" && popularShrines.length === 0 ? (
          <StateCard title="人気の神社がまだありません" description="通常の一覧からも神社を探せます。" />
        ) : null}

        {popularStatus === "ready" && popularShrines.length > 0 ? (
          <View style={styles.popularList}>
            {popularShrines.map((s, index) => (
              <Pressable
                key={s.id}
                onPress={() => {
                  trackShrineCardClick({ shrineId: s.id, position: "popular" });
                  router.push(`/shrines/${s.id}`);
                }}
                style={({ pressed }) => [styles.popularCard, pressed && styles.cardPressed]}
              >
                <Text style={styles.popularRank}>{index + 1}</Text>
                <View style={styles.cardBody}>
                  <Text style={styles.cardName}>{s.name}</Text>
                  {s.address ? (
                    <Text style={styles.cardArea} numberOfLines={1}>
                      {s.address}
                    </Text>
                  ) : null}
                </View>
                <Text accessibilityElementsHidden style={styles.chevron}>
                  ›
                </Text>
              </Pressable>
            ))}
          </View>
        ) : null}
      </View>

      {/* 地図で探す: 補助表示。Webはstyle URL未設定の間、AndroidはGoogle Maps APIキー未設定の間、
          セクション自体を表示しない(isSearchMapSectionAvailable、lib/shrineMap.ts参照) */}
      {isMapSectionAvailable ? (
        <View style={styles.mapSection}>
          <View style={styles.sectionHeader}>
            <Text style={styles.sectionTitle}>地図で探す</Text>
          </View>

          {mapStatus === "loading" ? (
            <StateCard title="地図を読み込み中" description="神社の位置情報を確認しています。" />
          ) : null}

          {mapStatus === "error" ? (
            <View style={styles.mapErrorWrap}>
              <StateCard title="地図を読み込めませんでした" description="通信状況を確認して、もう一度お試しください。" />
              <Button title="もう一度試す" variant="outline" size="compact" onPress={() => void loadMapPoints()} accessibilityLabel="地図をもう一度読み込む" />
            </View>
          ) : null}

          {mapStatus === "ready" && mapPoints.length === 0 ? (
            <StateCard
              title="神社が見つかりませんでした"
              description="この検索条件に一致する神社がありません。条件を変えてもう一度お試しください。"
            />
          ) : null}

          {mapStatus === "ready" && mapPoints.length > 0 ? (
            <ShrineSearchMap points={mapPoints} selectedId={selectedShrineId} onSelect={setSelectedShrineId} />
          ) : null}
        </View>
      ) : null}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  screen: {
    flex: 1,
    backgroundColor: theme.outside,
  },
  content: {
    width: "100%",
    maxWidth: 430,
    alignSelf: "center",
    minHeight: "100%",
    backgroundColor: theme.background,
    paddingHorizontal: 20,
    paddingTop: 22,
    paddingBottom: 96,
  },
  back: {
    alignSelf: "flex-start",
    borderWidth: 1,
    borderColor: theme.borderGold,
    paddingVertical: 8,
    paddingHorizontal: 13,
    borderRadius: 999,
    backgroundColor: "transparent",
    marginBottom: 28,
  },
  backText: {
    color: theme.gold,
    fontSize: 13,
    fontWeight: "800",
  },
  hero: {
    paddingBottom: 22,
    gap: 10,
  },
  heroLead: {
    color: theme.mutedSoft,
    fontSize: 14,
    fontWeight: "800",
    letterSpacing: 1,
  },
  heroTitle: {
    color: theme.text,
    fontSize: 28,
    fontWeight: "900",
    lineHeight: 38,
    letterSpacing: 0.8,
  },
  heroSub: {
    color: theme.muted,
    fontSize: 13,
    lineHeight: 21,
    fontWeight: "600",
  },
  summaryCard: {
    backgroundColor: theme.surface,
    borderWidth: 1,
    borderColor: theme.border,
    borderRadius: 20,
    padding: 16,
    marginBottom: 24,
  },
  summaryLabel: {
    color: theme.mutedSoft,
    fontSize: 11,
    fontWeight: "800",
    letterSpacing: 1.8,
    marginBottom: 8,
  },
  summaryText: {
    color: theme.text,
    fontSize: 14,
    fontWeight: "800",
  },
  summaryHint: {
    color: theme.muted,
    fontSize: 12,
    lineHeight: 18,
    marginTop: 8,
    fontWeight: "600",
  },
  tagRow: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 8,
    marginTop: 12,
  },
  mapSection: {
    marginBottom: 26,
  },
  mapErrorWrap: {
    gap: spacing.mdGap,
    alignItems: "flex-start",
  },
  selectedShrineWrap: {
    marginBottom: 24,
  },
  tag: {
    borderRadius: 999,
    backgroundColor: theme.surfaceSoft,
    borderWidth: 1,
    borderColor: theme.borderGold,
    paddingHorizontal: 10,
    paddingVertical: 6,
  },
  tagText: {
    color: theme.gold,
    fontSize: 12,
    fontWeight: "700",
  },
  sectionHeader: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    marginBottom: 12,
  },
  sectionTitle: {
    color: theme.text,
    fontSize: 18,
    fontWeight: "900",
  },
  sectionCount: {
    color: theme.gold,
    fontSize: 13,
    fontWeight: "800",
  },
  popularSection: {
    marginBottom: 26,
  },
  popularList: {
    gap: 10,
  },
  popularCard: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: theme.surface,
    borderWidth: 1,
    borderColor: theme.borderGold,
    borderRadius: 18,
    padding: 12,
    gap: 12,
  },
  popularRank: {
    width: 28,
    height: 28,
    borderRadius: 999,
    backgroundColor: theme.surfaceSoft,
    color: theme.gold,
    fontSize: 13,
    fontWeight: "900",
    lineHeight: 28,
    textAlign: "center",
  },
  list: {
    gap: 12,
    marginBottom: 26,
  },
  card: {
    backgroundColor: theme.surface,
    borderWidth: 1,
    borderColor: theme.borderHeader,
    borderRadius: 18,
    padding: 12,
    gap: 10,
  },
  cardMain: {
    flexDirection: "row",
    alignItems: "center",
    gap: 12,
  },
  cardMapActionRow: {
    flexDirection: "row",
  },
  cardPressed: {
    opacity: 0.74,
  },
  cardImage: {
    width: 76,
    height: 64,
    borderRadius: 14,
    backgroundColor: theme.surfaceSoft,
  },
  cardBody: {
    flex: 1,
    gap: 4,
  },
  cardName: {
    color: theme.text,
    fontSize: 16,
    fontWeight: "900",
  },
  cardArea: {
    color: theme.muted,
    fontSize: 12,
    fontWeight: "700",
  },
  miniTagRow: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 6,
    marginTop: 4,
  },
  miniTag: {
    borderRadius: 999,
    backgroundColor: theme.surfaceSoft,
    borderWidth: 1,
    borderColor: theme.borderSoft,
    paddingHorizontal: 8,
    paddingVertical: 3,
  },
  miniTagText: {
    color: theme.goldSoft,
    fontSize: 11,
    fontWeight: "700",
  },
  chevron: {
    color: theme.gold,
    fontSize: 22,
    fontWeight: "800",
  },
});
