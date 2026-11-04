from datetime import timedelta

from django.conf import settings
from django.contrib import admin
from django.db.models import Count, Sum
from django.db.models.functions import TruncDate
from django.shortcuts import render
from django.urls import path
from django.utils import timezone

from courses.models import Course, Enrollment, Lesson
from payments.models import Payment
from users.models import User, UserDevice


def dashboard_view(request):
    now = timezone.now()
    today = timezone.localdate()
    days = {'7': 7, '30': 30, '90': 90}.get(request.GET.get('period', '30'), 30)
    start = today - timedelta(days=days - 1)
    can_users = request.user.has_perm('users.view_user')
    can_payments = request.user.has_perm('payments.view_payment')
    can_courses = request.user.has_perm('courses.view_course')
    context = {
        **admin.site.each_context(request),
        'title': 'Boshqaruv markazi', 'period': str(days), 'days': days,
        'can_users': can_users, 'can_payments': can_payments,
        'can_courses': can_courses, 'today': today,
        'storage_enabled': settings.OBJECT_STORAGE_ENABLED, 'chart_end': today.strftime('%d.%m'),
    }
    users_daily, revenue_daily = {}, {}
    if can_users:
        users = User.objects.all()
        context.update(
            total_users=users.count(),
            new_users=users.filter(created_at__date__gte=start).count(),
            active_subs=users.filter(is_active=True, subscription_end__gt=now).count(),
            expiring_soon=users.filter(is_active=True, subscription_end__gt=now,
                                      subscription_end__lte=now + timedelta(days=3)).count(),
            recent_users=users.order_by('-created_at')[:5],
        )
        users_daily = {row['day']: row['count'] for row in users.filter(
            created_at__date__gte=start).annotate(day=TruncDate('created_at')).values('day').annotate(count=Count('pk'))}
    if can_payments:
        paid = Payment.objects.filter(status='paid')
        context.update(
            revenue_total=paid.aggregate(total=Sum('amount'))['total'] or 0,
            revenue_period=paid.filter(paid_at__date__gte=start).aggregate(total=Sum('amount'))['total'] or 0,
            pending_payments=Payment.objects.filter(status='pending').count(),
            recent_payments=Payment.objects.select_related('user', 'tariff').order_by('-created_at')[:8],
        )
        revenue_daily = {row['day']: float(row['total']) for row in paid.filter(
            paid_at__date__gte=start).annotate(day=TruncDate('paid_at')).values('day').annotate(total=Sum('amount'))}
    if can_courses:
        context.update(total_courses=Course.objects.count(),
                       published_courses=Course.objects.filter(is_published=True).count(),
                       draft_courses=Course.objects.filter(is_published=False).count())
        if request.user.has_perm('courses.view_enrollment'):
            context['top_courses'] = Course.objects.annotate(students_count=Count('enrollments')).order_by('-students_count', 'title')[:5]
            context['total_enrollments'] = Enrollment.objects.count()
    if request.user.has_perm('courses.view_lesson'):
        context['total_lessons'] = Lesson.objects.count()
    if request.user.has_perm('users.view_userdevice'):
        context['active_devices'] = UserDevice.objects.filter(last_seen__gte=now - timedelta(days=1)).count()
    context['chart_data'] = [
        {'label': (start + timedelta(days=i)).strftime('%d.%m'),
         'users': users_daily.get(start + timedelta(days=i), 0),
         'revenue': revenue_daily.get(start + timedelta(days=i), 0)} for i in range(days)
    ]
    return render(request, 'admin/dashboard.html', context)


def get_admin_urls():
    from users.admin_account import account_view
    return [
        path('', admin.site.admin_view(dashboard_view), name='overview'),
        path('dashboard/', admin.site.admin_view(dashboard_view), name='dashboard'),
        path('account/', admin.site.admin_view(account_view), name='account'),
    ]
