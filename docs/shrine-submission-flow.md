import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ShrineSearchResultPage } from "../page";

jest.mock("../../api/shrines", () => ({
  fetchShrines: jest.fn(),
}));

import { fetchShrines } from "../../api/shrines";

const mockedFetchShrines = fetchShrines as jest.MockedFunction<typeof fetchShrines>;

describe("ShrineSearchResultPage", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test("qありで0件ならCTAを表示する", async () => {
    mockedFetchShrines.mockResolvedValueOnce({
      data: [],
      totalCount: 0,
    });

    render(<ShrineSearchResultPage searchParams={{ q: "テスト" }} />);

    expect(await screen.findByText("お探しの神社が見つかりませんか？")).toBeInTheDocument();

    const cta = await screen.findByRole("button", { name: "神社を追加する" });
    expect(cta).toBeInTheDocument();
  });

  test("submitted=1 & status=pending なら審査中メッセージを表示する", async () => {
    mockedFetchShrines.mockResolvedValueOnce({
      data: [],
      totalCount: 0,
    });

    render(
      <ShrineSearchResultPage
        searchParams={{ submitted: "1", status: "pending", q: "未登録テスト神社20260419" }}
      />,
    );

    await waitFor(() => {
      expect(mockedFetchShrines).toHaveBeenCalled();
    });

    expect(
      await screen.findByText("「未登録テスト神社20260419」の投稿を受け付けました。現在審査中です。"),
    ).toBeInTheDocument();
  });
});

# 神社追加導線の現行仕様

## 目的
検索で神社が見つからない場合、その場で追加でき、投稿後の状態が分かる導線を1本成立させる。

## 現行仕様
- 神社追加の主導線は `/shrines` の検索0件時CTAとする
- CTA文言は「お探しの神社が見つかりませんか？ 神社を追加する」
- CTA押下時は `/shrines/new?returnTo=...` に遷移する
- 投稿後は `/shrines` に戻し、一覧上部に受付メッセージを表示する
- 投稿直後の状態表示は `審査中` とする
- 審査中データは公開検索結果に混ざらない前提で扱う

## duplicate_candidate 契約
- `POST /api/shrine-submissions/` は、既存 `Shrine` と重複の可能性がある場合 `400` を返す
- response は以下の形式とする

```json
{
  "code": "duplicate_candidate",
  "message": "この神社はすでに登録されている可能性があります。",
  "candidates": [
    {
      "id": 23,
      "name": "神田神社（神田明神）",
      "address": "東京都千代田区外神田2-16-2"
    }
  ]
}
```

- `candidates` は既存 `Shrine` の簡易情報配列とする
- candidate が1件のときは詳細導線を表示する
- candidate が複数件のときは `/shrines?q=...` への候補一覧導線を表示する
- `duplicate_candidate` は serializer の入力バリデーションではなく、view / service 側の重複候補判定で返す

## 確認済み
- `/shrines` の検索0件時にCTAが表示される
- CTAから `/shrines/new?returnTo=...` に遷移する
- 投稿後に `/shrines?...&submitted=1&status=pending` に戻る
- `/shrines` 上部に受付メッセージが表示される
- 投稿直後データは `Shrine` 公開検索には混ざらない
- duplicate_candidate の1件候補時は詳細導線に遷移する

## 未確認
- duplicate_candidate の複数候補ケースは未確認
- ローカル seed データ条件未成立のため、実運用または追加データ投入後に確認予定

- 公開検索対象は `Shrine`
- 投稿直後データは公開マスター未反映のため、審査完了までは検索結果に出ない
- 重複投稿抑止は Phase 2 で正規化・精度改善を行う
- duplicate candidate 判定では、神社名の空白・括弧表記ゆれと、住所の空白・ハイフンゆれを service 層で正規化して比較する
