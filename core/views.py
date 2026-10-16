from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from .models import Transaction
from .forms import TransactionForm


@login_required
def dashboard(request):
    transactions = (
        Transaction.objects
        .filter(user=request.user)
        .select_related('asset')
        .order_by('-date')
    )
    total_transactions = transactions.count()
    assets_count = transactions.values('asset').distinct().count()
    recent_transactions = transactions[:5]

    context = {
        'username': request.user.username,
        'total_transactions': total_transactions,
        'assets_count': assets_count,
        'recent_transactions': recent_transactions,
    }
    return render(request, 'core/dashboard.html', context)


def register(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('dashboard')
    else:
        form = UserCreationForm()

    return render(request, 'registration/register.html', {'form': form})


@login_required
def transaction_list(request):
    if request.method == 'POST':
        form = TransactionForm(request.POST, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Transakcja została pomyślnie dodana!')
            return redirect('transaction_list')
        else:
            messages.error(request, 'Wystąpił błąd podczas dodawania transakcji. Sprawdź formularz.')
    else:
        form = TransactionForm(user=request.user)

    transactions = (
        Transaction.objects
        .filter(user=request.user)
        .select_related('asset')
        .order_by('-date')
    )

    context = {
        'transactions': transactions,
        'form': form,
    }
    return render(request, 'core/transaction_list.html', context)