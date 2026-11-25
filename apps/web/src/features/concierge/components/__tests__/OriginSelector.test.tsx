import { act, fireEvent, render, screen } from "@testing-library/react";
import { vi } from "vitest";
import OriginSelector from "../OriginSelector";

describe("OriginSelector", () => {
  it("拒否後も手動入力へ切り替え、候補選択時だけ確定する", async () => {
    const onChange=vi.fn();
    vi.stubGlobal("fetch",vi.fn().mockResolvedValue({ok:true,json:async()=>({items:[{place_id:"1",name:"東京駅",lat:35.68,lng:139.77,type:"station"}]})}));
    render(<OriginSelector origin={null} onChange={onChange} onUseDevice={()=>undefined} deviceError="位置情報が拒否されました。"/>);
    fireEvent.click(screen.getByText("現在地を使用"));
    expect(screen.getByRole("alert")).toHaveTextContent("位置情報が拒否されました");
    // 代替導線は既存のラジオ（エラー領域内に重複CTAを置かない）
    fireEvent.click(screen.getByRole("radio", { name: "駅名・住所から指定" }));
    fireEvent.change(screen.getByLabelText("駅名または住所"),{target:{value:"東京駅"}});
    expect(onChange).not.toHaveBeenLastCalledWith(expect.objectContaining({latitude:expect.any(Number)}));
    await act(async()=>{await new Promise(resolve=>setTimeout(resolve,450));});
    fireEvent.click(await screen.findByText("東京駅"));
    expect(onChange).toHaveBeenLastCalledWith(expect.objectContaining({source:"station",latitude:35.68}));
  });

  it("都道府県をおおよその地点として選択できる", () => {
    const onChange=vi.fn();
    render(<OriginSelector origin={null} onChange={onChange} onUseDevice={()=>undefined}/>);
    fireEvent.click(screen.getByText("都道府県から指定"));
    fireEvent.change(screen.getByLabelText("都道府県"),{target:{value:"東京都"}});
    expect(onChange).toHaveBeenLastCalledWith(expect.objectContaining({source:"prefecture",accuracy:"approximate"}));
  });

  it("選択方法、候補、検索状態、現在値を読み上げ可能にする", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true, json: async () => ({ items: [{ place_id: "1", name: "東京駅", lat: 35.68, lng: 139.77, type: "station" }] }) }));
    const onChange = vi.fn();
    render(<OriginSelector origin={null} onChange={onChange} onUseDevice={() => undefined} />);

    const manual = screen.getByRole("radio", { name: "駅名・住所から指定" });
    expect(manual).toHaveAttribute("aria-checked", "false");
    fireEvent.click(manual);
    expect(manual).toHaveAttribute("aria-checked", "true");

    const input = screen.getByRole("combobox", { name: "駅名または住所" });
    expect(input).toHaveAttribute("aria-expanded", "false");
    fireEvent.change(input, { target: { value: "東京駅" } });
    await act(async () => { await new Promise((resolve) => setTimeout(resolve, 450)); });
    expect(await screen.findByRole("option", { name: "東京駅" })).toBeInTheDocument();
    expect(input).toHaveAttribute("aria-expanded", "true");
    expect(screen.getAllByRole("status").length).toBeGreaterThanOrEqual(2);
    expect(screen.getByText("1件の候補が見つかりました。候補を選択してください。")).toBeInTheDocument();
  });

  it("操作要素は44px相当の最小タップ領域とフォーカス表示を持つ", () => {
    render(<OriginSelector origin={null} onChange={() => undefined} onUseDevice={() => undefined} />);
    for (const radio of screen.getAllByRole("radio")) {
      expect(radio.className).toContain("min-h-11");
      expect(radio.className).toContain("focus-visible:ring-2");
    }
  });

  it.each([
    ["500", vi.fn().mockResolvedValue({ ok: false })],
    ["タイムアウト相当", vi.fn().mockRejectedValue(new Error("timeout"))],
  ])("ジオコード%sでもエラーを案内し、相談に必要な他の操作を妨げない", async (_label, fetchMock) => {
    vi.stubGlobal("fetch", fetchMock);
    const onChange = vi.fn();
    render(<OriginSelector origin={null} onChange={onChange} onUseDevice={() => undefined} />);
    fireEvent.click(screen.getByRole("radio", { name: "駅名・住所から指定" }));
    fireEvent.change(screen.getByLabelText("駅名または住所"), { target: { value: "失敗地点" } });
    await act(async () => { await new Promise((resolve) => setTimeout(resolve, 450)); });
    expect(screen.getByText("候補を検索できませんでした。相談はそのまま続けられます。")).toBeInTheDocument();
    expect(onChange).not.toHaveBeenCalledWith(expect.objectContaining({ latitude: expect.any(Number) }));
    expect(screen.getByRole("radio", { name: "方位情報を使用しない" })).toBeEnabled();
  });
});
