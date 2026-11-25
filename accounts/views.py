import logging
from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib import messages
from .forms import CustomUserCreationForm
from django.db import IntegrityError

logger = logging.getLogger(__name__)


def register(request):
    """Регистрация нового пользователя."""
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()
                logger.info(f'register: новый пользователь {user.username} ({user.email})')
                login(request, user)
                messages.success(request, 'Регистрация прошла успешно!')
                return redirect('core:home')
            except IntegrityError as e:
                logger.error(f'register: дубликат пользователя: {e}', exc_info=True)
                messages.error(request, 'Пользователь с таким email или именем уже существует.')
            except Exception as e:
                logger.error(f'register: ошибка при создании пользователя: {e}', exc_info=True)
                messages.error(request, 'Произошла ошибка при регистрации. Попробуйте позже.')
        else:
            logger.warning(f'register: ошибки валидации: {form.errors}')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'accounts/register.html', {'form': form})