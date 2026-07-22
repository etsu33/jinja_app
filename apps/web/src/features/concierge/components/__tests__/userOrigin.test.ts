import { describe, expect, it } from "vitest";
import { prefectureOrigin, toOriginPayload } from "../../../../../../../packages/shared/userOrigin";
describe("userOrigin payload",()=>{it("未選択・無効化時は座標を送らない",()=>expect(toOriginPayload(null)).toBeUndefined());it("選択済み地点を既存lat/lng境界へ変換する",()=>expect(toOriginPayload(prefectureOrigin("大阪府"))).toEqual({lat:34.6937,lng:135.5023}));});
