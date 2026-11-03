import { mediaUrl } from '../api/axios';
import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import api from '../api/axios';
import useAuthStore from '../store/authStore';

export default function WishlistPage() {
  const { t } = useTranslation();
  const { isAuthenticated } = useAuthStore();
  const navigate = useNavigate();
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!isAuthenticated) { navigate('/login'); return; }
    api.get('/interactions/wishlist/')
      .then(res => { setItems(res.data.results || res.data); setLoading(false); })
      .catch(() => setLoading(false));
  }, [isAuthenticated, navigate]);

  const removeItem = async (courseId) => {
    await api.delete(`/interactions/wishlist/${courseId}/remove/`);
    setItems(prev => prev.filter(i => i.course !== courseId));
  };

  if (loading) return <div className="loading">{t('common.loading')}</div>;

  return (
    <div className="wishlist-page">
      <div className="container">
        <h1 className="page-title">❤️ {t('wishlist.title')}</h1>

        {items.length === 0 ? (
          <div className="empty-state">
            <div className="empty-icon">💔</div>
            <h3>{t('wishlist.empty')}</h3>
            <Link to="/courses" className="btn-primary">{t('wishlist.explore')}</Link>
          </div>
        ) : (
          <div className="courses-grid">
            {items.map(item => (
              <div key={item.id} className="course-card wishlist-card">
                <Link to={`/courses/${item.course_slug}`} className="course-thumb">
                  {item.course_thumbnail
                    ? <img src={mediaUrl(item.course_thumbnail)} alt={item.course_title} />
                    : <div className="thumb-placeholder" />}
                </Link>
                <div className="course-info">
                  <h3>{item.course_title}</h3>
                  <button className="btn-danger-sm" onClick={() => removeItem(item.course)}>
                    ❌ {t('common.remove')}
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
