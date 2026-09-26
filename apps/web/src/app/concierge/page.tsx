import { Suspense } from "react";
import ConciergeClientFull from "./ConciergeClientFull";
import ConciergeRouteFallback from "./ConciergeRouteFallback";

export default function Page() {
  return (
    <Suspense fallback={<ConciergeRouteFallback />}>
      <ConciergeClientFull />
    </Suspense>
  );
}
