import { act, fireEvent, render, screen } from "@testing-library/react";
import { vi } from "vitest";
import OriginSelector from "../OriginSelector";

describe("OriginSelector", () => {
  it("拒否後も手動入力へ切り替え、候補選択時だけ確定する", async () => {
    const onChange=vi.fn();
    vi.stubGlobal("fetch",vi.fn().mockResolvedValue({ok:true,json:async()=>({items:[{place_id:"1",name:"東京駅",lat:35.68,lng:139.77,type:"station"}]})}));
    render(<OriginSelector origin={null} onChange={onChange} onUseDevice={()=>undefined} deviceError="位置情報が拒否されました。"/>);
    fireEvent.click(screen.getByText("現在地を使用"));
    expect(screen.getByText(/手動入力を選択できます/)).toBeInTheDocument();
    fireEvent.click(screen.getByText("駅名・住所から指定"));
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
});
