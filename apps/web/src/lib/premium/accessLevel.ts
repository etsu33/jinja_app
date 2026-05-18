export type AccessLevel = "anonymous" | "free" | "premium";

export type BillingStatusLike = {
  plan?: string | null;
  is_active?: boolean | null;
};

export function resolveAccessLevel(
  billingStatus: BillingStatusLike | null | undefined,
  isAuthenticated: boolean,
): AccessLevel {
  if (!isAuthenticated) {
    return "anonymous";
  }

  if (billingStatus?.plan === "premium" && billingStatus.is_active === true) {
    return "premium";
  }

  return "free";
}
