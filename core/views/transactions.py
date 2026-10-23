from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView

from core.models import Transaction
from core.forms import TransactionForm


class TransactionListView(LoginRequiredMixin, ListView):
    model = Transaction
    template_name = 'core/transaction_list.html'
    context_object_name = 'transactions'

    def get_queryset(self):
        return (
            Transaction.objects
            .filter(user=self.request.user)
            .select_related('asset')
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if 'form' not in context:
            context['form'] = TransactionForm(user=self.request.user)
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

    def get_success_message(self, cleaned_data):
        desc = f"{self.object.get_transaction_type_display()} {self.object.quantity} {self.object.asset.ticker}"
        return f'Transaction "{desc}" was successfully deleted.'

