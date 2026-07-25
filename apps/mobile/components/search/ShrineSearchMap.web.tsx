// apps/mobile/components/search/ShrineSearchMap.web.tsx
import * as React from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";
import { MapLibreMap, Marker, type ErrorEvent } from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";

import { kamimusubiDark as theme } from "../../design/theme";
import { radius } from "../../design/radius";
import { spacing } from "../../design/spacing";
import {
  computeWebMapViewport,
  hasValidCoordinates,
  type ShrineMapPoint,
  type ShrineSearchMapProps,
} from "../../lib/shrineMap";

// 公開クライアント用のstyle URL。secretはコードへ直書きせず、未設定時は
// Mapを生成せず既存の一覧fallbackを表示する。domain制限・使用量制限は
// provider側の設定に委ねる(docs/audit/web-map-tile-provider-selection.md参照)。
const STYLE_URL = process.env.EXPO_PUBLIC_WEB_MAP_STYLE_URL;

function applyMarkerSelectedState(element: HTMLElement, selected: boolean): void {
  element.setAttribute("aria-pressed", selected ? "true" : "false");
  element.style.transform = selected ? "scale(1.35)" : "scale(1)";
  element.style.boxShadow = selected ? `0 0 0 3px ${theme.gold}` : "none";
  element.style.zIndex = selected ? "1" : "0";
}

function createMarkerElement(
  point: ShrineMapPoint,
  onSelectRef: React.MutableRefObject<(id: string) => void>,
): HTMLDivElement {
  const element = document.createElement("div");
  element.setAttribute("role", "button");
  element.setAttribute("tabIndex", "0");
  element.setAttribute("aria-label", `${point.name}を選択`);
  element.setAttribute("aria-pressed", "false");
  element.title = point.name;
  element.style.width = "16px";
  element.style.height = "16px";
  element.style.borderRadius = "999px";
  element.style.backgroundColor = theme.gold;
  element.style.border = `2px solid ${theme.background}`;
  element.style.boxSizing = "border-box";
  element.style.cursor = "pointer";
  element.style.transition = "transform 0.1s ease-out";

  const select = () => onSelectRef.current(point.id);
  element.addEventListener("click", select);
  element.addEventListener("keydown", (event) => {
    if (event.key === "Enter" || event.key === " " || event.key === "Spacebar") {
      event.preventDefault();
      select();
    }
  });

  return element;
}

