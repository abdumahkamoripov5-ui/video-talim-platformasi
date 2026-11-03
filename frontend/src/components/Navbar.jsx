import { useState, useEffect } from 'react';
import { Link, NavLink, useNavigate, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import useAuthStore from '../store/authStore';
import useThemeStore from '../store/themeStore';
import api from '../api/axios';
import Icon from './Icon';
export default function Navbar() {
  const { t, i18n } = useTranslation();
  const { user, isAuthenticated, logout } = useAuthStore();
  const { theme, toggleTheme } = useThemeStore();
  const navigate = useNavigate();
  const location = useLocation();
  const [search, setSearch] = useState('');
  const [menu, setMenu] = useState(false);
  const [notifications, setNotifications] = useState([]);
  const [showNotifications, setShowNotifications] = useState(false);
  const [unread, setUnread] = useState(0);
  useEffect(() => {
    if (!isAuthenticated) return;
    api.get('/notifications/unread-count/').then(r => setUnread(r.data.count)).catch(() => {});
  }, [isAuthenticated, location.pathname]);
  const openNotifications = async () => {
    setShowNotifications(v => !v);
    try { const { data } = await api.get('/notifications/'); setNotifications(data.results || data); } catch { setNotifications([]); }
  };
  return <header className="site-header"><div className="container header-inner">
    <Link to="/" className="brand" aria-label="EduPlatform bosh sahifa"><span className="brand-symbol"><Icon name="book" size={23} /></span>edu<span>platform</span><i /></Link>
    <nav aria-label="Asosiy navigatsiya" className="desktop-nav"><NavLink to="/courses">{t('nav.courses')}</NavLink><Link to="/#tariffs">{t('nav.tariffs')}</Link><Link to="/#about">Biz haqimizda</Link></nav>
    <form className="header-search" role="search" onSubmit={e => { e.preventDefault(); navigate(`/courses?search=${encodeURIComponent(search.trim())}`); }}><Icon name="search" size={17} /><input aria-label="Kurs qidirish" placeholder="Nimani o‘rganmoqchisiz?" value={search} onChange={e => setSearch(e.target.value)} /></form>
    <div className="header-actions"><button className="icon-btn theme-switch" aria-label="Mavzuni almashtirish" onClick={toggleTheme}><Icon name={theme === 'light' ? 'moon' : 'sun'} size={19} /></button><select className="language-select" aria-label="Tilni tanlang" value={i18n.language?.split('-')[0] || 'uz'} onChange={e => i18n.changeLanguage(e.target.value)}><option value="uz">UZ</option><option value="ru">RU</option><option value="en">EN</option></select>
    {isAuthenticated ? <><div className="notification-anchor"><button className="icon-btn" aria-label="Bildirishnomalar" aria-expanded={showNotifications} onClick={openNotifications}><Icon name="bell" />{unread > 0 && <span className="notification-dot" />}</button>{showNotifications && <div className="notification-panel"><div><b>Bildirishnomalar</b><button className="link-btn" onClick={async () => { await api.post('/notifications/mark-all-read/'); setUnread(0); setNotifications(n => n.map(x => ({...x, is_read:true}))); }}>O‘qilgan deb belgilash</button></div>{notifications.length ? notifications.slice(0,8).map(n => <p key={n.id} className={n.is_read ? '' : 'unread'}><b>{n.title}</b><small>{n.message}</small></p>) : <p>Yangi bildirishnomalar yo‘q</p>}</div>}</div><Link to="/profile" className="user-chip" aria-label="Shaxsiy kabinet">{user?.full_name?.charAt(0) || 'U'}</Link></> : <><Link to="/login" className="header-login">Kirish</Link><Link to="/register" className="btn-primary header-register">Boshlash <Icon name="arrow" size={16} /></Link></>}
    <button className="icon-btn mobile-menu-toggle" aria-label="Menyuni ochish" aria-expanded={menu} onClick={() => setMenu(!menu)}><Icon name={menu ? 'close' : 'menu'} /></button></div>
  </div>{menu && <nav className="mobile-nav" aria-label="Mobil navigatsiya" onClick={() => setMenu(false)}><Link to="/courses">Kurslar</Link><Link to="/#tariffs">Tariflar</Link><Link to="/#about">Biz haqimizda</Link>{isAuthenticated ? <><Link to="/profile">Shaxsiy kabinet</Link><Link to="/wishlist">Sevimlilar</Link><button onClick={async () => { await logout(); navigate('/'); }}>Chiqish</button></> : <><Link to="/login">Kirish</Link><Link to="/register">Ro‘yxatdan o‘tish</Link></>}</nav>}</header>;
}
