// ...（省略せず全体必要だが長いので要点のみ変更）
import { getShrineFavoriteStateServer } from "@/lib/api/favorites.server";

// 既存コード...

  const nextPath = buildShrineHref(numericId, { query: Object.keys(query).length ? query : undefined });

  // ★ 追加: favorite状態をSSRで取得
  let favoriteInitial = false;
  let favoriteGuestMode = true;
  try {
    const favState = await getShrineFavoriteStateServer(numericId);
    favoriteInitial = favState.initial;
    favoriteGuestMode = favState.guestMode;
  } catch {
    favoriteInitial = false;
    favoriteGuestMode = true;
  }

  // ...中略...

          saveActionNode={
            <ShrineSaveButton
              shrineId={numericId}
              nextPath={nextPath}
              initial={favoriteInitial}
              guestMode={favoriteGuestMode}
            />
          }
        />
