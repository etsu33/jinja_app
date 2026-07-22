import type { DirectionCandidatePosition } from "../../../../../packages/shared/directionAnalytics";
import { isValidDirectionReference, type DirectionReference } from "../../../../../packages/shared/directionReference";

export type DirectionRouteContext = {
  matched: boolean;
  candidatePosition: DirectionCandidatePosition;
};

export function withDirectionRouteContext(
  href: string | null | undefined,
  reference: DirectionReference | null | undefined,
  candidatePosition: DirectionCandidatePosition,
): string | null | undefined {
  if (!href || !isValidDirectionReference(reference)) return href;
  const [pathAndQuery, hash = ""] = href.split("#", 2);
  const [path, query = ""] = pathAndQuery.split("?", 2);
  const params = new URLSearchParams(query);
  params.set("direction_matched", reference.matched ? "1" : "0");
  params.set("direction_position", candidatePosition);
  return `${path}?${params.toString()}${hash ? `#${hash}` : ""}`;
}

export function parseDirectionRouteContext(input: {
  direction_matched?: string | null;
  direction_position?: string | null;
}): DirectionRouteContext | null {
  if (input.direction_matched !== "1" && input.direction_matched !== "0") return null;
  if (input.direction_position !== "hero" && input.direction_position !== "other") return null;
  return {
    matched: input.direction_matched === "1",
    candidatePosition: input.direction_position,
  };
}
