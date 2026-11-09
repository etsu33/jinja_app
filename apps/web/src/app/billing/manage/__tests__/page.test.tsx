import { describe, expect, it, vi } from "vitest";

const redirectMock = vi.fn();
vi.mock("next/navigation", () => ({ redirect: (path: string) => redirectMock(path) }));

import BillingManagePage from "../page";

describe("/billing/manage", () => {
  it("月額の管理画面を廃止したので、プラン状況のページへ送る", () => {
    BillingManagePage();

    expect(redirectMock).toHaveBeenCalledWith("/billing");
  });
});
