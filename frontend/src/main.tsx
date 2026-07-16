import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";

import App from "./App";
import { CurrentUserProvider } from "./auth/CurrentUserContext";
import { initAuth } from "./auth/keycloak";
import "./index.css";

initAuth().then(() => {
  ReactDOM.createRoot(document.getElementById("root")!).render(
    <React.StrictMode>
      <BrowserRouter>
        <CurrentUserProvider>
          <App />
        </CurrentUserProvider>
      </BrowserRouter>
    </React.StrictMode>,
  );
});
