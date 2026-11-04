from django import forms
from django.contrib import admin, messages
from django.contrib.auth import password_validation, update_session_auth_hash
from django.contrib.admin.models import CHANGE, LogEntry
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from users.models import User


class AdminAccountForm(forms.ModelForm):
    current_password = forms.CharField(label='Joriy parol', strip=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'current-password'}))
    new_password1 = forms.CharField(label='Yangi parol', required=False, strip=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
        help_text='Parolni almashtirmasangiz, bo‘sh qoldiring. Kamida 8 belgidan foydalaning.')
    new_password2 = forms.CharField(label='Yangi parolni takrorlang', required=False, strip=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}))

    class Meta:
        model = User
        fields = ('email', 'full_name')
        labels = {'email': 'Login (email)', 'full_name': 'Ism va familiya'}
        widgets = {'email': forms.EmailInput(attrs={'autocomplete': 'email'}),
                   'full_name': forms.TextInput(attrs={'autocomplete': 'name'})}

    def clean_current_password(self):
        password = self.cleaned_data['current_password']
        if not self.instance.check_password(password):
            raise ValidationError('Joriy parol noto‘g‘ri.')
        return password

    def clean_email(self):
        email = User.objects.normalize_email(self.cleaned_data['email'].strip())
        if User.objects.exclude(pk=self.instance.pk).filter(email__iexact=email).exists():
            raise ValidationError('Bu email boshqa akkauntda ishlatilgan.')
        return email

    def clean(self):
        data = super().clean()
        first, second = data.get('new_password1'), data.get('new_password2')
        if first or second:
            if first != second:
                self.add_error('new_password2', 'Yangi parollar bir xil bo‘lishi kerak.')
            elif first:
                candidate = User(email=data.get('email', self.instance.email), full_name=data.get('full_name', self.instance.full_name))
                try:
                    password_validation.validate_password(first, candidate)
                except ValidationError as exc:
                    self.add_error('new_password1', exc)
        return data


@require_http_methods(['GET', 'POST'])
def account_view(request):
    form = AdminAccountForm(request.POST if request.method == 'POST' else None, instance=request.user)
    if request.method == 'POST' and form.is_valid():
        try:
            with transaction.atomic():
                user = form.save(commit=False)
                if form.cleaned_data['new_password1']:
                    user.set_password(form.cleaned_data['new_password1'])
                user.save(update_fields=['email', 'full_name', 'password', 'updated_at'])
                LogEntry.objects.log_actions(user_id=user.pk, queryset=User.objects.filter(pk=user.pk),
                    action_flag=CHANGE, change_message='Admin akkaunt sozlamalari yangilandi.')
        except IntegrityError:
            form.add_error('email', 'Bu email band. Boshqa email kiriting.')
        else:
            update_session_auth_hash(request, user)
            messages.success(request, 'Akkaunt yangilandi. Keyingi kirishda yangi email va paroldan foydalaning.')
            return redirect('admin:account')
    return render(request, 'admin/account.html', {
        **admin.site.each_context(request), 'title': 'Akkaunt sozlamalari', 'form': form,
    })
