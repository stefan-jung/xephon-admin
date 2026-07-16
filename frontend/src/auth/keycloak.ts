import Keycloak from "keycloak-js";

export const keycloak = new Keycloak({
  url: import.meta.env.VITE_KEYCLOAK_URL ?? "http://localhost:8080",
  realm: import.meta.env.VITE_KEYCLOAK_REALM ?? "xephon",
  clientId: import.meta.env.VITE_KEYCLOAK_CLIENT_ID ?? "xephon-admin",
});

let initPromise: Promise<boolean> | null = null;

export function initAuth(): Promise<boolean> {
  if (initPromise === null) {
    initPromise = keycloak.init({ onLoad: "check-sso", pkceMethod: "S256" });
  }
  return initPromise;
}
