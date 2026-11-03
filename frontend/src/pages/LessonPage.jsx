import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import api, { downloadFile } from '../api/axios';
import useAuthStore from '../store/authStore';
import VideoPlayer from '../components/VideoPlayer';
import Comments from '../components/Comments';
import Questions from '../components/Questions';
import Quiz from '../components/Quiz';
import Icon from '../components/Icon';
export default function LessonPage() {
  const { id } = useParams();
  return <LessonContent key={id} id={id} />;
}
function LessonContent({ id }) {
  const { user } = useAuthStore();
  const [lesson, setLesson] = useState(null);
  const [course, setCourse] = useState(null);
  const [videoData, setVideoData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [fileError, setFileError] = useState('');
  useEffect(() => {
    let active = true;
    api.get(`/courses/lessons/${id}/`).then(async ({ data }) => {
      if (!active) return;
      setLesson(data);
      const [video, details] = await Promise.allSettled([api.get(`/courses/lessons/${id}/video-url/`), api.get(`/courses/${data.course_slug}/`)]);
      if (!active) return;
      if (video.status === 'fulfilled') setVideoData(video.value.data);
      if (details.status === 'fulfilled') setCourse(details.value.data);
    }).catch(err => { if (active) setError(err.response?.status === 403 ? 'Bu darsni ko‘rish uchun faol obuna kerak.' : 'Darsni yuklab bo‘lmadi. Qayta urinib ko‘ring.'); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [id]);
  if (loading) return <div className="loading" role="status">Dars yuklanmoqda…</div>;
  if (error) return <div className="error-page"><h2>{error}</h2><Link to="/tariffs" className="btn-primary">Tariflarni ko‘rish</Link><Link to="/courses">Kurslarga qaytish</Link></div>;
  if (!lesson) return null;
  return <div className="lesson-page"><div className="container"><div className="lesson-breadcrumb"><Link to="/courses">Kurslar</Link> / <Link to={`/courses/${lesson.course_slug}`}>{lesson.course_title}</Link> / Dars</div><div className="lesson-layout"><div><h1>{lesson.title}</h1>{videoData ? <VideoPlayer key={id} lessonId={Number(id)} watermarkId={user?.display_id} resumeAt={videoData.resume_at} initialData={videoData} poster={lesson.thumbnail} /> : <div className="empty-state"><Icon name="play" size={32} /><h3>Video hozircha tayyor emas</h3><p>Materiallar bilan tanishishingiz yoki boshqa darsni tanlashingiz mumkin.</p></div>}
    {lesson.description && <section className="lesson-description"><h3>Dars haqida</h3><p>{lesson.description}</p></section>}
    {lesson.attachments?.length > 0 && <section className="attachments"><h3>O‘quv materiallari</h3>{fileError && <p role="alert" className="error-banner">{fileError}</p>}<div className="attachments-list">{lesson.attachments.map(a => <button key={a.id} className="attachment-item" onClick={() => { setFileError(''); downloadFile(a.file, `${a.title}${a.file_type === 'pdf' ? '.pdf' : a.file_type === 'word' ? '.docx' : ''}`).catch(() => setFileError('Faylni yuklab bo‘lmadi. Qayta urinib ko‘ring.')); }}><Icon name="book" />{a.title} <small>{a.file_type.toUpperCase()} ↓</small></button>)}</div></section>}
    <Quiz key={`quiz-${id}`} lessonId={Number(id)} /><LessonTabs key={`tabs-${id}`} lessonId={Number(id)} /></div><aside className="lesson-sidebar"><h3>{course?.title || 'Kurs darslari'}</h3>{course && <><p className="notice">{course.lessons.filter(l => l.is_completed).length}/{course.lessons.length} dars — {course.progress}%</p><progress max="100" value={course.progress} />{course.lessons.map((l,i) => <Link key={l.id} to={`/lessons/${l.id}`} className={String(l.id) === id ? 'active' : ''}><span>{l.is_completed ? '✓' : String(i+1).padStart(2,'0')}</span><span>{l.title}</span></Link>)}</>}</aside></div></div></div>;
}
function LessonTabs({ lessonId }) {
  const [tab, setTab] = useState('comments');
  return <div className="lesson-tabs"><div className="tabs-nav" role="tablist" aria-label="Dars muhokamasi"><button role="tab" aria-selected={tab === 'comments'} className={`tab-btn ${tab === 'comments' ? 'active' : ''}`} onClick={() => setTab('comments')}>Izohlar</button><button role="tab" aria-selected={tab === 'questions'} className={`tab-btn ${tab === 'questions' ? 'active' : ''}`} onClick={() => setTab('questions')}>Savollar</button></div><div className="tab-content" role="tabpanel">{tab === 'comments' ? <Comments lessonId={lessonId} /> : <Questions lessonId={lessonId} />}</div></div>;
}