export function ShrineSearchMap({ points, selectedId, onSelect }: ShrineSearchMapProps) {
  const containerRef = React.useRef<View>(null);
  const mapRef = React.useRef<MapLibreMap | null>(null);
  const markersRef = React.useRef<Map<string, Marker>>(new Map());
  const onSelectRef = React.useRef(onSelect);
  onSelectRef.current = onSelect;

  const [mapUnavailable, setMapUnavailable] = React.useState(false);

  const mappablePoints = React.useMemo(() => points.filter(hasValidCoordinates), [points]);
  const styleUrlConfigured = Boolean(STYLE_URL);
  const shouldAttemptMap = styleUrlConfigured && !mapUnavailable;

  const teardownMap = React.useCallback(() => {
    markersRef.current.forEach((marker) => marker.remove());
    markersRef.current.clear();
    mapRef.current?.remove();
    mapRef.current = null;
  }, []);

  // Unmount時のみ後片付けする。selectedId変更やpoints更新では実行しない。
  React.useEffect(() => {
    return () => teardownMap();
  }, [teardownMap]);

  // Mapの遅延生成とMarkerの同期。selectedIdはこのeffectの依存に含めず、
  // 選択状態の変更だけでMapやMarkerを作り直さないようにする。
  React.useEffect(() => {
    if (!shouldAttemptMap) return;

    if (!mapRef.current) {
      if (mappablePoints.length === 0) return;
      const containerEl = containerRef.current as unknown as HTMLElement | null;
      if (!containerEl) return;

      const viewport = computeWebMapViewport(mappablePoints);
      if (!viewport) return;

      try {
        const map = new MapLibreMap({
          container: containerEl,
          style: STYLE_URL as string,
          center: viewport.kind === "point" ? viewport.center : [mappablePoints[0].longitude, mappablePoints[0].latitude],
          zoom: viewport.kind === "point" ? viewport.zoom : 2,
        });

        map.on("error", (event: ErrorEvent) => {
          const message = String(event?.error?.message ?? "").toLowerCase();
          // 個別タイル1件の読み込み失敗だけではfallbackへ切り替えない。
          // styleそのものが読み込めない場合のみ一覧fallbackへ切り替える。
          if (message.includes("style") || message.includes("failed to fetch")) {
            teardownMap();
            setMapUnavailable(true);
          }
        });

        if (viewport.kind === "bounds") {
          map.fitBounds(viewport.bounds, { padding: viewport.padding, maxZoom: viewport.maxZoom, duration: 0 });
        }

        mapRef.current = map;
      } catch {
        setMapUnavailable(true);
        return;
      }
    } else if (mappablePoints.length > 0) {
      const viewport = computeWebMapViewport(mappablePoints);
      if (viewport?.kind === "bounds") {
        mapRef.current.fitBounds(viewport.bounds, { padding: viewport.padding, maxZoom: viewport.maxZoom, duration: 0 });
      } else if (viewport?.kind === "point") {
        mapRef.current.setCenter(viewport.center);
        mapRef.current.setZoom(viewport.zoom);
      }
    }

    const map = mapRef.current;
    if (!map) return;

    const nextIds = new Set(mappablePoints.map((point) => point.id));
    markersRef.current.forEach((marker, id) => {
      if (!nextIds.has(id)) {
        marker.remove();
        markersRef.current.delete(id);
      }
    });

    mappablePoints.forEach((point) => {
      const existing = markersRef.current.get(point.id);
      if (existing) {
        existing.setLngLat([point.longitude, point.latitude]);
        return;
      }
      const element = createMarkerElement(point, onSelectRef);
      applyMarkerSelectedState(element, point.id === selectedId);
      const marker = new Marker({ element }).setLngLat([point.longitude, point.latitude]).addTo(map);
      markersRef.current.set(point.id, marker);
    });
    // selectedIdは初期表示状態の付与にのみ使う。以降の更新は下の選択同期effectが担う。
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [mappablePoints, shouldAttemptMap, teardownMap]);

  // 選択状態の同期のみを行う。Marker・Mapの再生成は行わない。
  React.useEffect(() => {
    markersRef.current.forEach((marker, id) => {
      applyMarkerSelectedState(marker.getElement(), id === selectedId);
    });
  }, [selectedId]);

  const mapShown = shouldAttemptMap && mappablePoints.length > 0;
  const showMapUnavailableNotice = !styleUrlConfigured || mapUnavailable;
  const showNoCoordinatesNotice = !showMapUnavailableNotice && mappablePoints.length === 0;

  return (
    <View style={styles.wrap} accessibilityRole="summary" accessibilityLabel="検索結果の神社を地図で見る">
      {mapShown ? (
        <View ref={containerRef} style={styles.mapContainer} />
      ) : null}

      {showMapUnavailableNotice ? (
        <Text style={styles.notice}>地図を読み込めないため一覧を表示しています。</Text>
      ) : null}
      {showNoCoordinatesNotice ? (
        <Text style={styles.notice}>位置情報がないため一覧で表示しています。</Text>
      ) : null}

      {points.length > 0 ? (
        <View style={styles.list}>
          {points.map((point) => {
            const selected = point.id === selectedId;
            return (
              <Pressable
                key={point.id}
                onPress={() => onSelect(point.id)}
                accessibilityRole="button"
                accessibilityLabel={selected ? `${point.name}を選択、選択中` : `${point.name}を選択`}
                accessibilityState={{ selected }}
                style={({ pressed }) => [styles.item, selected && styles.itemSelected, pressed && styles.itemPressed]}
              >
                <View style={styles.itemHeader}>
                  <Text style={styles.itemName} numberOfLines={1}>
                    {point.name}
                  </Text>
                  {selected ? <Text style={styles.itemSelectedBadge}>選択中</Text> : null}
                </View>
                {point.address ? (
                  <Text style={styles.itemAddress} numberOfLines={1}>
                    {point.address}
                  </Text>
                ) : null}
              </Pressable>
            );
          })}
        </View>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: {
    borderRadius: radius.lg,
    backgroundColor: theme.surfaceSoft,
    padding: spacing.mdGap,
    gap: spacing.tightGap,
  },
  mapContainer: {
    height: 240,
    borderRadius: radius.lg,
    overflow: "hidden",
    backgroundColor: theme.surfaceSoft,
  },
  notice: {
    color: theme.muted,
    fontSize: 12,
    lineHeight: 18,
    fontWeight: "600",
  },
  list: {
    gap: spacing.tightGap,
  },
  item: {
    borderRadius: radius.xs,
    borderWidth: 1,
    borderColor: theme.border,
    backgroundColor: theme.surface,
    paddingHorizontal: spacing.mdGap,
    paddingVertical: spacing.tightGap,
  },
  itemSelected: {
    borderColor: theme.borderGold,
  },
  itemPressed: {
    opacity: 0.74,
  },
  itemHeader: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    gap: spacing.tightGap,
  },
  itemName: {
    color: theme.text,
    fontSize: 14,
    fontWeight: "800",
  },
  itemSelectedBadge: {
    color: theme.gold,
    fontSize: 11,
    fontWeight: "800",
  },
  itemAddress: {
    color: theme.muted,
    fontSize: 12,
    fontWeight: "600",
    marginTop: 2,
  },
});
