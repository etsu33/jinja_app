// apps/mobile/components/search/ShrineSearchMap.native.tsx
import * as React from "react";
import { StyleSheet, View } from "react-native";
import MapView, { Marker, type Region } from "react-native-maps";

import { kamimusubiDark as theme } from "../../design/theme";
import { radius } from "../../design/radius";
import { prefectureOrigin } from "../../../../packages/shared/userOrigin";
import type { ShrineMapPoint } from "../../lib/shrineMap";

const FALLBACK_ORIGIN = prefectureOrigin("東京都");
const FALLBACK_REGION: Region = {
  latitude: FALLBACK_ORIGIN?.latitude ?? 35.6762,
  longitude: FALLBACK_ORIGIN?.longitude ?? 139.6503,
  latitudeDelta: 0.15,
  longitudeDelta: 0.15,
};

const MIN_DELTA = 0.05;
const REGION_PADDING = 1.4;

function buildInitialRegion(points: ShrineMapPoint[]): Region {
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

type Props = {
  points: ShrineMapPoint[];
  selectedId: string | null;
  onSelect: (id: string) => void;
};

export function ShrineSearchMap({ points, selectedId, onSelect }: Props) {
  const initialRegion = React.useMemo(() => buildInitialRegion(points), [points]);

  return (
    <View style={styles.wrap} accessibilityLabel="検索結果の神社を地図で見る">
      <MapView style={styles.map} initialRegion={initialRegion}>
        {points.map((point) => {
          const selected = point.id === selectedId;
          return (
            <Marker
              key={point.id}
              coordinate={{ latitude: point.latitude, longitude: point.longitude }}
              title={point.name}
              onPress={() => onSelect(point.id)}
              accessibilityRole="button"
              accessibilityLabel={`${point.name}を選択`}
              accessibilityState={{ selected }}
              opacity={selected ? 1 : 0.85}
              zIndex={selected ? 1 : 0}
            />
          );
        })}
      </MapView>
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
});
