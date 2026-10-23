from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from .models import Asset, Transaction
from .forms import TransactionForm, AssetForm


@login_required
def dashboard(request):
    transactions = (
        Transaction.objects
        .filter(user=request.user)
        .select_related('asset')
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


# TRANSACTIONS

@login_required
def transaction_list(request):
    if request.method == 'POST':
        form = TransactionForm(request.POST, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Transaction added successfully!')
            return redirect('transaction_list')
        else:
            messages.error(request, 'An error occurred while adding the transaction. Please check the form below.')
    else:
        form = TransactionForm(user=request.user)

    transactions = (
        Transaction.objects
        .filter(user=request.user)
        .select_related('asset')
    )

    context = {
        'transactions': transactions,
        'form': form,
    }
    return render(request, 'core/transaction_list.html', context)


@login_required
def transaction_edit(request, pk):
    transaction = get_object_or_404(Transaction, pk=pk, user=request.user)
    if request.method == 'POST':
        form = TransactionForm(request.POST, instance=transaction, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Transaction updated successfully!')
            return redirect('transaction_list')
        else:
            messages.error(request, 'An error occurred while editing the transaction. Please check the form below.')
    else:
        form = TransactionForm(instance=transaction, user=request.user)

    context = {
        'form': form,
        'transaction': transaction,
    }
    return render(request, 'core/transaction_form.html', context)


@login_required
def transaction_delete(request, pk):
    transaction = get_object_or_404(Transaction, pk=pk, user=request.user)
    if request.method == 'POST':
        desc = f"{transaction.get_transaction_type_display()} {transaction.quantity} {transaction.asset.ticker}"
        transaction.delete()
        messages.success(request, f'Transaction "{desc}" was successfully deleted.')
        return redirect('transaction_list')

    return render(request, 'core/transaction_confirm_delete.html', {'transaction': transaction})


# ASSETS

@login_required
def asset_list(request):
    if request.method == 'POST':
        form = AssetForm(request.POST)
        if form.is_valid():
            asset = form.save()
            messages.success(request, f'Asset {asset.ticker} ({asset.name}) was successfully added!')
            return redirect('asset_list')
        else:
            messages.error(request, 'An error occurred while adding the asset. Please verify the entered data.')
    else:
        form = AssetForm()

    assets = Asset.objects.all().order_by('ticker')
    context = {
        'assets': assets,
        'form': form,
    }
    return render(request, 'core/asset_list.html', context)


@login_required
def asset_edit(request, pk):
    asset = get_object_or_404(Asset, pk=pk)
    if request.method == 'POST':
        form = AssetForm(request.POST, instance=asset)
        if form.is_valid():
            form.save()
            messages.success(request, f'Asset {asset.ticker} was successfully updated!')
            return redirect('asset_list')
        else:
            messages.error(request, 'An error occurred while updating the asset.')
    else:
        form = AssetForm(instance=asset)

    return render(request, 'core/asset_form.html', {'form': form, 'asset': asset})


@login_required
def asset_delete(request, pk):
    asset = get_object_or_404(Asset, pk=pk)
    if request.method == 'POST':
        if asset.transactions.exists():
            messages.error(
                request,
                f'Cannot delete asset {asset.ticker} because there are {asset.transactions.count()} associated transaction(s).'
            )
            return redirect('asset_list')
        ticker = asset.ticker
        asset.delete()
        messages.success(request, f'Asset {ticker} was successfully deleted.')
        return redirect('asset_list')

    return render(request, 'core/asset_confirm_delete.html', {'asset': asset})