import { mediaUrl } from '../api/axios';
import { useState, useEffect, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import api from '../api/axios';
import useAuthStore from '../store/authStore';

export default function Questions({ lessonId }) {
  const { t } = useTranslation();
  const { isAuthenticated } = useAuthStore();
  const [questions, setQuestions] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');

  const load = useCallback(() => {
    api.get(`/interactions/questions/?lesson=${lessonId}`)
      .then(res => setQuestions(res.data.results || res.data))
      .catch(() => {});
  }, [lessonId]);

  useEffect(() => { load(); }, [load]);

  const submit = async (e) => {
    e.preventDefault();
    if (!isAuthenticated || !title || !content) return;
    await api.post('/interactions/questions/', {
      lesson: lessonId, title, content,
    });
    setTitle(''); setContent(''); setShowForm(false);
    load();
  };

  return (
    <div className="questions-section">
      <div className="reviews-header">
        <h2>❓ {t('lesson.questions')} ({questions.length})</h2>
        {isAuthenticated && !showForm && (
          <button className="btn-primary-sm" onClick={() => setShowForm(true)}>
            {t('lesson.ask_question')}
          </button>
        )}
      </div>

      {showForm && (
        <form className="review-form" onSubmit={submit}>
          <label>{t('lesson.question_title')}</label>
          <input value={title} onChange={(e) => setTitle(e.target.value)} required />
          <label>{t('lesson.question_content')}</label>
          <textarea
            rows={4}
            value={content}
            onChange={(e) => setContent(e.target.value)}
            required
          />
          <div className="form-actions">
            <button type="submit" className="btn-primary">{t('lesson.send')}</button>
            <button type="button" className="btn-outline-sm" onClick={() => setShowForm(false)}>
              {t('common.cancel')}
            </button>
          </div>
        </form>
      )}

      {questions.length === 0 ? (
        <p className="empty">{t('lesson.no_questions')}</p>
      ) : (
        <div className="questions-list">
          {questions.map(q => <QuestionItem key={q.id} question={q} onAnswer={load} />)}
        </div>
      )}
    </div>
  );
}

function QuestionItem({ question, onAnswer }) {
  const { t } = useTranslation();
  const { isAuthenticated } = useAuthStore();
  const [showAnswer, setShowAnswer] = useState(false);
  const [answerContent, setAnswerContent] = useState('');

  const submitAnswer = async (e) => {
    e.preventDefault();
    if (!answerContent.trim()) return;
    await api.post('/interactions/answers/', {
      question: question.id, content: answerContent,
    });
    setAnswerContent('');
    setShowAnswer(false);
    onAnswer?.();
  };

  return (
    <div className="question-item">
      <div className="question-header">
        <div className="comment-avatar">
          {question.user_avatar
            ? <img src={mediaUrl(question.user_avatar)} alt="" />
            : <span>{question.user_name?.charAt(0).toUpperCase()}</span>
          }
        </div>
        <div style={{flex: 1}}>
          <div className="comment-meta">
            <b>{question.user_name}</b>
            <span className={`q-status ${question.status}`}>
              {question.status === 'answered' ? '✓ Javob berilgan' : '⏳ Kutilmoqda'}
            </span>
          </div>
          <h4 className="question-title">{question.title}</h4>
          <p>{question.content}</p>
        </div>
      </div>

      {question.answers?.length > 0 && (
        <div className="answers-list">
          {question.answers.map(a => (
            <div key={a.id} className={`answer-item ${a.is_admin_answer ? 'admin' : ''}`}>
              <div className="comment-avatar">
                {a.author_avatar
                  ? <img src={mediaUrl(a.author_avatar)} alt="" />
                  : <span>{a.author_name?.charAt(0).toUpperCase()}</span>
                }
              </div>
              <div>
                <div className="comment-meta">
                  <b>{a.author_name}</b>
                  {a.is_admin_answer && <span className="admin-tag">👑 {t('lesson.admin_answer')}</span>}
                  <span className="comment-date">{new Date(a.created_at).toLocaleString('uz-UZ')}</span>
                </div>
                <p>{a.content}</p>
              </div>
            </div>
          ))}
        </div>
      )}

      {isAuthenticated && (
        <div className="answer-form-wrapper">
          {!showAnswer ? (
            <button className="link-btn" onClick={() => setShowAnswer(true)}>↪ {t('lesson.reply')}</button>
          ) : (
            <form onSubmit={submitAnswer}>
              <textarea
                rows={3}
                value={answerContent}
                onChange={(e) => setAnswerContent(e.target.value)}
                placeholder={t('lesson.write_comment')}
              />
              <div className="form-actions">
                <button type="submit" className="btn-primary-sm">{t('lesson.send')}</button>
                <button type="button" className="btn-outline-sm" onClick={() => setShowAnswer(false)}>
                  {t('common.cancel')}
                </button>
              </div>
            </form>
          )}
        </div>
      )}
    </div>
  );
}
