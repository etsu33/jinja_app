import { beforeEach, describe, expect, it, vi } from "vitest";
const {track}=vi.hoisted(()=>({track:vi.fn()}));vi.mock("../track",()=>({track}));
import { trackWebDirection } from "../directionEvents";
describe("direction analytics",()=>{beforeEach(()=>track.mockClear());it("個人情報を含まない共通契約だけを送る",()=>{trackWebDirection("direction_origin_result",{origin_type:"prefecture",result:"selected"});expect(track).toHaveBeenCalledWith("direction_origin_result",{platform:"web",origin_type:"prefecture",result:"selected"});});});
