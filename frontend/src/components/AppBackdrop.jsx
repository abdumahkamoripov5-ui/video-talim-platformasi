// Decorative, non-interactive education/video backdrop shown behind every page.
export default function AppBackdrop() {
  return (
    <div className="app-backdrop" aria-hidden="true">
      <span className="backdrop-blob backdrop-blob--a" />
      <span className="backdrop-blob backdrop-blob--b" />
      <span className="backdrop-blob backdrop-blob--c" />
      <svg className="backdrop-icon bi-play" viewBox="0 0 24 24"><path d="M8 5v14l11-7z" /></svg>
      <svg className="backdrop-icon bi-book" viewBox="0 0 24 24"><path d="M4 5.5A2.5 2.5 0 0 1 6.5 3H20v15H6.5A2.5 2.5 0 0 0 4 20.5zM6.5 18H18v2H6.5a.5.5 0 0 1 0-1z" /></svg>
      <svg className="backdrop-icon bi-cap" viewBox="0 0 24 24"><path d="M12 3 1 9l11 6 9-4.9V17h2V9zM5 12.2V16c0 1.7 3.1 3 7 3s7-1.3 7-3v-3.8l-7 3.8z" /></svg>
      <svg className="backdrop-icon bi-chart" viewBox="0 0 24 24"><path d="M3 20h18v2H3zM5 16l4-5 3 3 6-7 1.5 1.3L12 15l-3-3-3.2 4z" /></svg>
    </div>
  );
}
