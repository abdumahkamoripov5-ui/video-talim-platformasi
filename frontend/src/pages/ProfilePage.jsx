import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api, { downloadFile } from '../api/axios';
import useAuthStore from '../store/authStore';

export default function ProfilePage() {
  const navigate = useNavigate();
  const { user, isAuthenticated, logout, fetchProfile } = useAuthStore();
  const [error, setError] = useState('');
  const [devices, setDevices] = useState([]);
  const [payments, setPayments] = useState([]);
  const [enrollments, setEnrollments] = useState([]);
  const [certificates, setCertificates] = useState([]);

  useEffect(() => {
    if (!isAuthenticated) { navigate('/login'); return; }
    fetchProfile();
    Promise.all([
      api.get('/users/devices/'),
      api.get('/payments/history/'),
      api.get('/courses/enrollments/'),
      api.get('/interactions/certificates/'),
    ]).then(([d, p, e, c]) => {
      setDevices(d.data.results || d.data);
      setPayments(p.data.results || p.data);
      setEnrollments(e.data.results || e.data);
      setCertificates(c.data.results || c.data);
    }).catch(() => setError('Profil ma’lumotlari yuklanmadi. Sahifani yangilang.'));
  }, [isAuthenticated, navigate, fetchProfile]);

  const removeDevice = async (id) => {
    await api.delete(`/users/devices/${id}/remove/`);
    setDevices(prev => prev.filter(d => d.id !== id));
  };

  if (!user) return <div className="loading">Yuklanmoqda...</div>;

  return (
    <div className="profile-page">
      <div className="container">
        <div className="profile-header">
          <div className="avatar-circle">
            {user.full_name?.charAt(0).toUpperCase()}
          </div>
          <div>
            <h1>{user.full_name}</h1>
            <p>{user.email}</p>
            <div className={`sub-badge ${user.has_active_subscription ? 'active' : 'inactive'}`}>
              {user.has_active_subscription
                ? `Obuna faol — ${(user.subscription_end ? new Date(user.subscription_end).toLocaleDateString('uz-UZ') : 'Administrator')}`
                : 'Obuna faol emas'}
            </div>
          </div>
          <button className="btn-outline logout-btn" onClick={async () => { await logout(); navigate('/'); }}>
            Chiqish
          </button>
        </div>

        {error && <div role="alert" className="error-banner">{error}</div>}
        {/* Kurslar progressi */}
        <section className="profile-section">
          <h2>Kurslarim</h2>
          {enrollments.length === 0 ? (
            <p className="empty">Hali hech qanday kursga yozilmagansiz</p>
          ) : (
            <div className="enrollments-list">
              {enrollments.map(e => (
                <div key={e.id} className="enrollment-item">
                  <span>{e.course_title}</span>
                  <div className="mini-progress">
                    <div className="mini-fill" style={{ width: `${e.progress}%` }} />
                  </div>
                  <span>{e.progress}%</span>
                </div>
              ))}
            </div>
          )}
        </section>

        {/* Sertifikatlar */}
        <section className="profile-section">
          <h2>🏆 Sertifikatlarim ({certificates.length})</h2>
          {certificates.length === 0 ? (
            <p className="empty">Hali sertifikatlar yo'q. Kursni tugating va sertifikat oling!</p>
          ) : (
            <div className="certificates-grid">
              {certificates.map(cert => (
                <div key={cert.id} className="certificate-card">
                  <div className="cert-icon">🏆</div>
                  <h4>{cert.course_title}</h4>
                  <p className="cert-num">№ {cert.certificate_number}</p>
                  <p className="cert-date">{new Date(cert.issued_at).toLocaleDateString('uz-UZ')}</p>
                  <button
                    onClick={() => downloadFile(`/interactions/certificates/${cert.id}/download/`, `sertifikat-${cert.certificate_number}.pdf`).catch(() => alert('Faylni yuklab bo‘lmadi'))}
                    className="btn-primary-sm"
                  >
                    Yuklab olish
                  </button>
                </div>
              ))}
            </div>
          )}
        </section>

        {/* Qurilmalar */}
        <section className="profile-section">
          <h2>Qurilmalar ({devices.length}/2)</h2>
          {devices.map(device => (
            <div key={device.id} className="device-item">
              <div>
                <b>{device.device_name || 'Noma\'lum qurilma'}</b>
                <p>IP: {device.ip_address} — So'nggi faollik: {new Date(device.last_seen).toLocaleString('uz-UZ')}</p>
              </div>
              <button className="btn-danger-sm" onClick={() => removeDevice(device.id)}>
                O'chirish
              </button>
            </div>
          ))}
        </section>

        {/* To'lovlar tarixi */}
        <section className="profile-section">
          <h2>To'lovlar tarixi</h2>
          {payments.length === 0 ? (
            <p className="empty">To'lovlar tarixi yo'q</p>
          ) : (
            <table className="payments-table">
              <thead>
                <tr>
                  <th>Tarif</th>
                  <th>Summa</th>
                  <th>Tizim</th>
                  <th>Holat</th>
                  <th>Sana</th>
                </tr>
              </thead>
              <tbody>
                {payments.map(p => (
                  <tr key={p.id}>
                    <td>{p.tariff_name}</td>
                    <td>{Number(p.amount).toLocaleString('uz-UZ')} so'm</td>
                    <td>{p.provider_display}</td>
                    <td className={`status-${p.status}`}>{p.status_display}</td>
                    <td>{new Date(p.created_at).toLocaleDateString('uz-UZ')}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </section>
      </div>
    </div>
  );
}
