import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import api from '../api/axios';
import useAuthStore from '../store/authStore';
import CourseCard from '../components/CourseCard';
import Icon from '../components/Icon';

export default function HomePage() {
  const { user } = useAuthStore();
  const [courses, setCourses] = useState([]);
  const [tariffs, setTariffs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [category, setCategory] = useState('all');
  const [attempt, setAttempt] = useState(0);
  useEffect(() => {
    let active = true;
    Promise.all([api.get('/courses/'), api.get('/payments/tariffs/')])
      .then(([c, t]) => { if (active) { setCourses(c.data.results || c.data); setTariffs(t.data.results || t.data); } })
      .catch(() => { if (active) setError('Ma’lumotlarni yuklab bo‘lmadi. Internet aloqasi va serverni tekshiring.'); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [attempt]);
  const categories = [...new Map(courses.filter(c => c.category).map(c => [c.category.id, c.category])).values()];
  const filtered = courses.filter(c => category === 'all' || c.category?.id === category).slice(0, 6);
  return <div className="home-page">
    <section className="academy-hero container">
      <div className="hero-copy">
        <span className="eyebrow"><span className="status-dot" /> KATTA MAQSADLAR KICHIK QADAMDAN</span>
        <h1>Bugun o‘rganing.<br /><span>Ertaga yarating.</span></h1>
        <p>Yangi ko‘nikma, yangi imkoniyat. O‘zbek tilidagi video darslar bilan o‘zingizga qulay vaqtda, o‘z sur’atingizda rivojlaning.</p>
        <div className="hero-actions"><Link to="/courses" className="btn-primary">Kurslarni o‘rganish <Icon name="arrow" /></Link><a href="#how-it-works" className="hero-how"><span><Icon name="play" size={15} /></span> Qanday ishlaydi?</a></div>
        <div className="hero-assurances"><span><Icon name="check" size={16} /> Bepul tanishuv darslari</span><span><Icon name="check" size={16} /> Istalgan qurilmada</span></div>
      </div>
      <div className="learning-visual">
        <span className="visual-orbit orbit-one" /><span className="visual-orbit orbit-two" />
        <div className="learning-window">
          <div className="window-top"><div><i /><i /><i /></div><span>MENING O‘RGANISH YO‘LIM</span><Icon name="book" size={16} /></div>
          <div className="window-content"><div className="learning-label">KELAJAK SIZDAN BOSHLANADI</div><h2>Bir qadam oldinda<br />bo‘lishni tanlang.</h2><div className="visual-player"><div className="code-lines"><span /><span /><span /><span /><span /></div><Link to="/courses" className="big-play" aria-label="Video kurslarni ochish"><Icon name="play" size={28} /></Link><div className="visual-quality">HD <span>•</span> VIDEO DARSLAR</div></div>
          <div className="learning-steps"><span><b>01</b> Tomosha qiling</span><span><b>02</b> Mashq qiling</span><span><b>03</b> Natijaga erishing</span></div></div>
        </div>
        <div className="floating-note note-top"><span className="note-icon"><Icon name="chart" size={22} /></span><div><b>Har kuni bir qadam</b><small>O‘sish — doimiy harakat</small></div></div>
        <div className="floating-note note-bottom"><span className="note-icon"><Icon name="check" size={22} /></span><div><b>Bilim siz bilan qoladi</b><small>Ko‘ring. Qo‘llang. Rivojlaning.</small></div></div>
        <span className="visual-spark">✳</span>
      </div>
    </section>
    <div className="benefit-strip"><div className="container"><span><Icon name="play" /> Sifatli video darslar</span><span><Icon name="clock" /> O‘zingizga qulay vaqtda</span><span><Icon name="chart" /> Natijangizni kuzating</span><span><Icon name="globe" /> O‘zbek tilida o‘rganing</span></div></div>
    {user && <section className="container continue-banner"><div><span className="eyebrow">XUSH KELIBSIZ, {user.full_name}</span><h2>O‘rganishni davom ettiramizmi?</h2></div><Link to="/profile" className="btn-outline">Mening kurslarim <Icon name="arrow" /></Link></section>}
    <section className="section container" id="courses"><div className="section-heading"><div><span className="eyebrow">BILIMGA SARMOYA — KELAJAKKA SARMOYA</span><h2>Keyingi qadamingizni tanlang</h2><p>Maqsadingizga mos kursni toping va bugunoq boshlang.</p></div><Link to="/courses" className="text-link">Barcha kurslar <Icon name="arrow" /></Link></div>
      <div className="category-tabs"><button className={category === 'all' ? 'active' : ''} onClick={() => setCategory('all')}>Barchasi</button>{categories.map(c => <button key={c.id} className={category === c.id ? 'active' : ''} onClick={() => setCategory(c.id)}>{c.name}</button>)}</div>
      {error ? <div role="alert" className="empty-state"><h3>Hozircha bog‘lana olmadik</h3><p>{error}</p><button className="btn-outline" onClick={() => { setLoading(true); setError(''); setAttempt(a => a+1); }}>Qayta urinish</button></div> : loading ? <div className="loading-grid" aria-label="Kurslar yuklanmoqda">{[1,2,3].map(n => <div className="skeleton-card" key={n} />)}</div> : filtered.length ? <div className="courses-grid">{filtered.map((c,i) => <CourseCard course={c} index={i} key={c.id} />)}</div> : <div className="empty-state"><Icon name="book" size={36} /><h3>Yangi kurslar tez orada</h3><p>Kurslar e’lon qilingach shu yerda ko‘rinadi.</p></div>}
    </section>
    <section className="how-section" id="how-it-works"><div className="container"><div className="section-heading"><div><span className="eyebrow">HAMMASI ODDIY</span><h2>Maqsaddan natijagacha</h2></div><p>Murakkab sozlamalarsiz.<br />Bor e’tiboringiz o‘rganishda bo‘lsin.</p></div><div className="how-grid">{[['01', 'Yo‘nalishni tanlang', 'Qiziqishingiz va maqsadingizga mos kurs bilan tanishing.', 'book'], ['02', 'O‘rganishni boshlang', 'Bepul darsni ko‘ring. Davom etish uchun qulay obunani tanlang.', 'play'], ['03', 'Natijangizni kuzating', 'To‘xtagan joydan davom eting va kursdagi progressingizni kuzating.', 'chart']].map(([n,title,text,icon]) => <article key={n}><div className="how-top"><Icon name={icon} size={26} /><span>{n}</span></div><h3>{title}</h3><p>{text}</p></article>)}</div></div></section>
    <section className="section container" id="tariffs"><div className="section-heading centered"><span className="eyebrow">BITTA OBUNA. KO‘PROQ IMKONIYAT.</span><h2>O‘zingizga sarmoya kiriting</h2><p>Barcha kurslar, video darslar va o‘quv materiallari — bir joyda.</p></div><div className="tariffs-grid">{tariffs.map((t,i) => <article key={t.id} className={`tariff-card ${i === 0 ? 'featured-tariff' : ''}`}><span className="plan-label">{i === 0 ? 'O‘RGANISHNI BOSHLANG' : 'SIZ UCHUN'}</span><h3>{t.name}</h3><div className="plan-price">{Number(t.price).toLocaleString('uz-UZ')} <small>so‘m</small></div><p className="plan-period">{t.duration_days} kunlik foydalanish</p><p>{t.description}</p><ul>{['Barcha e’lon qilingan kurslar', '360p / 720p / 1080p video', 'PDF va Word materiallari', 'Progress va davom ettirish', '2 ta qurilmadan foydalanish'].map(x => <li key={x}><Icon name="check" size={17} />{x}</li>)}</ul><Link to={`/payment/${t.id}`} className="btn-primary">Obunani tanlash <Icon name="arrow" /></Link></article>)}</div>{!loading && !tariffs.length && <p className="empty">{error ? 'Tariflar yuklanmadi.' : 'Tariflar tez orada e’lon qilinadi.'}</p>}<p className="payment-methods"><Icon name="shield" size={16} /> To‘lov usullari <b>payme</b><b>CLICK</b><b>uzum bank</b></p></section>
    <section className="about-band container" id="about"><div><span className="eyebrow">EDUPLATFORM HAQIDA</span><h2>Imkoniyatlar chegarasini<br />bilim bilan kengaytiring.</h2><p>Biz o‘zbek tilidagi ta’limni qulayroq qilamiz. Video darslar, amaliy materiallar va shaxsiy progress — barchasi o‘z ustingizda ishlashingiz uchun.</p><Link to="/register" className="btn-primary">Birinchi qadamni qo‘ying <Icon name="arrow" /></Link></div><div className="about-emblem" aria-hidden="true"><Icon name="book" size={86} /><span>O‘RGANISH HECH QACHON TO‘XTAMAYDI</span></div></section>
    <section className="section container faq-section"><div><span className="eyebrow">SAVOLLARINGIZ BORMI?</span><h2>Boshlashdan oldin</h2></div><div className="faq-list">{[['Darslarni qaysi qurilmalarda ko‘raman?', 'Desktop va mobil brauzerlarda foydalanishingiz mumkin. Bitta hisobga ko‘pi bilan ikkita qurilma ulanadi.'], ['Obuna tugaganda nima bo‘ladi?', 'Pullik darslarga kirish avtomatik yopiladi. Progressingiz saqlanadi; yangi to‘lovdan keyin davom etasiz.'], ['Videoni to‘xtagan joyimdan ko‘ra olamanmi?', 'Ha. Hisobingizga kirgan holda tomosha qiling: video pozitsiyasi avtomatik saqlanadi.'], ['Kurs bilan bepul tanishish mumkinmi?', 'Kurs sahifasida “Bepul” deb belgilangan darslarni hisobingizga kirib ko‘rishingiz mumkin.']].map(([q,a]) => <details key={q}><summary>{q}<span>+</span></summary><p>{a}</p></details>)}</div></section>
  </div>;
}
