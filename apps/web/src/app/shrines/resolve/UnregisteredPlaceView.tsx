// apps/web/src/app/shrines/resolve/UnregisteredPlaceView.tsx
//
// Shrine マスタ未登録の Place を、作成せずに表示する（Shrine マスタの新規作成は staff 限定）。
// `POST /api/places/resolve/` が `registered: false` を返したときに使う。

export type UnregisteredPlace = {
  place_id: string;
  name_jp?: string | null;
  address?: string | null;
};

export function buildGoogleMapsPlaceHref(place: UnregisteredPlace): string {
  const q = new URLSearchParams({
    api: "1",
    query: place.name_jp?.trim() || place.address?.trim() || place.place_id,
    query_place_id: place.place_id,
  });
  return `https://www.google.com/maps/search/?${q.toString()}`;
}

export function UnregisteredPlaceView({ place }: { place: UnregisteredPlace }) {
  const name = place.name_jp?.trim() || "名称未設定の場所";
  const address = place.address?.trim();

  return (
    <main className="mx-auto max-w-md space-y-3 p-6">
      <h1 className="text-lg font-bold text-[var(--kt-color-text-primary)]">{name}</h1>
      {address ? <p className="text-sm text-[var(--kt-color-text-secondary)]">{address}</p> : null}
      <p className="rounded-xl border border-[var(--kt-color-border-default)] bg-[var(--kt-color-surface-default)] p-3 text-xs text-[var(--kt-color-text-secondary)]">
        この場所はまだ神社として登録されていません。お気に入りや参拝記録は、登録済みの神社で使えます。
      </p>
      <a
        href={buildGoogleMapsPlaceHref(place)}
        target="_blank"
        rel="noopener noreferrer"
        className="inline-block rounded-md bg-[var(--kt-color-surface-emphasis)] px-3 py-2 text-xs text-[var(--kt-color-text-primary)] hover:bg-[var(--kt-color-surface-emphasis-hover)]"
      >
        Google マップで見る
      </a>
    </main>
  );
}
