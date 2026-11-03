from django.db import models
from django.conf import settings


class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    icon = models.CharField(max_length=50, blank=True)

    class Meta:
        verbose_name = 'Kategoriya'
        verbose_name_plural = 'Kategoriyalar'

    def __str__(self):
        return self.name


class Course(models.Model):
    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    thumbnail = models.ImageField(upload_to='courses/thumbnails/')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='courses')
    instructor = models.CharField(max_length=150)
    is_published = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Kurs'
        verbose_name_plural = 'Kurslar'
        ordering = ['order', '-created_at']

    def __str__(self):
        return self.title

    @property
    def total_lessons(self):
        return self.lessons.filter(is_published=True).count()

    @property
    def total_duration(self):
        return sum(l.duration_seconds for l in self.lessons.all() if l.duration_seconds)

    @property
    def average_rating(self):
        from django.db.models import Avg
        avg = self.reviews.filter(is_published=True).aggregate(a=Avg('rating'))['a']
        return round(avg, 1) if avg else 0

    @property
    def reviews_count(self):
        return self.reviews.filter(is_published=True).count()


class Lesson(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='lessons')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    thumbnail = models.ImageField(upload_to='lessons/thumbnails/', null=True, blank=True)
    order = models.PositiveIntegerField(default=0)
    is_published = models.BooleanField(default=False)
    is_free_preview = models.BooleanField(default=False)
    duration_seconds = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Dars'
        verbose_name_plural = 'Darslar'
        ordering = ['order']

    def __str__(self):
        return f"{self.course.title} — {self.title}"


class LessonAttachment(models.Model):
    FILE_TYPES = [
        ('pdf', 'PDF'),
        ('word', 'Word'),
        ('other', 'Boshqa'),
    ]
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='attachments')
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to='lessons/attachments/')
    file_type = models.CharField(max_length=10, choices=FILE_TYPES, default='other')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Biriktirma fayl"
        verbose_name_plural = "Biriktirma fayllar"

    def __str__(self):
        return self.title


class Enrollment(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='enrollments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    enrolled_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'course')
        verbose_name = "Ro'yxat"
        verbose_name_plural = "Ro'yxatlar"

    def __str__(self):
        return f"{self.user.email} — {self.course.title}"

    def get_progress(self):
        total = self.course.lessons.filter(is_published=True).count()
        if total == 0:
            return 0
        completed = self.user.progresses.filter(
            lesson__course=self.course, lesson__is_published=True, is_completed=True
        ).count()
        return round((completed / total) * 100)
