import { useEffect, useRef, useState } from 'react';
import Hls from 'hls.js';
import api, { mediaUrl } from '../api/axios';

export default function VideoPlayer({ lessonId, watermarkId, resumeAt = 0, initialData, poster }) {
  const videoRef = useRef(null);
  const shellRef = useRef(null);
  const hlsRef = useRef(null);
  const positionRef = useRef(resumeAt);
  const [data, setData] = useState(initialData || null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);
  const [qualities, setQualities] = useState([]);
  const [quality, setQuality] = useState('-1');
  const [saveError, setSaveError] = useState(false);
  const [pos, setPos] = useState({ x: 6, y: 8 });
  const [retry, setRetry] = useState(0);
  useEffect(() => {
    let alive = true;
    const renew = async () => {
      try {
        if (videoRef.current?.currentTime) positionRef.current = videoRef.current.currentTime;
        const response = await api.get(`/courses/lessons/${lessonId}/video-url/`);
        if (alive) { setData(response.data); setError(''); }
      } catch { if (alive) setError('Video yuklanmadi. Obunangiz va internet aloqasini tekshiring.'); }
    };
    if (!initialData || retry) renew();
    const interval = setInterval(renew, Math.max(60, (initialData?.expires_in || 1800) - 90) * 1000);
    return () => { alive = false; clearInterval(interval); };
  }, [lessonId, initialData, retry]);
  useEffect(() => {
    const video = videoRef.current;
    if (!data?.url || !video) return;
    setLoading(true);
    const resume = () => { video.currentTime = Math.min(positionRef.current || data.resume_at || 0, Number.isFinite(video.duration) ? video.duration : Infinity); setLoading(false); };
    video.addEventListener('loadedmetadata', resume, { once: true });
    if (Hls.isSupported()) {
      const hls = new Hls({ xhrSetup: xhr => { xhr.withCredentials = true; } });
      hlsRef.current = hls;
      hls.loadSource(mediaUrl(data.url)); hls.attachMedia(video);
      hls.on(Hls.Events.MANIFEST_PARSED, () => setQualities(hls.levels.map((l,i) => ({ id: i, label: `${l.height}p` }))));
      hls.on(Hls.Events.ERROR, (_, event) => {
        if (event.fatal) { setLoading(false); setError('Videoni ijro etib bo‘lmadi. Qayta urinib ko‘ring.'); }
      });
    } else if (video.canPlayType('application/vnd.apple.mpegurl')) {
      video.src = mediaUrl(data.url);
    } else { setLoading(false); setError('Brauzer HLS videoni qo‘llab-quvvatlamaydi.'); }
    return () => { video.removeEventListener('loadedmetadata', resume); hlsRef.current?.destroy(); hlsRef.current = null; };
  }, [data]);
  useEffect(() => {
    const video = videoRef.current;
    const save = async () => {
      if (!video || !Number.isFinite(video.duration) || video.currentTime <= 0) return;
      positionRef.current = video.currentTime;
      try { await api.post('/users/progress/', { lesson: lessonId, watched_seconds: Math.floor(video.currentTime) }); setSaveError(false); }
      catch { setSaveError(true); }
    };
    const visibility = () => { if (document.hidden) save(); };
    const timer = setInterval(save, 10000);
    video?.addEventListener('pause', save); video?.addEventListener('ended', save);
    document.addEventListener('visibilitychange', visibility);
    return () => { save(); clearInterval(timer); video?.removeEventListener('pause', save); video?.removeEventListener('ended', save); document.removeEventListener('visibilitychange', visibility); };
  }, [lessonId]);
  useEffect(() => { const timer = setInterval(() => setPos({ x: 5 + Math.random()*60, y: 5 + Math.random()*65 }), 7000); return () => clearInterval(timer); }, []);
  return <div><div className="player-shell" ref={shellRef} onContextMenu={e => e.preventDefault()}>
    <video ref={videoRef} controls controlsList="nodownload noremoteplayback nofullscreen" disablePictureInPicture disableRemotePlayback playsInline crossOrigin="use-credentials" poster={mediaUrl(poster)} onWaiting={() => setLoading(true)} onPlaying={() => setLoading(false)} onCanPlay={() => setLoading(false)} onError={() => { setLoading(false); setError('Video ochilmadi. Qayta urinib ko‘ring.'); }} />
    {loading && !error && <div className="player-loading">Video tayyorlanmoqda…</div>}
    {error && <div className="player-error" role="alert"><span>{error}</span><button className="btn-outline" onClick={() => { setError(''); setRetry(r => r+1); }}>Qayta urinish</button></div>}
    {(data?.watermark_id || watermarkId) && <span className="player-watermark" style={{ left: `${pos.x}%`, top: `${pos.y}%` }}>ID: {data?.watermark_id || watermarkId}</span>}
  </div><div className="player-tools"><span role="status">{saveError ? 'Progress saqlanmadi. Ulanish tiklangach qayta uriniladi.' : 'Progress avtomatik saqlanadi'}</span><div>{qualities.length > 0 && <select aria-label="Video sifati" value={quality} onChange={e => { setQuality(e.target.value); if (hlsRef.current) hlsRef.current.currentLevel = Number(e.target.value); }}><option value="-1">Avtomatik sifat</option>{qualities.map(q => <option key={q.id} value={q.id}>{q.label}</option>)}</select>}<button onClick={() => { if (document.fullscreenElement) document.exitFullscreen(); else shellRef.current?.requestFullscreen?.().catch(() => {}); }}>To‘liq ekran</button></div></div></div>;
}
