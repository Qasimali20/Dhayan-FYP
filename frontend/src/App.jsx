import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import "./styles/app.css";

import { AuthProvider } from "./hooks/useAuth";
import { ChildProvider } from "./hooks/useChild";
import ProtectedRoute from "./components/ProtectedRoute";
import Layout from "./components/Layout";

import Login from "./pages/login";
import Signup from "./pages/Signup";
import ForgotPassword from "./pages/ForgotPassword";
import Dashboard from "./pages/Dashboard";
import TherapistConsole from "./pages/TherapistConsole";
import GameRouter from "./pages/GameRouter";
import JaGame from "./pages/JaGame";
import MatchingGame from "./pages/games/MatchingGame";
import MemoryMatchGame from "./pages/games/MemoryMatchGame";
import ObjectDiscovery from "./pages/games/ObjectDiscovery";
import ProblemSolving from "./pages/games/ProblemSolving";
import SpeechTherapy from "./pages/games/SpeechTherapy";

function ProtectedLayout({ children }) {
  return (
    <ProtectedRoute>
      <ChildProvider>
        <Layout>{children}</Layout>
      </ChildProvider>
    </ProtectedRoute>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          {/* Public routes */}
          <Route path="/login" element={<Login />} />
          <Route path="/signup" element={<Signup />} />
          <Route path="/forgot-password" element={<ForgotPassword />} />

          {/* Protected routes with layout */}
          <Route path="/dashboard" element={<ProtectedLayout><Dashboard /></ProtectedLayout>} />
          <Route path="/therapist" element={<ProtectedLayout><TherapistConsole /></ProtectedLayout>} />
          <Route path="/games" element={<ProtectedLayout><GameRouter /></ProtectedLayout>} />
          <Route path="/games/ja" element={<ProtectedLayout><JaGame /></ProtectedLayout>} />
          <Route path="/games/matching" element={<ProtectedLayout><MatchingGame /></ProtectedLayout>} />
          <Route path="/games/memory-match" element={<ProtectedLayout><MemoryMatchGame /></ProtectedLayout>} />
          <Route path="/games/object-discovery" element={<ProtectedLayout><ObjectDiscovery /></ProtectedLayout>} />
          <Route path="/games/problem-solving" element={<ProtectedLayout><ProblemSolving /></ProtectedLayout>} />
          <Route path="/speech-therapy" element={<ProtectedLayout><SpeechTherapy /></ProtectedLayout>} />

          {/* Default redirect */}
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}
