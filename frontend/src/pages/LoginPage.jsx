import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import useAuthStore from '../store/authStore';

export default function LoginPage() {
  const navigate = useNavigate();
  const next = new URLSearchParams(window.location.search).get('next');
  const { login, loading } = useAuthStore();
  const [form, setForm] = useState({ email: '', password: '' });
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    try {
      await login(form.email, form.password);

      navigate(next?.startsWith('/') && !next.startsWith('//') ? next : '/profile');
    } catch (err) {
      const msg = err.response?.data?.detail || "Email yoki parol noto'g'ri";
      if (msg.includes('Qurilmalar soni')) {
        setError(msg);
      } else {
        setError("Email yoki parol noto'g'ri");
      }
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-card">
        <h1>Kirish</h1>
        <p>Platformaga kirish uchun ma'lumotlaringizni kiriting</p>

        {error && <div className="error-banner">{error}</div>}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Email</label>
            <input
              type="email"
              placeholder="email@example.com"
              value={form.email}
              onChange={e => setForm({ ...form, email: e.target.value })}
              required
            />
          </div>
          <div className="form-group">
            <label>Parol</label>
            <input
              type="password"
              placeholder="••••••••"
              value={form.password}
              onChange={e => setForm({ ...form, password: e.target.value })}
              required
            />
          </div>
          <button type="submit" className="btn-primary" disabled={loading}>
            {loading ? 'Kirilmoqda...' : 'Kirish'}
          </button>
        </form>

        <p className="auth-link">
          Akkaunt yo'qmi? <Link to="/register">Ro'yxatdan o'ting</Link>
        </p>
      </div>
    </div>
  );
}
