import { mediaUrl } from '../api/axios';
import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import api, { downloadFile } from '../api/axios';
import useAuthStore from '../store/authStore';
import Reviews from '../components/Reviews';

function formatDuration(seconds) {
  if (!seconds) return '';
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${m}:${String(s).padStart(2, '0')}`;
}

export default function CoursePage() {
  const { slug } = useParams();
  const navigate = useNavigate();
  const { user, isAuthenticated } = useAuthStore();
  const [course, setCourse] = useState(null);
  const [actionError, setActionError] = useState('');
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get(`/courses/${slug}/`)
      .then(res => { setCourse(res.data); setLoading(false); })
      .catch(() => navigate('/'));
  }, [slug, navigate]);

  const enroll = async () => {
    if (!isAuthenticated) return navigate('/login');
    setBusy(true); setActionError('');
    try {
      await api.post('/courses/enrollments/', { course: course.id });
      setCourse(prev => ({ ...prev, is_enrolled: true }));
    } catch { setActionError('Kursga yozilish amalga oshmadi. Qayta urinib ko‘ring.'); }
    finally { setBusy(false); }
  };

  const toggleWishlist = async () => {
    if (!isAuthenticated) return navigate('/login');
    setBusy(true); setActionError('');
    try {
    if (course.is_wishlisted) {
      await api.delete(`/interactions/wishlist/${course.id}/remove/`);
      setCourse(prev => ({ ...prev, is_wishlisted: false }));
    } else {
      await api.post('/interactions/wishlist/', { course: course.id });
      setCourse(prev => ({ ...prev, is_wishlisted: true }));
    }
    } catch { setActionError('Sevimlilarni yangilab bo‘lmadi.'); } finally { setBusy(false); }
  };

  const claimCertificate = async () => {
    try {
      const res = await api.post(`/interactions/certificates/issue/${course.id}/`);
      await downloadFile(`/interactions/certificates/${res.data.id}/download/`, 'sertifikat.pdf');
    } catch (err) {
      alert(err.response?.data?.detail || 'Xatolik');
    }
  };

  if (loading) return <div className="loading">Yuklanmoqda...</div>;
  if (!course) return null;

  const completedCount = course.lessons?.filter(l => l.is_completed).length || 0;
  const totalCount = course.lessons?.length || 0;

  return (
    <div className="course-page">
      <div className="container">
        <div className="lesson-breadcrumb"><a href="/courses">Kurslar</a> / {course.category?.name || "Video kurs"}</div>
        {actionError && <p role="alert" className="error-banner">{actionError}</p>}
        <div className="course-header">
          <div className="course-header-info">
            <h1>{course.title}</h1>
            <p className="instructor">O'qituvchi: {course.instructor}</p>
            <p className="description">{course.description}</p>
            <div className="course-stats">
              <span>📚 {totalCount} ta dars</span>
              {course.average_rating > 0 && (
                <span>⭐ {course.average_rating} ({course.reviews_count} sharh)</span>
              )}
              {course.is_enrolled && (
                <span className="progress-stat">{completedCount}/{totalCount} dars — {course.progress}%</span>
              )}
            </div>
            <div className="course-action-btns">
              {!course.is_enrolled ? (
                <button className="btn-primary" onClick={enroll} disabled={busy}>
                  {isAuthenticated ? "Kursga yozilish" : "Kirish kerak"}
                </button>
              ) : (
                <>
                  <div className="enrolled-badge">✔ Yozilgansiz</div>
                  {course.progress === 100 && (
                    <button className="btn-primary" onClick={claimCertificate}>
                      🏆 Sertifikat olish
                    </button>
                  )}
                </>
              )}
              <button
                className={`wishlist-btn ${course.is_wishlisted ? 'active' : ''}`}
                onClick={toggleWishlist} disabled={busy}
                title={course.is_wishlisted ? "Olib tashlash" : "Sevimlilarga qo'shish"}
              >
                {course.is_wishlisted ? '❤️' : '🤍'}
              </button>
            </div>
          </div>
          {course.thumbnail && (
            <img
              src={mediaUrl(course.thumbnail)}
              alt={course.title}
              className="course-cover"
            />
          )}
        </div>

        {/* Progress bar */}
        {course.is_enrolled && (
          <div className="course-progress-bar">
            <div className="progress-fill" style={{ width: `${course.progress}%` }} />
          </div>
        )}

        {/* Darslar ro'yxati */}
        <div className="lessons-list">
          <h2>Darslar</h2>
          {course.lessons?.map((lesson, idx) => (
            <LessonRow
              key={lesson.id}
              lesson={lesson}
              index={idx + 1}
              isEnrolled={course.is_enrolled}
              hasSubscription={user?.has_active_subscription}
            />
          ))}
        </div>

        {/* Reviews */}
        <Reviews courseId={course.id} />
      </div>
    </div>
  );
}

function LessonRow({ lesson, index, isEnrolled, hasSubscription }) {
  const navigate = useNavigate();

  const canAccess = lesson.is_free_preview || (isEnrolled && hasSubscription);

  const handleClick = () => {
    if (!localStorage.getItem('access_token')) navigate(`/login?next=/lessons/${lesson.id}`);
    else if (canAccess) navigate(`/lessons/${lesson.id}`);
    else navigate('/tariffs');
  };

  return (
    <button type="button"
      className={`lesson-row ${canAccess ? 'clickable' : 'locked'}`}
      onClick={handleClick}
    >
      <div className="lesson-number">{lesson.is_completed ? '✔' : index}</div>
      <div className="lesson-info">
        <span className="lesson-title">{lesson.title}</span>
        {lesson.is_free_preview && <span className="free-badge">Bepul</span>}
        {!canAccess && <span className="lock-icon">🔒</span>}
      </div>
      <div className="lesson-duration">
        {formatDuration(lesson.duration_seconds)}
      </div>
    </button>
  );
}
