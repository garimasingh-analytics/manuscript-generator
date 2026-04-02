import React from "react";
import { Navigate, Route, Routes, useLocation } from "react-router-dom";
import { useAuth } from "./lib/auth";
import { AuthPage } from "./pages/AuthPage";
import { ProjectsPage } from "./pages/ProjectsPage";
import { UploadReportPage } from "./pages/UploadReportPage";
import { LiteraturePage } from "./pages/LiteraturePage";
import { ManuscriptPage } from "./pages/ManuscriptPage";

function Protected({ children }: { children: React.ReactNode }) {
  const { token } = useAuth();
  const loc = useLocation();
  if (!token) return <Navigate to="/" replace state={{ from: loc.pathname }} />;
  return <>{children}</>;
}

export function App() {
  return (
    <Routes>
      <Route path="/" element={<AuthPage />} />
      <Route
        path="/projects"
        element={
          <Protected>
            <ProjectsPage />
          </Protected>
        }
      />
      <Route
        path="/projects/:projectId/upload"
        element={
          <Protected>
            <UploadReportPage />
          </Protected>
        }
      />
      <Route
        path="/projects/:projectId/literature"
        element={
          <Protected>
            <LiteraturePage />
          </Protected>
        }
      />
      <Route
        path="/projects/:projectId/manuscript"
        element={
          <Protected>
            <ManuscriptPage />
          </Protected>
        }
      />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

