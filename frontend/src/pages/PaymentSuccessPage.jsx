import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import api from '../api/axios';
import useAuthStore from '../store/authStore';
import Icon from '../components/Icon';
export default function PaymentSuccessPage() {
  const { fetchProfile } = useAuthStore();
  const [state, setState] = useState('checking');
  const [retry, setRetry] = useState(0);
  useEffect(() => {
    let alive = true; let attempts = 0; let done = false;
    const check = async () => {
      if (done) return;
      try {
        const { data } = await api.get('/payments/history/');
        const payments = data.results || data;
        if (!alive) return;
        if (payments[0]?.status === 'paid') { done = true; setState('paid'); await fetchProfile(); return; }
        if (++attempts >= 12) { done = true; setState('pending'); }
      } catch { if (alive) setState('error'); }
    };
    check();
    const timer = setInterval(check, 5000);
    return () => { alive = false; clearInterval(timer); };
  }, [fetchProfile, retry]);
  return <div className="error-page"><Icon name={state === 'paid' ? 'check' : 'clock'} size={50} /><h2>{state === 'paid' ? 'Obunangiz faollashdi!' : state === 'checking' ? 'To‘lov tasdig‘ini kutyapmiz…' : 'To‘lov holatini tekshiring'}</h2><p className="notice">{state === 'paid' ? 'Video darslarni tomosha qilishni boshlashingiz mumkin.' : 'Obuna faqat to‘lov tizimi tasdiqlagach faollashadi. To‘lovlaringizni shaxsiy kabinetda ko‘ring.'}</p><Link to={state === 'paid' ? '/courses' : '/profile'} className="btn-primary">{state === 'paid' ? 'Kurslarga o‘tish' : 'Shaxsiy kabinet'}</Link>{state !== 'paid' && <button className="btn-outline" onClick={() => { setState('checking'); setRetry(r => r+1); }}>Qayta tekshirish</button>}</div>;
}
