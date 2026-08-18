import { Suspense } from "react";
import CompassClient from "@/features/compass/CompassClient";

export default function Page() {
  return (
    <Suspense fallback={null}>
      <CompassClient />
    </Suspense>
  );
}
