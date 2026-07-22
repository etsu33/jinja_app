import { beforeEach, describe, expect, it, vi } from "vitest";
const {track}=vi.hoisted(()=>({track:vi.fn()}));vi.mock("../analytics",()=>({track}));
import { trackMobileDirection } from "../directionEvents";
describe("direction analytics",()=>{beforeEach(()=>track.mockClear());it("個人情報を含まない共通契約だけを送る",()=>{trackMobileDirection("direction_condition_submitted",{has_visit_date:true,has_origin:true});expect(track).toHaveBeenCalledWith("direction_condition_submitted",{platform:"mobile",has_visit_date:true,has_origin:true});});});
