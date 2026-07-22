import type { UserOrigin } from "../../../packages/shared/userOrigin";
let currentOrigin: UserOrigin | null = null;
export const setOriginSession = (origin: UserOrigin | null) => { currentOrigin = origin; };
export const getOriginSession = () => currentOrigin;
