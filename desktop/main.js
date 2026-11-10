const { app, BrowserWindow, shell, Menu } = require('electron');

const SITE_URL = process.env.SITE_URL || 'https://video-talim-platformasi.vercel.app';

const SPLASH_HTML = `
<!doctype html>
<html><head><meta charset="utf-8"><style>
  html,body{margin:0;height:100%;overflow:hidden;font-family:Segoe UI,Arial,sans-serif;color:#fff;
    background:radial-gradient(circle at 20% 20%,#6a5cff 0%,transparent 45%),
               radial-gradient(circle at 80% 80%,#00c6ff 0%,transparent 45%),
               linear-gradient(135deg,#1e1b4b 0%,#312e81 50%,#0f172a 100%);}
  .wrap{height:100%;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:18px}
  .logo{width:84px;height:84px;border-radius:24px;background:rgba(255,255,255,.14);
    display:flex;align-items:center;justify-content:center;font-size:40px;
    box-shadow:0 10px 40px rgba(0,0,0,.35);backdrop-filter:blur(6px)}
  h1{font-size:26px;margin:0;font-weight:700;letter-spacing:.5px}
  p{margin:0;opacity:.75;font-size:14px}
  .bar{width:180px;height:4px;border-radius:4px;background:rgba(255,255,255,.2);overflow:hidden}
  .bar::after{content:"";display:block;height:100%;width:40%;background:#fff;border-radius:4px;
    animation:s 1.2s ease-in-out infinite}
  @keyframes s{0%{transform:translateX(-100%)}100%{transform:translateX(260%)}}
</style></head>
<body><div class="wrap">
  <div class="logo">&#127902;</div>
  <h1>Video Ta'lim</h1>
  <p>Yuklanmoqda...</p>
  <div class="bar"></div>
</div></body></html>`;

let mainWin;
let splash;

function createSplash() {
  splash = new BrowserWindow({
    width: 420,
    height: 320,
    frame: false,
    transparent: false,
    resizable: false,
    center: true,
    backgroundColor: '#1e1b4b',
    show: true,
  });
  splash.loadURL('data:text/html;charset=utf-8,' + encodeURIComponent(SPLASH_HTML));
}

function createMainWindow() {
  mainWin = new BrowserWindow({
    width: 1280,
    height: 800,
    minWidth: 900,
    minHeight: 600,
    title: "Video Ta'lim",
    show: false,
    autoHideMenuBar: true,
    backgroundColor: '#0f172a',
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  Menu.setApplicationMenu(null);

  const showMain = () => {
    if (splash && !splash.isDestroyed()) splash.close();
    if (!mainWin.isDestroyed()) {
      mainWin.show();
      mainWin.focus();
    }
  };

  mainWin.webContents.once('did-finish-load', showMain);
  // Tarmoq xatosi bo'lsa ham splash yopilib, oyna ochilsin
  mainWin.webContents.once('did-fail-load', showMain);
  setTimeout(showMain, 15000);

  mainWin.loadURL(SITE_URL);

  // Sayt ichidagi tashqi havolalarni tizim brauzerida ochish
  mainWin.webContents.setWindowOpenHandler(({ url }) => {
    if (!url.startsWith(SITE_URL)) {
      shell.openExternal(url);
      return { action: 'deny' };
    }
    return { action: 'allow' };
  });
}

const gotLock = app.requestSingleInstanceLock();
if (!gotLock) {
  app.quit();
} else {
  app.on('second-instance', () => {
    if (mainWin && !mainWin.isDestroyed()) {
      if (mainWin.isMinimized()) mainWin.restore();
      mainWin.focus();
    }
  });
  app.whenReady().then(() => {
    createSplash();
    createMainWindow();
  });
  app.on('window-all-closed', () => app.quit());
}
