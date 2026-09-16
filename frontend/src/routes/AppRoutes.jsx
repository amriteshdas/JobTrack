import { Routes, Route } from "react-router-dom";

import Home from "../pages/public/Home";
import Login from "../pages/public/Login";
import Register from "../pages/public/Register";
import SeekerDashboard from "../pages/seeker/SeekerDashboard";
import EmployerDashboard from "../pages/employer/EmployerDashboard";
import ProtectedRoute from "./ProtectedRoute";

export default function AppRoutes() {
  return (
    <Routes>
      {/* Public */}
      <Route path="/" element={<Home />} />
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />

      {/* Role-gated. The `role` prop is UX only -- the backend enforces
          the same rule independently on every API call. */}
      <Route
        path="/seeker"
        element={
          <ProtectedRoute role="seeker">
            <SeekerDashboard />
          </ProtectedRoute>
        }
      />
      <Route
        path="/employer"
        element={
          <ProtectedRoute role="employer">
            <EmployerDashboard />
          </ProtectedRoute>
        }
      />
    </Routes>
  );
}
