from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import TradeInRequest

@login_required
def my_tradeins(request):
    requests = TradeInRequest.objects.filter(customer=request.user)
    return render(request, 'tradein/my_list.html', {'requests': requests})