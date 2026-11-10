import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import api from '../api/axios';

const DISMISSED_KEY = 'dismissed_announcement';

function readDismissed() {
  try { return localStorage.getItem(DISMISSED_KEY); } catch { return null; }
}

export default function AnnouncementBanner() {
  const [item, setItem] = useState(null);

  useEffect(() => {
    let alive = true;
    api.get('/notifications/announcements/')
      .then(({ data }) => {
        const list = Array.isArray(data) ? data : data.results || [];
        if (alive && list.length && String(list[0].id) !== readDismissed()) setItem(list[0]);
      })
      .catch(() => {});
    return () => { alive = false; };
  }, []);

  if (!item) return null;

  const dismiss = () => {
    try { localStorage.setItem(DISMISSED_KEY, String(item.id)); } catch { /* storage unavailable */ }
    setItem(null);
  };

  return (
    <aside className="announcement-banner" role="status" aria-label="E'lon">
      <div className="announcement-text">
        <strong>{item.title}</strong>
        {item.body && <span>{item.body}</span>}
        <div className="announcement-actions">
          {item.link && <Link to={item.link} onClick={dismiss}>Batafsil</Link>}
          <button type="button" className="announcement-close" onClick={dismiss}>Yopish</button>
        </div>
      </div>
    </aside>
  );
}
