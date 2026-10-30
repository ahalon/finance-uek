from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView

from core.models import Asset
from core.forms import AssetForm


class AssetListView(LoginRequiredMixin, ListView):
    model = Asset
    template_name = 'core/asset_list.html'
    context_object_name = 'assets'
    ordering = ['ticker']

    def get_queryset(self):
        qs = Asset.objects.all().order_by('ticker')
        q = self.request.GET.get('q', '').strip()
        if q:
            qs = qs.filter(
                Q(ticker__icontains=q) |
                Q(name__icontains=q) |
                Q(currency__icontains=q)
            )
        return qs

    def get_template_names(self):
        if self.request.headers.get('HX-Request'):
            return ['core/partials/asset_rows.html']
        return [self.template_name]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if 'form' not in context:
            context['form'] = AssetForm()
        context['search_query'] = self.request.GET.get('q', '').strip()
        return context

    def post(self, request, *args, **kwargs):
        return AssetCreateView.as_view()(request, *args, **kwargs)


class AssetCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = Asset
    form_class = AssetForm
    template_name = 'core/asset_form.html'
    success_url = reverse_lazy('asset_list')

    def get_success_message(self, cleaned_data):
        return f'Asset {self.object.ticker} ({self.object.name}) was successfully added!'

    def form_invalid(self, form):
        messages.error(
            self.request,
            'An error occurred while adding the asset. Please verify the entered data.'
        )
        assets = Asset.objects.all().order_by('ticker')
        return render(
            self.request,
            'core/asset_list.html',
            {'form': form, 'assets': assets}
        )


class AssetUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Asset
    form_class = AssetForm
    template_name = 'core/asset_form.html'
    context_object_name = 'asset'
    success_url = reverse_lazy('asset_list')

    def get_success_message(self, cleaned_data):
        return f'Asset {self.object.ticker} was successfully updated!'

    def form_invalid(self, form):
        messages.error(self.request, 'An error occurred while updating the asset.')
        return super().form_invalid(form)


class AssetDeleteView(LoginRequiredMixin, SuccessMessageMixin, DeleteView):
    model = Asset
    template_name = 'core/asset_confirm_delete.html'
    context_object_name = 'asset'
    success_url = reverse_lazy('asset_list')

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.transactions.exists():
            msg = f'Cannot delete asset {self.object.ticker} because there are {self.object.transactions.count()} associated transaction(s).'
            if request.headers.get('HX-Request'):
                return HttpResponse(f'<div class="alert alert-danger py-1 px-2 small mb-0">{msg}</div>', status=400)
            messages.error(request, msg)
            return redirect('asset_list')

        ticker = self.object.ticker
        self.object.delete()

        if request.headers.get('HX-Request'):
            return HttpResponse("")

        messages.success(request, f'Asset {ticker} was successfully deleted.')
        return redirect('asset_list')

    def get_success_message(self, cleaned_data):
        return f'Asset {self.object.ticker} was successfully deleted.'
