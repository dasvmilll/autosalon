from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import TradeInRequest
from .forms import TradeInRequestForm

@login_required
def my_tradeins(request):
    requests = TradeInRequest.objects.filter(customer=request.user)
    return render(request, 'tradein/my_list.html', {'requests': requests})

@login_required
def tradein_create(request):
    if request.method == 'POST':
        form = TradeInRequestForm(request.POST, request.FILES)
        if form.is_valid():
            tradein = form.save(commit=False)
            tradein.customer = request.user
            tradein.save()
            messages.success(request, 'Заявка на трейд-ин успешно отправлена!')
            return redirect('tradein:my_list')
    else:
        form = TradeInRequestForm()
    return render(request, 'tradein/create.html', {'form': form})