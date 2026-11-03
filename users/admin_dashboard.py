from datetime import timedelta
from django.contrib import admin
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count, Sum, Q
from django.shortcuts import render
from django.urls import path
from django.utils import timezone
from django.utils.decorators import method_decorator

from users.models import User, UserDevice
from courses.models import Course, Lesson, Enrollment
from payments.models import Payment


@staff_member_required
def dashboard_view(request):
    now = timezone.now()
    today = now.date()
    month_start = today.replace(day=1)

    total_users = User.objects.count()
    active_subs = User.objects.filter(subscription_end__gt=now).count()
    new_users_today = User.objects.filter(created_at__date=today).count()
    new_users_month = User.objects.filter(created_at__date__gte=month_start).count()

    paid_payments = Payment.objects.filter(status='paid')
    revenue_today = paid_payments.filter(paid_at__date=today).aggregate(s=Sum('amount'))['s'] or 0
    revenue_month = paid_payments.filter(paid_at__date__gte=month_start).aggregate(s=Sum('amount'))['s'] or 0
    revenue_total = paid_payments.aggregate(s=Sum('amount'))['s'] or 0

    pending_payments = Payment.objects.filter(status='pending').count()

    expiring_soon = User.objects.filter(
        subscription_end__gt=now,
        subscription_end__lte=now + timedelta(days=3),
    ).count()

    total_courses = Course.objects.count()
    published_courses = Course.objects.filter(is_published=True).count()
    total_lessons = Lesson.objects.count()
    total_enrollments = Enrollment.objects.count()

    # Top 5 mashhur kurslar
    top_courses = Course.objects.annotate(
        students_count=Count('enrollments')
    ).order_by('-students_count')[:5]

    # So'nggi 5 to'lov
    recent_payments = Payment.objects.select_related('user', 'tariff').order_by('-created_at')[:10]

    # Eng faol foydalanuvchilar (eng ko'p qurilmaga ega)
    busy_users = User.objects.annotate(dc=Count('devices')).filter(dc__gte=2).order_by('-dc')[:10]

    context = {
        'title': 'Statistika',
        'total_users': total_users,
        'active_subs': active_subs,
        'new_users_today': new_users_today,
        'new_users_month': new_users_month,
        'revenue_today': revenue_today,
        'revenue_month': revenue_month,
        'revenue_total': revenue_total,
        'pending_payments': pending_payments,
        'expiring_soon': expiring_soon,
        'total_courses': total_courses,
        'published_courses': published_courses,
        'total_lessons': total_lessons,
        'total_enrollments': total_enrollments,
        'top_courses': top_courses,
        'recent_payments': recent_payments,
        'busy_users': busy_users,
    }
    return render(request, 'admin/dashboard.html', context)


def get_admin_urls():
    return [
        path('dashboard/', dashboard_view, name='dashboard'),
    ]
