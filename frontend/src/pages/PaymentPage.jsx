import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import api from '../api/axios';
import useAuthStore from '../store/authStore';

const PROVIDERS = [
  { id: 'payme', label: 'Payme', color: '#00CCAA' },
  { id: 'click', label: 'Click', color: '#0099FF' },
  { id: 'uzum', label: 'Uzum Bank', color: '#7B2FBE' },
];

export default function PaymentPage() {
  const { tariffId } = useParams();
  const navigate = useNavigate();
  const { isAuthenticated } = useAuthStore();
  const [tariff, setTariff] = useState(null);
  const [provider, setProvider] = useState('payme');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!isAuthenticated) { navigate(`/login?next=/payment/${tariffId}`); return; }
    api.get('/payments/tariffs/')
      .then(res => {
        const list = res.data.results || res.data;
        const found = list.find(t => String(t.id) === String(tariffId));
        if (!found) navigate('/');
        else setTariff(found);
      }).catch(() => setError('Tariflar yuklanmadi. Sahifani yangilang.'));
  }, [tariffId, isAuthenticated, navigate]);

  const handlePay = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await api.post('/payments/create/', {
        tariff_id: tariff.id,
        provider,
      });
      window.location.href = res.data.payment_url;
    } catch (err) {
      setError(err.response?.data?.detail || "To'lov yaratishda xatolik. Qayta urinib ko'ring.");
      setLoading(false);
    }
  };

  if (!tariff) return <div className="loading" role="status">{error || 'Yuklanmoqda...'}</div>;

  return (
    <div className="payment-page">
      <div className="container">
        <div className="payment-card">
          <h1>To'lov</h1>

          <div className="tariff-summary">
            <h3>{tariff.name}</h3>
            <div className="tariff-price-big">
              {Number(tariff.price).toLocaleString('uz-UZ')} so'm
            </div>
            <p>{tariff.duration_days} kunlik obuna</p>
          </div>

          <div className="provider-select">
            <h3>To'lov tizimini tanlang</h3>
            <div className="provider-list">
              {PROVIDERS.map(p => (
                <button
                  key={p.id}
                  className={`provider-btn ${provider === p.id ? 'active' : ''}`}
                  style={{ '--provider-color': p.color }}
                  onClick={() => setProvider(p.id)}
                >
                  {p.label}
                </button>
              ))}
            </div>
          </div>

          {error && <div className="error-banner">{error}</div>}

          <button
            className="btn-primary btn-pay"
            onClick={handlePay}
            disabled={loading}
          >
            {loading ? "Yo'naltirilmoqda..." : `${provider.charAt(0).toUpperCase() + provider.slice(1)} orqali to'lash`}
          </button>

          <p className="pay-note">
            To'lovdan so'ng obuna avtomatik faollashadi
          </p>
        </div>
      </div>
    </div>
  );
}
