import { Routes, Route } from "react-router-dom";

import Home from "../pages/public/Home";
import Login from "../pages/public/Login";
import Register from "../pages/public/Register";
import JobDetails from "../pages/public/JobDetails";
import CompanyProfile from "../pages/public/CompanyProfile";
import SeekerDashboard from "../pages/seeker/SeekerDashboard";
import SeekerProfile from "../pages/seeker/SeekerProfile";
import SavedJobs from "../pages/seeker/SavedJobs";
import MyApplications from "../pages/seeker/MyApplications";
import EmployerDashboard from "../pages/employer/EmployerDashboard";
import JobApplicants from "../pages/employer/JobApplicants";
import CreateJob from "../pages/employer/CreateJob";
import EditJob from "../pages/employer/EditJob";
import ProtectedRoute from "./ProtectedRoute";

export default function AppRoutes() {
  return (
    <Routes>
      {/* Public marketplace */}
      <Route path="/" element={<Home />} />
      <Route path="/jobs/:id" element={<JobDetails />} />
      <Route path="/companies/:slug" element={<CompanyProfile />} />
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
        path="/seeker/profile"
        element={
          <ProtectedRoute role="seeker">
            <SeekerProfile />
          </ProtectedRoute>
        }
      />
      <Route
        path="/seeker/saved-jobs"
        element={
          <ProtectedRoute role="seeker">
            <SavedJobs />
          </ProtectedRoute>
        }
      />
      <Route
        path="/seeker/applications"
        element={
          <ProtectedRoute role="seeker">
            <MyApplications />
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
      <Route
        path="/employer/jobs/new"
        element={
          <ProtectedRoute role="employer">
            <CreateJob />
          </ProtectedRoute>
        }
      />
      <Route
        path="/employer/jobs/:id/edit"
        element={
          <ProtectedRoute role="employer">
            <EditJob />
          </ProtectedRoute>
        }
      />
      <Route
        path="/employer/jobs/:jobId/applicants"
        element={
          <ProtectedRoute role="employer">
            <JobApplicants />
          </ProtectedRoute>
        }
      />
    </Routes>
  );
}
