import { BrowserRouter as Router, Route, Routes, Navigate, useLocation } from 'react-router-dom';
import LandingPage from './pages/LandingPage';
import ChatPage from './pages/Chat';
import SignupForm from './pages/Signup';
import { supabase } from './utils/supabase';
import { useEffect, useMemo, useState } from 'react';

function App() {
  const [session, setSession] = useState<any>(null);
  const [authInitialized, setAuthInitialized] = useState(false);

  useEffect(() => {
    supabase.auth.getSession().then(({ data: { session } }) => {
      setSession(session);
      setAuthInitialized(true);
    });

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((event, session) => {
      if (event === 'SIGNED_IN') {
        try {
          sessionStorage.setItem('justLoggedIn', '1');
        } catch {}
      }
      setSession(session);
      setAuthInitialized(true);
    });

    return () => subscription.unsubscribe();
  }, []);

  const location = useLocation();

  const isOAuthCallback = useMemo(() => {
    if (typeof window === 'undefined') return false;
    return (
      window.location.hash.includes('access_token') ||
      window.location.hash.includes('refresh_token') ||
      window.location.search.includes('code=')
    );
  }, [location.pathname, location.search, location.hash]);

  const shouldRedirectToChat = useMemo(() => {
    if (!session || typeof window === 'undefined') return false;
    const flag = sessionStorage.getItem('justLoggedIn') === '1';
    const fromSignup = location.pathname === '/signup';
    return flag || isOAuthCallback || fromSignup;
  }, [session, location.pathname, isOAuthCallback]);

  const ChatRouteElement = () => {
    if (isOAuthCallback) return <div />; // waiting for Supabase to finish parsing tokens
    if (!authInitialized) return <div />;
    return session ? <ChatPage /> : <Navigate to="/" />;
  };

  return (
    <Routes>
      <Route
        path="/"
        element={shouldRedirectToChat ? <Navigate to="/chat" replace /> : <LandingPage />}
      />
      <Route path="/chat" element={<ChatRouteElement />} />
      <Route path="/signup" element={<SignupForm />} />
    </Routes>
  );
}

function AppRouter() {
  return (
    <Router>
      <App />
    </Router>
  );
}

export default AppRouter;
