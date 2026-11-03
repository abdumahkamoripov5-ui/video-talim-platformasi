import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import api from '../api/axios';

export default function Quiz({ lessonId }) {
  const { t } = useTranslation();
  const [quiz, setQuiz] = useState(null);
  const [answers, setAnswers] = useState({});
  const [currentIdx, setCurrentIdx] = useState(0);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(true);
  const [hasQuiz, setHasQuiz] = useState(false);

  useEffect(() => {
    api.get(`/quizzes/lessons/${lessonId}/`)
      .then(res => { setQuiz(res.data); setHasQuiz(true); setLoading(false); })
      .catch(() => { setHasQuiz(false); setLoading(false); });
  }, [lessonId]);

  if (loading) return null;
  if (!hasQuiz) return null;

  const submit = async () => {
    const res = await api.post(`/quizzes/lessons/${lessonId}/submit/`, { answers });
    setResult(res.data);
  };

  const reset = () => {
    setAnswers({});
    setCurrentIdx(0);
    setResult(null);
  };

  if (result) {
    return (
      <div className="quiz-result">
        <div className={`result-card ${result.is_passed ? 'passed' : 'failed'}`}>
          <div className="result-icon">{result.is_passed ? '🎉' : '😔'}</div>
          <h2>{result.is_passed ? t('lesson.quiz_passed') : t('lesson.quiz_failed')}</h2>
          <div className="result-score">
            <span className="score-num">{result.score}</span>
            <span className="score-of">/ {result.total}</span>
          </div>
          <div className="result-percent">{result.percentage}%</div>
          <p>O'tish balli: {result.pass_percentage}%</p>
          <button className="btn-primary" onClick={reset}>{t('quiz.try_again')}</button>
        </div>
      </div>
    );
  }

  const question = quiz.questions[currentIdx];
  if (!question) return null;
  const isLast = currentIdx === quiz.questions.length - 1;
  const allAnswered = quiz.questions.every(q => answers[q.id]);

  return (
    <div className="quiz-section">
      <div className="quiz-header">
        <div>
          <h2>📝 {quiz.title}</h2>
          <p>{quiz.questions.length} {t('quiz.questions_count')} • {quiz.pass_percentage}{t('quiz.pass_required')}</p>
        </div>
        <div className="quiz-progress">
          {currentIdx + 1} / {quiz.questions.length}
        </div>
      </div>

      <div className="quiz-bar">
        <div className="quiz-bar-fill" style={{ width: `${((currentIdx + 1) / quiz.questions.length) * 100}%` }} />
      </div>

      <div className="quiz-question">
        <h3>{question.text}</h3>
        <div className="quiz-choices">
          {question.choices.map(choice => (
            <label
              key={choice.id}
              className={`quiz-choice ${answers[question.id] === choice.id ? 'selected' : ''}`}
            >
              <input
                type="radio"
                name={`q-${question.id}`}
                checked={answers[question.id] === choice.id}
                onChange={() => setAnswers({ ...answers, [question.id]: choice.id })}
              />
              <span>{choice.text}</span>
            </label>
          ))}
        </div>
      </div>

      <div className="quiz-actions">
        {currentIdx > 0 && (
          <button className="btn-outline" onClick={() => setCurrentIdx(currentIdx - 1)}>
            ← {t('common.back')}
          </button>
        )}
        {!isLast ? (
          <button
            className="btn-primary"
            onClick={() => setCurrentIdx(currentIdx + 1)}
            disabled={!answers[question.id]}
          >
            {t('quiz.next')} →
          </button>
        ) : (
          <button className="btn-primary" onClick={submit} disabled={!allAnswered}>
            ✓ {t('quiz.submit')}
          </button>
        )}
      </div>
    </div>
  );
}
