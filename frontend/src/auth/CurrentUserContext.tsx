import React, { createContext, useContext } from "react";
import { keycloak } from "./keycloak";

interface CurrentUser {
  id: string;
  email: string | undefined;
  name: string | undefined;
  isAdmin: boolean;
}

const CurrentUserContext = createContext<CurrentUser | null>(null);

export function CurrentUserProvider({ children }: { children: React.ReactNode }) {
  const payload = keycloak.tokenParsed as Record<string, unknown> | undefined;
  const realmRoles = (payload?.realm_access as { roles?: string[] })?.roles ?? [];
  const user: CurrentUser = {
    id: (payload?.sub as string) ?? "",
    email: payload?.email as string | undefined,
    name: (payload?.name as string | undefined) ?? (payload?.preferred_username as string | undefined),
    isAdmin: realmRoles.includes("xephon:admin"),
  };
  return <CurrentUserContext.Provider value={user}>{children}</CurrentUserContext.Provider>;
}

export function useCurrentUser(): CurrentUser {
  const ctx = useContext(CurrentUserContext);
  if (!ctx) throw new Error("useCurrentUser must be inside CurrentUserProvider");
  return ctx;
}
