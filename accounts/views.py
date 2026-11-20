import logging
from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib import messages
from .forms import CustomUserCreationForm

logger = logging.getLogger(__name__)


def register(request):
    """Регистрация нового пользователя."""
    logger.info(f'register: открыта страница регистрации (IP: {request.META.get("REMOTE_ADDR")})')
    
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            user.role = 'customer'
            user.save(update_fields=['role'])
            login(request, user)
            logger.info(f'register: создан новый пользователь "{user.username}" (role={user.role}, email={user.email})')
            messages.success(request, 'Регистрация прошла успешно! Добро пожаловать.')
            return redirect('core:home')
        else:
            logger.warning(f'register: ошибки валидации формы: {form.errors}')
    else:
        form = CustomUserCreationForm()
    return render(request, 'registration/register.html', {'form': form})