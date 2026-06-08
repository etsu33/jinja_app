import SignupForm from "../../signup/SignupForm";
import { normalizeReturnToParam } from "@/lib/nav/returnTo";

export default async function Page({
  searchParams,
}: {
  searchParams?: Promise<Record<string, string | string[] | undefined>> | Record<string, string | string[] | undefined>;
}) {
  const returnTo = await normalizeReturnToParam(searchParams);
  return <SignupForm returnTo={returnTo} />;
}
