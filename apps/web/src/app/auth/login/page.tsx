import LoginForm from "../../login/LoginForm";
import { normalizeReturnToParam } from "@/lib/nav/returnTo";

export default async function Page({
  searchParams,
}: {
  searchParams?: Promise<Record<string, string | string[] | undefined>> | Record<string, string | string[] | undefined>;
}) {
  const returnTo = await normalizeReturnToParam(searchParams);
  return <LoginForm next={returnTo} />;
}
