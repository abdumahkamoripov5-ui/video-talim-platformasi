from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from .models import Quiz, QuizQuestion, Choice, QuizAttempt
from .serializers import QuizSerializer, QuizAttemptSerializer


class QuizDetailView(generics.RetrieveAPIView):
    serializer_class = QuizSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'lesson_id'

    def get_object(self):
        try:
            quiz = Quiz.objects.prefetch_related('questions__choices').get(
                lesson_id=self.kwargs['lesson_id'], is_active=True, lesson__is_published=True, lesson__course__is_published=True
            )
            if not quiz.lesson.is_free_preview and not self.request.user.has_active_subscription:
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied('Obuna kerak')
            return quiz
        except Quiz.DoesNotExist:
            from rest_framework.exceptions import NotFound
            raise NotFound("Test topilmadi")


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def submit_quiz(request, lesson_id):
    """answers: {question_id: choice_id} formatida"""
    try:
        quiz = Quiz.objects.select_related('lesson').get(lesson_id=lesson_id, is_active=True, lesson__is_published=True, lesson__course__is_published=True)
    except Quiz.DoesNotExist:
        return Response({'detail': 'Test topilmadi'}, status=status.HTTP_404_NOT_FOUND)

    if not quiz.lesson.is_free_preview and not request.user.has_active_subscription:
        return Response({'detail': 'Obuna kerak'}, status=403)
    answers = request.data.get('answers', {})
    if not isinstance(answers, dict):
        return Response({'detail': 'Javoblar obyekt bo‘lishi kerak'}, status=400)
    questions = quiz.questions.prefetch_related('choices').all()

    score = 0
    total = questions.count()
    detailed = {}

    for question in questions:
        selected_choice_id = answers.get(str(question.id))
        correct_choice = question.choices.filter(is_correct=True).first()

        is_correct = False
        if selected_choice_id and correct_choice:
            try:
                is_correct = int(selected_choice_id) == correct_choice.id
            except (ValueError, TypeError):
                return Response({'detail': 'Javob formati noto‘g‘ri'}, status=400)

        if is_correct:
            score += 1

        detailed[str(question.id)] = {
            'selected': selected_choice_id,
            'correct': correct_choice.id if correct_choice else None,
            'is_correct': is_correct,
        }

    is_passed = (score / total * 100) >= quiz.pass_percentage if total else False

    attempt = QuizAttempt.objects.create(
        user=request.user,
        quiz=quiz,
        score=score,
        total=total,
        is_passed=is_passed,
        answers_data=detailed,
    )

    return Response({
        'attempt_id': attempt.id,
        'score': score,
        'total': total,
        'percentage': attempt.percentage,
        'is_passed': is_passed,
        'pass_percentage': quiz.pass_percentage,
        'detailed': detailed,
    })


class MyAttemptsView(generics.ListAPIView):
    serializer_class = QuizAttemptSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return self.request.user.quiz_attempts.select_related('quiz')
