from django.contrib import admin
from django.utils.html import format_html
from .models import Wishlist, Review, LessonComment, Question, Answer, Certificate


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ('user', 'course', 'created_at')
    search_fields = ('user__email', 'course__title')


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('user', 'course', 'rating_stars', 'short_comment', 'is_published', 'created_at')
    list_filter = ('rating', 'is_published')
    list_editable = ('is_published',)
    search_fields = ('user__email', 'course__title', 'comment')

    def rating_stars(self, obj):
        return '⭐' * obj.rating
    rating_stars.short_description = 'Reyting'

    def short_comment(self, obj):
        return obj.comment[:60] + '...' if len(obj.comment) > 60 else obj.comment
    short_comment.short_description = 'Izoh'


@admin.register(LessonComment)
class LessonCommentAdmin(admin.ModelAdmin):
    list_display = ('user', 'lesson', 'short_content', 'is_published', 'created_at')
    list_filter = ('is_published',)
    list_editable = ('is_published',)
    search_fields = ('user__email', 'content')

    def short_content(self, obj):
        return obj.content[:80]


class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 1
    readonly_fields = ('is_admin_answer', 'created_at')
    fields = ('author', 'content', 'is_admin_answer', 'created_at')


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('user', 'title', 'lesson', 'course', 'status_badge', 'answers_count', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('title', 'content', 'user__email')
    inlines = [AnswerInline]
    readonly_fields = ('created_at', 'updated_at')
    list_per_page = 25
    ordering = ('-created_at',)

    def status_badge(self, obj):
        colors = {'pending': 'orange', 'answered': 'green', 'closed': 'gray'}
        return format_html(
            '<span style="color:{};font-weight:bold">{}</span>',
            colors.get(obj.status, 'gray'),
            obj.get_status_display()
        )
    status_badge.short_description = 'Holat'

    def answers_count(self, obj):
        count = obj.answers.count()
        return format_html('<b>{}</b>', count) if count else '0'
    answers_count.short_description = 'Javoblar'

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for instance in instances:
            if not instance.pk and not instance.author_id:
                instance.author = request.user
            instance.save()
        formset.save_m2m()


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ('author', 'question', 'short_content', 'is_admin_answer', 'created_at')
    list_filter = ('is_admin_answer', 'created_at')
    search_fields = ('author__email', 'content', 'question__title')

    def short_content(self, obj):
        return obj.content[:80]


@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ('certificate_number', 'user', 'course', 'issued_at')
    search_fields = ('certificate_number', 'user__email', 'course__title')
    readonly_fields = ('certificate_number', 'issued_at')
