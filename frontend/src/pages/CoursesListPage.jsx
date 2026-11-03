import CourseCard from '../components/CourseCard';
import { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import api from '../api/axios';

export default function CoursesListPage() {
  const { t } = useTranslation();
  const [searchParams, setSearchParams] = useSearchParams();
  const [courses, setCourses] = useState([]);
  const [categories, setCategories] = useState([]);
  const [error, setError] = useState('');
  const [count, setCount] = useState(0);
  const page = Math.max(1, Number(searchParams.get('page')) || 1);
  const [loading, setLoading] = useState(true);

  const search = searchParams.get('search') || '';
  const category = searchParams.get('category') || '';
  const minRating = searchParams.get('min_rating') || '';
  const ordering = searchParams.get('ordering') || '';

  useEffect(() => {
    api.get('/courses/categories/')
      .then(res => setCategories(res.data.results || res.data))
      .catch(() => {});
  }, []);

  useEffect(() => {
    let active = true;
    const params = new URLSearchParams();
    params.set('page', page);
    if (search) params.set('search', search);
    if (category) params.set('category', category);
    if (minRating) params.set('min_rating', minRating);
    if (ordering) params.set('ordering', ordering);

    api.get(`/courses/?${params}`)
      .then(res => { if (active) { setCourses(res.data.results || res.data); setCount(res.data.count || 0); setLoading(false); } })
      .catch(() => { if (active) { setError('Kurslar yuklanmadi. Sahifani yangilang.'); setLoading(false); } });
    return () => { active = false; };
  }, [search, category, minRating, ordering, page]);

  const updateParam = (key, value) => {
    setLoading(true); setError('');
    const next = new URLSearchParams(searchParams);
    if (value) next.set(key, value);
    else next.delete(key);
    if (key !== 'page') next.delete('page');
    setSearchParams(next);
  };

  const clearFilters = () => setSearchParams({});

  return (
    <div className="courses-list-page">
      <div className="container">
        <span className="eyebrow">O‘RGANISH UCHUN YANGI IMKONIYAT</span><h1 className="page-title">{t('nav.courses')}</h1>
        {error && <div className="error-banner" role="alert">{error}</div>}

        <div className="catalog-grid">
          {/* Filter sidebar */}
          <aside className="filter-sidebar">
            <div className="filter-header">
              <h3>{t('filter.title')}</h3>
              <button className="link-btn" onClick={clearFilters}>{t('filter.clear')}</button>
            </div>

            <div className="filter-group">
              <h4>{t('filter.category')}</h4>
              <label className="filter-radio">
                <input type="radio" name="cat" checked={!category} onChange={() => updateParam('category', '')} />
                <span>{t('filter.all')}</span>
              </label>
              {categories.map(cat => (
                <label key={cat.id} className="filter-radio">
                  <input
                    type="radio" name="cat"
                    checked={String(category) === String(cat.id)}
                    onChange={() => updateParam('category', cat.id)}
                  />
                  <span>{cat.icon} {cat.name}</span>
                </label>
              ))}
            </div>

            <div className="filter-group">
              <h4>{t('filter.rating')}</h4>
              {[4, 3, 2, 1].map(r => (
                <label key={r} className="filter-radio">
                  <input
                    type="radio" name="rating"
                    checked={String(minRating) === String(r)}
                    onChange={() => updateParam('min_rating', r)}
                  />
                  <span>{'⭐'.repeat(r)} va yuqori</span>
                </label>
              ))}
            </div>

            <div className="filter-group">
              <h4>{t('filter.sort')}</h4>
              <label className="filter-radio">
                <input type="radio" name="sort" checked={!ordering} onChange={() => updateParam('ordering', '')} />
                <span>{t('filter.newest')}</span>
              </label>
              <label className="filter-radio">
                <input type="radio" name="sort" checked={ordering === 'popular'} onChange={() => updateParam('ordering', 'popular')} />
                <span>{t('filter.popular')}</span>
              </label>
              <label className="filter-radio">
                <input type="radio" name="sort" checked={ordering === 'rating'} onChange={() => updateParam('ordering', 'rating')} />
                <span>{t('filter.highest_rated')}</span>
              </label>
            </div>
          </aside>

          {/* Courses */}
          <div>
            {search && <p className="search-result-info">"<b>{search}</b>" — {courses.length} ta natija</p>}
            {loading ? (
              <div className="loading-grid">
                {[1, 2, 3].map(i => <div key={i} className="skeleton-card" />)}
              </div>
            ) : courses.length === 0 ? (
              <div className="empty-state">
                <div className="empty-icon">🔍</div>
                <h3>Hech narsa topilmadi</h3>
                <p>Filtrlarni o'zgartirib ko'ring</p>
              </div>
            ) : (
              <div className="courses-grid">
                {courses.map((course, index) => (
                  <CourseCard key={course.id} course={course} index={index} />
                ))}
              </div>
            )}
            {count > 20 && <div className="pagination"><button className="btn-outline" disabled={page <= 1} onClick={() => updateParam('page', page-1)}>Oldingi</button><span>{page} / {Math.ceil(count/20)}</span><button className="btn-outline" disabled={page*20 >= count} onClick={() => updateParam('page', page+1)}>Keyingi</button></div>}
          </div>
        </div>
      </div>
    </div>
  );
}
