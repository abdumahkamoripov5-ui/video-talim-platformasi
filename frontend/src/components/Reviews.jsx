import { mediaUrl } from '../api/axios';
import { useState, useEffect, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import api from '../api/axios';
import useAuthStore from '../store/authStore';

export default function Reviews({ courseId }) {
  const { t } = useTranslation();
  const { isAuthenticated } = useAuthStore();
  const [reviews, setReviews] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [rating, setRating] = useState(5);
  const [comment, setComment] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const load = useCallback(() => {
    api.get(`/interactions/courses/${courseId}/reviews/`)
      .then(res => setReviews(res.data.results || res.data))
      .catch(() => {});
  }, [courseId]);

  useEffect(() => { load(); }, [load]);

  const submit = async (e) => {
    e.preventDefault();
    if (!isAuthenticated) return;
    setSubmitting(true);
    try {
      await api.post(`/interactions/courses/${courseId}/reviews/`, { rating, comment });
      setShowForm(false);
      setComment('');
      load();
    } finally { setSubmitting(false); }
  };

  return (
    <div className="reviews-section">
      <div className="reviews-header">
        <h2>💬 {t('course.all_reviews')} ({reviews.length})</h2>
        {isAuthenticated && !showForm && (
          <button className="btn-primary-sm" onClick={() => setShowForm(true)}>
            ✨ {t('course.add_review')}
          </button>
        )}
      </div>

      {showForm && (
        <form className="review-form" onSubmit={submit}>
          <label>{t('course.your_rating')}</label>
          <div className="stars-input">
            {[1, 2, 3, 4, 5].map(n => (
              <button
                type="button" key={n}
                onClick={() => setRating(n)}
                className={`star-btn ${n <= rating ? 'active' : ''}`}
              >
                ⭐
              </button>
            ))}
          </div>
          <label>{t('course.comment')}</label>
          <textarea
            value={comment}
            onChange={(e) => setComment(e.target.value)}
            placeholder={t('course.comment')}
            rows={3}
          />
          <div className="form-actions">
            <button type="submit" className="btn-primary" disabled={submitting}>
              {t('course.submit')}
            </button>
            <button type="button" className="btn-outline-sm" onClick={() => setShowForm(false)}>
              {t('common.cancel')}
            </button>
          </div>
        </form>
      )}

      {reviews.length === 0 ? (
        <p className="empty">{t('course.no_reviews')}</p>
      ) : (
        <div className="reviews-list">
          {reviews.map(r => (
            <div key={r.id} className="review-item">
              <div className="review-avatar">
                {r.user_avatar
                  ? <img src={mediaUrl(r.user_avatar)} alt="" />
                  : <span>{r.user_name?.charAt(0).toUpperCase()}</span>
                }
              </div>
              <div className="review-body">
                <div className="review-meta">
                  <b>{r.user_name}</b>
                  <span className="review-stars">{'⭐'.repeat(r.rating)}</span>
                  <span className="review-date">{new Date(r.created_at).toLocaleDateString('uz-UZ')}</span>
                </div>
                {r.comment && <p>{r.comment}</p>}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
