import { Routes, Route } from "react-router-dom";
import Home from "../pages/public/Home";

/**
 * Route definitions live in their own file, separate from App.jsx, so that
 * as the app grows into public/seeker/employer route groups (Phase 4+),
 * this file — not App.jsx — is what changes. App.jsx stays a thin shell
 * (providers, layout) for the whole project's life.
 *
 * Only one route exists right now on purpose: Phase 1 proves the wiring
 * works, it doesn't build the marketplace.
 */
export default function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
    </Routes>
  );
}
