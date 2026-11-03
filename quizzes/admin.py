from django.contrib import admin
from .models import Quiz, QuizQuestion, Choice, QuizAttempt


class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 4
    fields = ('text', 'is_correct')


@admin.register(QuizQuestion)
class QuizQuestionAdmin(admin.ModelAdmin):
    list_display = ('quiz', 'short_text', 'order')
    list_filter = ('quiz',)
    inlines = [ChoiceInline]

    def short_text(self, obj):
        return obj.text[:80]


class QuestionInline(admin.TabularInline):
    model = QuizQuestion
    extra = 0
    fields = ('text', 'order')
    show_change_link = True


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ('title', 'lesson', 'pass_percentage', 'is_active', 'questions_count')
    list_filter = ('is_active',)
    inlines = [QuestionInline]

    def questions_count(self, obj):
        return obj.questions.count()
    questions_count.short_description = 'Savollar'


@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = ('user', 'quiz', 'score', 'total', 'percentage', 'is_passed', 'created_at')
    list_filter = ('is_passed',)
    search_fields = ('user__email', 'quiz__title')
    readonly_fields = ('answers_data', 'created_at')
