import { readFileSync, writeFileSync } from 'node:fs';
const raw = process.argv[2];
if (!raw) throw new Error('Backend manzilini kiriting: npm run configure:vercel -- https://api.example.uz');
const origin = new URL(raw);
if (origin.protocol !== 'https:' || origin.pathname !== '/' || origin.search || origin.username || origin.password) throw new Error('Faqat HTTPS origin kiriting, /api qo‘shmang.');
const file = new URL('../vercel.json', import.meta.url);
const config = JSON.parse(readFileSync(file));
config.rewrites = [
  { source: '/api/:path*', destination: `${origin.origin}/api/:path*` },
  { source: '/media/:path*', destination: `${origin.origin}/media/:path*` },
  { source: '/((?!api/|media/).*)', destination: '/index.html' },
];
writeFileSync(file, JSON.stringify(config, null, 2) + '\n');
console.log(`Vercel /api va /media so‘rovlarini ${origin.origin} serveriga yuboradi.`);
