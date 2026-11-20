import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import TradeInRequest
from .forms import TradeInRequestForm, TradeInEstimateForm

logger = logging.getLogger(__name__)


@login_required
def my_tradeins(request):
    requests = TradeInRequest.objects.filter(customer=request.user)
    return render(request, 'tradein/my_list.html', {'requests': requests})


@login_required
def tradein_detail(request, pk):
    """Просмотр конкретной заявки (FR-18)."""
    tradein = get_object_or_404(TradeInRequest, pk=pk, customer=request.user)
    logger.info(f'tradein_detail: пользователь {request.user.username} открыл заявку #{pk}')
    return render(request, 'tradein/detail.html', {'tradein': tradein})


@login_required
def tradein_create(request):
    if request.method == 'POST':
        form = TradeInRequestForm(request.POST, request.FILES)
        if form.is_valid():
            tradein = form.save(commit=False)
            tradein.customer = request.user
            tradein.save()
            logger.info(
                f'tradein_create: НОВАЯ ЗАЯВКА #{tradein.pk} от {request.user.username} — '
                f'{tradein.brand} {tradein.model_name} ({tradein.year} г., пробег {tradein.mileage_km} км)'
            )
            messages.success(request, 'Заявка на трейд-ин успешно отправлена!')
            return redirect('tradein:my_list')
        else:
            logger.warning(f'tradein_create: ошибки валидации формы: {form.errors}')
    else:
        form = TradeInRequestForm()
    return render(request, 'tradein/create.html', {'form': form})


@login_required
def appraiser_list(request):
    if request.user.role not in ['appraiser', 'admin']:
        messages.error(request, 'У вас нет прав.')
        return redirect('core:home')
    requests = TradeInRequest.objects.all().select_related('customer')
    return render(request, 'tradein/appraiser_list.html', {'requests': requests})


@login_required
def estimate_update(request, pk):
    if request.user.role not in ['appraiser', 'admin']:
        messages.error(request, 'У вас нет прав.')
        return redirect('core:home')
    tradein = get_object_or_404(TradeInRequest, pk=pk)
    if request.method == 'POST':
        form = TradeInEstimateForm(request.POST, instance=tradein)
        if form.is_valid():
            estimate = form.save(commit=False)
            estimate.appraiser = request.user
            estimate.status = 'estimated'
            estimate.save()
            logger.info(
                f'estimate_update: оценщик {request.user.username} выставил оценку '
                f'{estimate.preliminary_estimate}₽ для заявки #{tradein.pk} '
                f'({tradein.brand} {tradein.model_name})'
            )
            messages.success(request, 'Оценка сохранена.')
            return redirect('tradein:appraiser_list')
        else:
            logger.warning(f'estimate_update: ошибки валидации формы: {form.errors}')
    else:
        form = TradeInEstimateForm(instance=tradein)
    return render(request, 'tradein/estimate_form.html', {'form': form, 'tradein': tradein})