import { Link } from 'react-router-dom';
import { mediaUrl } from '../api/axios';
import Icon from './Icon';

export default function CourseCard({ course, index = 0 }) {
  return <Link to={`/courses/${course.slug}`} className={`course-card course-tone-${index % 4}`}>
    <div className="course-thumb">
      {course.thumbnail ? <img src={mediaUrl(course.thumbnail)} alt={course.title} loading="lazy" onError={e => { e.currentTarget.hidden = true; }} /> : null}
      <div className="course-art" aria-hidden="true"><Icon name={['code', 'chart', 'globe', 'book'][index % 4]} size={64} /><span>{course.category?.name || 'Yangi bilimlar'}</span></div>
      <span className="course-category-badge">{course.category?.name || 'Video kurs'}</span>
      <span className="course-open"><Icon name="arrow" /></span>
    </div>
    <div className="course-info">
      <div className="card-eyebrow">VIDEO DARSLAR {course.average_rating > 0 && <span>★ {course.average_rating}</span>}</div>
      <h3>{course.title}</h3>
      <p className="instructor">{course.instructor}</p>
      <div className="course-meta"><span><Icon name="book" size={16} /> {course.total_lessons} ta dars</span><span>O‘rganish <Icon name="arrow" size={15} /></span></div>
      {course.is_enrolled && <div className="card-progress"><span>O‘zlashtirilgan <b>{course.progress}%</b></span><progress max="100" value={course.progress} /></div>}
    </div>
  </Link>;
}
