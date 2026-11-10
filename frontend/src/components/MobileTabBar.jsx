import { NavLink } from 'react-router-dom';

const tabs = [
  { to: '/', label: 'Bosh sahifa', end: true, icon: <path d="M4 11.2 12 4l8 7.2V20a1 1 0 0 1-1 1h-4.5v-5.5h-5V21H5a1 1 0 0 1-1-1z" /> },
  { to: '/courses', label: 'Kurslar', icon: <path d="M4 5.5A2.5 2.5 0 0 1 6.5 3H20v15H6.5A2.5 2.5 0 0 0 4 20.5zM6.5 18H18v2H6.5a.5.5 0 0 1 0-1z" /> },
  { to: '/wishlist', label: 'Sevimli', icon: <path d="M12 21s-7.5-4.6-9.5-9.2C1.1 8.7 3 5 6.6 5c2 0 3.6 1.1 4.4 2.6C11.8 6.1 13.4 5 15.4 5 19 5 20.9 8.7 21.5 11.8 19.5 16.4 12 21 12 21z" /> },
  { to: '/profile', label: 'Profil', icon: <path d="M12 12a4.5 4.5 0 1 0 0-9 4.5 4.5 0 0 0 0 9zm0 2c-4.4 0-8 2.2-8 5v1h16v-1c0-2.8-3.6-5-8-5z" /> },
];

export default function MobileTabBar() {
  return (
    <nav className="mobile-tabbar" aria-label="Asosiy navigatsiya">
      {tabs.map(tab => (
        <NavLink key={tab.to} to={tab.to} end={tab.end} className={({ isActive }) => `tab-item${isActive ? ' active' : ''}`}>
          <svg viewBox="0 0 24 24" aria-hidden="true">{tab.icon}</svg>
          <span>{tab.label}</span>
        </NavLink>
      ))}
    </nav>
  );
}
