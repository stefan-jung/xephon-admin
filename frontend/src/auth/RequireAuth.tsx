import React, { useEffect, useState } from "react";
import { keycloak } from "./keycloak";

export function RequireAuth({ children }: { children: React.ReactNode }) {
  const [checked, setChecked] = useState(false);

  useEffect(() => {
    if (!keycloak.authenticated) {
      keycloak.login();
    } else {
      setChecked(true);
    }
  }, []);

  if (!checked) return <p className="p-8 text-gray-500">Redirecting to login…</p>;
  return <>{children}</>;
}
