import { BrowserRouter, Routes, Route, Navigate, useLocation, Link } from 'react-router-dom';
import { useEffect, lazy, Suspense } from 'react';
import Navbar from './components/Navbar';
import Footer from './components/Footer';
import AppBackdrop from './components/AppBackdrop';
import MobileTabBar from './components/MobileTabBar';
import HomePage from './pages/HomePage';
const LoginPage = lazy(() => import('./pages/LoginPage'));
const RegisterPage = lazy(() => import('./pages/RegisterPage'));
const CoursePage = lazy(() => import('./pages/CoursePage'));
const CoursesListPage = lazy(() => import('./pages/CoursesListPage'));
const LessonPage = lazy(() => import('./pages/LessonPage'));
const PaymentPage = lazy(() => import('./pages/PaymentPage'));
const ProfilePage = lazy(() => import('./pages/ProfilePage'));
const WishlistPage = lazy(() => import('./pages/WishlistPage'));
import useAuthStore from './store/authStore';
import './App.css';
import './academy.css';
import './backdrop.css';
import './mobile.css';
const PaymentSuccessPage = lazy(() => import('./pages/PaymentSuccessPage'));

function App() {
  const { isAuthenticated, fetchProfile } = useAuthStore();

  useEffect(() => {
    if (isAuthenticated) fetchProfile();
  }, [isAuthenticated, fetchProfile]);

  return (
    <BrowserRouter>
      <AppBackdrop />
      <ScrollManager />
      <a className="skip-link" href="#main-content">Asosiy kontentga o‘tish</a>
      <Navbar />
      <main id="main-content">
        <Suspense fallback={<div className="loading">Sahifa yuklanmoqda…</div>}><Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route path="/courses" element={<CoursesListPage />} />
          <Route path="/courses/:slug" element={<CoursePage />} />
          <Route path="/lessons/:id" element={<Protected><LessonPage /></Protected>} />
          <Route path="/payment/success" element={<Protected><PaymentSuccessPage /></Protected>} />
          <Route path="/payment/:tariffId" element={<PaymentPage />} />
          <Route path="/profile" element={<ProfilePage />} />
          <Route path="/wishlist" element={<WishlistPage />} />
          <Route path="/tariffs" element={<Navigate to="/#tariffs" replace />} />
          <Route path="*" element={<div className="error-page"><h1>404</h1><p>Sahifa topilmadi</p><Link to="/courses" className="btn-primary">Kurslarni ko‘rish</Link></div>} />
        </Routes></Suspense>
      </main>
      <Footer />
      <MobileTabBar />
    </BrowserRouter>
  );
}

function Protected({ children }) {
  const { isAuthenticated } = useAuthStore();
  const location = useLocation();
  return isAuthenticated ? children : <Navigate to={`/login?next=${encodeURIComponent(location.pathname)}`} replace />;
}
function ScrollManager() {
  const { pathname, hash } = useLocation();
  useEffect(() => {
    if (!hash) { window.scrollTo(0, 0); return; }
    let count = 0;
    const timer = setInterval(() => {
      const target = document.getElementById(hash.slice(1));
      if (target) { target.scrollIntoView(); clearInterval(timer); }
      if (++count > 30) clearInterval(timer);
    }, 100);
    return () => clearInterval(timer);
  }, [pathname, hash]);
  return null;
}
export default App;
