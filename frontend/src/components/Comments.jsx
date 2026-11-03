import { mediaUrl } from '../api/axios';
import { useState, useEffect, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import api from '../api/axios';
import useAuthStore from '../store/authStore';

export default function Comments({ lessonId }) {
  const { t } = useTranslation();
  const { isAuthenticated } = useAuthStore();
  const [comments, setComments] = useState([]);
  const [content, setContent] = useState('');
  const [replyTo, setReplyTo] = useState(null);

  const load = useCallback(() => {
    api.get(`/interactions/lessons/${lessonId}/comments/`)
      .then(res => setComments(res.data.results || res.data))
      .catch(() => {});
  }, [lessonId]);

  useEffect(() => { load(); }, [load]);

  const submit = async (e) => {
    e.preventDefault();
    if (!content.trim() || !isAuthenticated) return;
    await api.post(`/interactions/lessons/${lessonId}/comments/`, {
      content,
      parent: replyTo,
    });
    setContent('');
    setReplyTo(null);
    load();
  };

  return (
    <div className="comments-section">
      <h2>💬 {t('lesson.comments')} ({comments.length})</h2>

      {isAuthenticated && (
        <form className="comment-form" onSubmit={submit}>
          {replyTo && (
            <div className="reply-info">
              ↪ Javob yozish
              <button type="button" onClick={() => setReplyTo(null)}>✕</button>
            </div>
          )}
          <textarea
            placeholder={t('lesson.write_comment')}
            value={content}
            onChange={(e) => setContent(e.target.value)}
            rows={3}
          />
          <button type="submit" className="btn-primary-sm" disabled={!content.trim()}>
            {t('lesson.send')}
          </button>
        </form>
      )}

      {comments.length === 0 ? (
        <p className="empty">{t('lesson.no_comments')}</p>
      ) : (
        <div className="comments-list">
          {comments.map(c => (
            <CommentItem key={c.id} comment={c} onReply={() => setReplyTo(c.id)} />
          ))}
        </div>
      )}
    </div>
  );
}

function CommentItem({ comment, onReply }) {
  const { t } = useTranslation();
  const [showReplies, setShowReplies] = useState(false);
  const [replies, setReplies] = useState([]);

  const loadReplies = async () => {
    if (!showReplies) {
      const res = await api.get(`/interactions/comments/${comment.id}/replies/`);
      setReplies(res.data.results || res.data);
    }
    setShowReplies(!showReplies);
  };

  return (
    <div className="comment-item">
      <div className="comment-avatar">
        {comment.user_avatar
          ? <img src={mediaUrl(comment.user_avatar)} alt="" />
          : <span>{comment.user_name?.charAt(0).toUpperCase()}</span>
        }
      </div>
      <div className="comment-body">
        <div className="comment-meta">
          <b>{comment.user_name}</b>
          {comment.is_admin && <span className="admin-tag">👑 Admin</span>}
          <span className="comment-date">{new Date(comment.created_at).toLocaleString('uz-UZ')}</span>
        </div>
        <p>{comment.content}</p>
        <div className="comment-actions">
          <button className="link-btn" onClick={onReply}>↪ {t('lesson.reply')}</button>
          {comment.replies_count > 0 && (
            <button className="link-btn" onClick={loadReplies}>
              {showReplies ? '▴' : '▾'} {comment.replies_count} {t('lesson.answers')}
            </button>
          )}
        </div>
        {showReplies && (
          <div className="replies-list">
            {replies.map(r => (
              <CommentItem key={r.id} comment={r} onReply={onReply} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
