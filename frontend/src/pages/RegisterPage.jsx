import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import useAuthStore from '../store/authStore';

export default function RegisterPage() {
  const navigate = useNavigate();
  const { register, loading } = useAuthStore();
  const [form, setForm] = useState({ email: '', full_name: '', phone: '', password: '', password2: '' });
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    if (form.password !== form.password2) {
      setError('Parollar mos kelmadi');
      return;
    }
    try {
      await register(form);
      navigate('/');
    } catch (err) {
      const data = err.response?.data;
      if (data?.email) setError(data.email[0]);
      else if (data?.password) setError(data.password[0]);
      else setError("Xatolik yuz berdi. Qayta urinib ko'ring.");
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-card">
        <h1>Ro'yxatdan o'tish</h1>
        <p>Yangi akkaunt yarating</p>

        {error && <div className="error-banner">{error}</div>}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>To'liq ism</label>
            <input
              placeholder="Ism Familiya"
              value={form.full_name}
              onChange={e => setForm({ ...form, full_name: e.target.value })}
              required
            />
          </div>
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
            <label>Telefon (ixtiyoriy)</label>
            <input
              placeholder="+998 90 123 45 67"
              value={form.phone}
              onChange={e => setForm({ ...form, phone: e.target.value })}
            />
          </div>
          <div className="form-group">
            <label>Parol</label>
            <input
              type="password"
              placeholder="Kamida 8 ta belgi"
              value={form.password}
              onChange={e => setForm({ ...form, password: e.target.value })}
              required
            />
          </div>
          <div className="form-group">
            <label>Parolni tasdiqlang</label>
            <input
              type="password"
              placeholder="••••••••"
              value={form.password2}
              onChange={e => setForm({ ...form, password2: e.target.value })}
              required
            />
          </div>
          <button type="submit" className="btn-primary" disabled={loading}>
            {loading ? "Yaratilmoqda..." : "Ro'yxatdan o'tish"}
          </button>
        </form>

        <p className="auth-link">
          Akkaunt bormi? <Link to="/login">Kirish</Link>
        </p>
      </div>
    </div>
  );
}
