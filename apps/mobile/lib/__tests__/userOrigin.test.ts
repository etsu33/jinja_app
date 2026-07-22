import { describe, expect, it } from "vitest";
import { prefectureOrigin, toOriginPayload } from "../../../../packages/shared/userOrigin";
describe("userOrigin",()=>{
  it("確定済み地点だけpayloadへ変換する",()=>{expect(toOriginPayload(prefectureOrigin("東京都"))).toEqual({lat:35.6762,lng:139.6503});expect(toOriginPayload(null)).toBeUndefined();});
  it("都道府県を概算精度として扱う",()=>expect(prefectureOrigin("東京都")).toMatchObject({source:"prefecture",accuracy:"approximate"}));
});
