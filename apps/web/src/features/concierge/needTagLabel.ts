import { NEED_DISPLAY_LABELS, labelNeedDisplayTag } from "@/features/concierge/copy/needDisplayCopy";

export const NEED_TAG_LABEL = NEED_DISPLAY_LABELS;

export function labelNeedTag(tag: string): string {
  return labelNeedDisplayTag(tag);
}
