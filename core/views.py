from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def dashboard(request):
    context = {'username': request.user.username}
    return render(request, 'core/dashboard.html', context)

@login_required
def transaction_list(request):
    return render(request, 'core/transaction_list.html')

@login_required
def category_list(request):
    return render(request, 'core/category_list.html')