// apps/mobile/components/search/ShrineSearchMap.native.tsx
import * as React from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";
import MapView, { Marker, type Region } from "react-native-maps";

import { kamimusubiDark as theme } from "../../design/theme";
import { radius } from "../../design/radius";
import { spacing } from "../../design/spacing";
import { prefectureOrigin } from "../../../../packages/shared/userOrigin";
import { hasValidCoordinates, type ShrineSearchMapProps } from "../../lib/shrineMap";
import { trackMapMarkerSelect } from "../../lib/searchAnalytics";

const FALLBACK_ORIGIN = prefectureOrigin("東京都");
const FALLBACK_REGION: Region = {
  latitude: FALLBACK_ORIGIN?.latitude ?? 35.6762,
  longitude: FALLBACK_ORIGIN?.longitude ?? 139.6503,
  latitudeDelta: 0.15,
  longitudeDelta: 0.15,
};

const MIN_DELTA = 0.05;
const REGION_PADDING = 1.4;

type MappablePoint = { id: string; latitude: number; longitude: number };

function buildInitialRegion(points: MappablePoint[]): Region {
  if (points.length === 0) return FALLBACK_REGION;

  let minLat = points[0].latitude;
  let maxLat = points[0].latitude;
  let minLng = points[0].longitude;
  let maxLng = points[0].longitude;

  for (const point of points) {
    minLat = Math.min(minLat, point.latitude);
    maxLat = Math.max(maxLat, point.latitude);
    minLng = Math.min(minLng, point.longitude);
    maxLng = Math.max(maxLng, point.longitude);
  }

  const latitude = (minLat + maxLat) / 2;
  const longitude = (minLng + maxLng) / 2;
  const latitudeDelta = Math.max((maxLat - minLat) * REGION_PADDING, MIN_DELTA);
  const longitudeDelta = Math.max((maxLng - minLng) * REGION_PADDING, MIN_DELTA);

  return { latitude, longitude, latitudeDelta, longitudeDelta };
}

export function ShrineSearchMap({ points, selectedId, onSelect }: ShrineSearchMapProps) {
  // pointsの配列参照はSearch画面側でselectedShrineId変更時に変わらないため、
  // useMemoの依存をpointsのみにしてMapViewのinitialRegionが選択のたびに動かないようにする。
  const mappablePoints = React.useMemo(() => points.filter(hasValidCoordinates), [points]);
  const unmappablePoints = React.useMemo(() => points.filter((point) => !hasValidCoordinates(point)), [points]);
  const initialRegion = React.useMemo(() => buildInitialRegion(mappablePoints), [mappablePoints]);

  // Marker押下・座標欠損リスト押下は「地図で選んだ」という同一の探索行動のため、
  // 呼び出し元(神社一覧の「地図で選択」ボタン等)とは別に、ここで1箇所だけ計測する。
  const handleSelect = React.useCallback(
    (id: string) => {
      trackMapMarkerSelect({ shrineId: id });
      onSelect(id);
    },
    [onSelect],
  );

  return (
    <View>
      <View style={styles.wrap} accessibilityLabel="検索結果の神社を地図で見る">
        <MapView style={styles.map} initialRegion={initialRegion}>
          {mappablePoints.map((point) => {
            const selected = point.id === selectedId;
            return (
              <Marker
                key={point.id}
                coordinate={{ latitude: point.latitude, longitude: point.longitude }}
                title={point.name}
                onPress={() => handleSelect(point.id)}
                accessibilityRole="button"
                accessibilityLabel={selected ? `${point.name}を選択、選択中` : `${point.name}を選択`}
                accessibilityState={{ selected }}
                opacity={selected ? 1 : 0.85}
                zIndex={selected ? 1 : 0}
              />
            );
          })}
        </MapView>
      </View>

      {unmappablePoints.length > 0 ? (
        <View style={styles.noCoordSection}>
          <Text style={styles.noCoordLabel}>位置情報のない神社</Text>
          <View style={styles.noCoordList}>
            {unmappablePoints.map((point) => {
              const selected = point.id === selectedId;
              return (
                <Pressable
                  key={point.id}
                  onPress={() => handleSelect(point.id)}
                  accessibilityRole="button"
                  accessibilityLabel={selected ? `${point.name}を選択、選択中` : `${point.name}を選択`}
                  accessibilityState={{ selected }}
                  style={({ pressed }) => [
                    styles.noCoordItem,
                    selected && styles.noCoordItemSelected,
                    pressed && styles.noCoordItemPressed,
                  ]}
                >
                  <Text style={styles.noCoordItemText} numberOfLines={1}>
                    {point.name}
                    {selected ? "・選択中" : ""}
                  </Text>
                </Pressable>
              );
            })}
          </View>
        </View>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: {
    height: 240,
    borderRadius: radius.lg,
    overflow: "hidden",
    backgroundColor: theme.surfaceSoft,
  },
  map: {
    flex: 1,
  },
  noCoordSection: {
    marginTop: spacing.mdGap,
    gap: spacing.tightGap,
  },
  noCoordLabel: {
    color: theme.muted,
    fontSize: 12,
    fontWeight: "700",
  },
  noCoordList: {
    gap: spacing.tightGap,
  },
  noCoordItem: {
    borderRadius: radius.xs,
    borderWidth: 1,
    borderColor: theme.border,
    backgroundColor: theme.surface,
    paddingHorizontal: spacing.mdGap,
    paddingVertical: spacing.tightGap,
  },
  noCoordItemSelected: {
    borderColor: theme.borderGold,
  },
  noCoordItemPressed: {
    opacity: 0.74,
  },
  noCoordItemText: {
    color: theme.text,
    fontSize: 14,
    fontWeight: "800",
  },
});
