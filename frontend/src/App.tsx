import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from './hooks/useAuth';
import { Loader } from 'lucide-react';
import Sidebar from './components/Sidebar';
import ProtectedRoute from './components/ProtectedRoute';
import ErrorBoundary from './components/ErrorBoundary';
import { ThemeProvider } from './components/ThemeProvider';
import { ToastProvider } from './components/ToastContainer';
import DashboardPage from './pages/DashboardPage';
import ChatPage from './pages/ChatPage';
import EntitiesPage from './pages/EntitiesPage';
import AutomationsPage from './pages/AutomationsPage';
import IntegrationsPage from './pages/IntegrationsPage';
import MemoryPage from './pages/MemoryPage';
import SettingsPage from './pages/SettingsPage';
import LoginPage from './pages/LoginPage';
import SignupPage from './pages/SignupPage';
import ProfilePage from './pages/ProfilePage';
import NotFound from './pages/NotFound';
import ServerError from './pages/ServerError';
import { ForgotPasswordPage } from './pages/ForgotPasswordPage';
import { ResetPasswordPage } from './pages/ResetPasswordPage';
import { VerifyEmailPage } from './pages/VerifyEmailPage';

export default function App() {
  const { isLoading, isAuthenticated } = useAuth();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
        <div className="text-center">
          <Loader className="text-purple-400 animate-spin size-12 mx-auto mb-4" />
          <p className="text-purple-300 text-lg font-medium">AI Agent</p>
          <p className="text-gray-400 text-sm mt-2">Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <ErrorBoundary>
      <ThemeProvider>
        <ToastProvider>
          <Routes>
            {/* Error Pages */}
            <Route path="/error" element={<ServerError />} />

            {/* Auth Routes */}
            <Route path="/login" element={isAuthenticated ? <Navigate to="/" replace /> : <LoginPage />} />
            <Route path="/signup" element={isAuthenticated ? <Navigate to="/" replace /> : <SignupPage />} />
            <Route path="/forgot-password" element={isAuthenticated ? <Navigate to="/" replace /> : <ForgotPasswordPage />} />
            <Route path="/reset-password" element={isAuthenticated ? <Navigate to="/" replace /> : <ResetPasswordPage />} />
            <Route path="/verify-email" element={<VerifyEmailPage />} />

            {/* Protected Routes with Sidebar */}
            <Route
              path="/*"
              element={
                <ProtectedRoute>
                  <div className="flex h-screen bg-gray-950">
                    <Sidebar />
                    <main className="flex-1 overflow-hidden">
                      <Routes>
                        <Route path="/" element={<DashboardPage />} />
                        <Route path="/chat" element={<ChatPage />} />
                        <Route path="/chat/:conversationId?" element={<ChatPage />} />
                        <Route path="/entities" element={<EntitiesPage />} />
                        <Route path="/automations" element={<AutomationsPage />} />
                        <Route path="/integrations" element={<IntegrationsPage />} />
                        <Route path="/memory" element={<MemoryPage />} />
                        <Route path="/settings" element={<SettingsPage />} />
                        <Route path="/profile" element={<ProfilePage />} />
                        <Route path="*" element={<NotFound />} />
                      </Routes>
                    </main>
                  </div>
                </ProtectedRoute>
              }
            />

            {/* 404 Fallback */}
            <Route path="*" element={<NotFound />} />
          </Routes>
        </ToastProvider>
      </ThemeProvider>
    </ErrorBoundary>
  );
}
