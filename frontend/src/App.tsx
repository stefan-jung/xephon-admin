import { NavLink, Route, Routes } from "react-router-dom";
import { RequireAuth } from "./auth/RequireAuth";
import { useCurrentUser } from "./auth/CurrentUserContext";
import { keycloak } from "./auth/keycloak";
import { AuditLogPage } from "./pages/AuditLogPage";
import { ServicesPage } from "./pages/ServicesPage";
import { UserPage } from "./pages/UserPage";
import { UsersPage } from "./pages/UsersPage";

function Topbar() {
  const user = useCurrentUser();
  return (
    <header className="topbar">
      <NavLink to="/" className="topbar-brand">
        Xephon Admin
      </NavLink>
      <nav className="topbar-nav hidden md:flex ml-6 gap-1">
        <NavLink
          to="/users"
          className={({ isActive }) => `topbar-nav-link ${isActive ? "active" : ""}`}
        >
          Users
        </NavLink>
        <NavLink
          to="/services"
          className={({ isActive }) => `topbar-nav-link ${isActive ? "active" : ""}`}
        >
          Services
        </NavLink>
        <NavLink
          to="/audit"
          className={({ isActive }) => `topbar-nav-link ${isActive ? "active" : ""}`}
        >
          Audit Log
        </NavLink>
      </nav>
      <div className="ml-auto flex items-center gap-3 text-sm">
        <span className="text-white/70">{user.name ?? user.email}</span>
        <button
          className="btn btn-ghost btn-sm text-white/80 hover:text-white hover:bg-white/10"
          onClick={() => keycloak.logout()}
        >
          Sign out
        </button>
      </div>
    </header>
  );
}

export default function App() {
  return (
    <RequireAuth>
      <Topbar />
      <main className="main-content">
        <Routes>
          <Route path="/" element={<UsersPage />} />
          <Route path="/users" element={<UsersPage />} />
          <Route path="/users/:userId" element={<UserPage />} />
          <Route path="/services" element={<ServicesPage />} />
          <Route path="/audit" element={<AuditLogPage />} />
        </Routes>
      </main>
    </RequireAuth>
  );
}
