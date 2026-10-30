from decimal import Decimal
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Q
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import ListView, CreateView, UpdateView, DeleteView

from core.models import Transaction, Asset
from core.forms import TransactionForm


class TransactionListView(LoginRequiredMixin, ListView):
    model = Transaction
    template_name = 'core/transaction_list.html'
    context_object_name = 'transactions'

    def get_queryset(self):
        qs = (
            Transaction.objects
            .filter(user=self.request.user)
            .select_related('asset')
        )
        q = self.request.GET.get('q', '').strip()
        if q:
            qs = qs.filter(
                Q(asset__ticker__icontains=q) |
                Q(asset__name__icontains=q) |
                Q(transaction_type__iexact=q)
            )
        return qs

    def get_template_names(self):
        if self.request.headers.get('HX-Request'):
            return ['core/partials/transaction_rows.html']
        return [self.template_name]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if 'form' not in context:
            context['form'] = TransactionForm(user=self.request.user)
        context['search_query'] = self.request.GET.get('q', '').strip()
        return context

    def post(self, request, *args, **kwargs):
        return TransactionCreateView.as_view()(request, *args, **kwargs)


class TransactionCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = Transaction
    form_class = TransactionForm
    template_name = 'core/transaction_form.html'
    success_url = reverse_lazy('transaction_list')
    success_message = 'Transaction added successfully!'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(
            self.request,
            'An error occurred while adding the transaction. Please check the form below.'
        )
        transactions = (
            Transaction.objects
            .filter(user=self.request.user)
            .select_related('asset')
        )
        return render(
            self.request,
            'core/transaction_list.html',
            {'form': form, 'transactions': transactions}
        )


class TransactionUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Transaction
    form_class = TransactionForm
    template_name = 'core/transaction_form.html'
    context_object_name = 'transaction'
    success_url = reverse_lazy('transaction_list')
    success_message = 'Transaction updated successfully!'

    def get_queryset(self):
        return Transaction.objects.filter(user=self.request.user)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_invalid(self, form):
        messages.error(
            self.request,
            'An error occurred while editing the transaction. Please check the form below.'
        )
        return super().form_invalid(form)


class TransactionDeleteView(LoginRequiredMixin, SuccessMessageMixin, DeleteView):
    model = Transaction
    template_name = 'core/transaction_confirm_delete.html'
    context_object_name = 'transaction'
    success_url = reverse_lazy('transaction_list')

    def get_queryset(self):
        return Transaction.objects.filter(user=self.request.user)

    def form_valid(self, form):
        self.object = self.get_object()
        desc = f"{self.object.get_transaction_type_display()} {self.object.quantity} {self.object.asset.ticker}"
        self.object.delete()

        if self.request.headers.get('HX-Request'):
            return HttpResponse("")

        messages.success(self.request, f'Transaction "{desc}" was successfully deleted.')
        return HttpResponseRedirect(self.get_success_url())

    def get_success_message(self, cleaned_data):
        desc = f"{self.object.get_transaction_type_display()} {self.object.quantity} {self.object.asset.ticker}"
        return f'Transaction "{desc}" was successfully deleted.'


class TransactionEstimateView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        asset_id = request.GET.get('asset')
        qty_str = request.GET.get('quantity')
        price_str = request.GET.get('price')
        fee_str = request.GET.get('fee', '0')

        if not (asset_id and qty_str and price_str):
            return HttpResponse("")

        try:
            asset = Asset.objects.get(pk=asset_id)
            qty = Decimal(qty_str)
            price = Decimal(price_str)
            fee = Decimal(fee_str) if fee_str else Decimal('0')
            total_cost = (qty * price) + fee
            total_cost_pln = total_cost * asset.exchange_rate_to_pln

            html = f"""
            <div class="alert alert-info py-2 px-3 small mt-3 mb-0 d-flex justify-content-between align-items-center">
                <span>💰 <strong>Total:</strong> {total_cost:,.2f} {asset.currency}</span>
                <span class="badge bg-primary fs-6">≈ {total_cost_pln:,.2f} PLN</span>
            </div>
            """
            return HttpResponse(html)
        except Exception:
            return HttpResponse("")
