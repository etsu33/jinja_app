// apps/web/vitest.setup.ts
import * as matchers from "@testing-library/jest-dom/matchers";
import { expect, vi } from "vitest";

// `@testing-library/jest-dom/vitest` は内部で未宣言の `vitest` importを持ち、
// pnpm workspace統合後はphantom dependency解決でMobile側のvitest実体を拾ってしまう
// (SnapshotClientがモジュールスコープのシングルトンのため不整合が起きる)。
// このファイルが直接importしたexpect（Web側のvitest実体）へ明示登録することで回避する。
expect.extend(matchers);

// next/navigation の最低限モック
const _replace = vi.fn();
const _push = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace: _replace, push: _push }),
  useSearchParams: () => new URLSearchParams(),
  _mocks: { replace: _replace, push: _push },
}));

// 認証フックのデフォルトモック（各テストで _setAuth で上書き可）
vi.mock("@/lib/hooks/useAuth", () => {
  let state = {
    user: null,
    isLoggedIn: false,
    loading: false,
    logout: vi.fn(),
  };
  return {
    __esModule: true,
    useAuth: () => state,
    _setAuth: (next: Partial<typeof state>) => {
      state = { ...state, ...next };
    },
  };
});


vi.mock("@/lib/api/goshuin", async () => {
  const actual = await vi.importActual<any>("@/lib/api/goshuin");
  return {
    ...actual,
    fetchMyGoshuin: vi.fn().mockResolvedValue([]),
    uploadMyGoshuin: vi.fn(),
    deleteMyGoshuin: vi.fn(),
    updateMyGoshuinVisibility: vi.fn(),
  };
});

// ---- テスト中の console ノイズを抑える（必要なら）----
vi.spyOn(console, "error").mockImplementation(() => {});
vi.spyOn(console, "warn").mockImplementation(() => {});
