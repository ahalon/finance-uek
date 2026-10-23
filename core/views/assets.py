from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if 'form' not in context:
            context['form'] = AssetForm()
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
            messages.error(
                request,
                f'Cannot delete asset {self.object.ticker} because there are {self.object.transactions.count()} associated transaction(s).'
            )
            return redirect('asset_list')
        return super().post(request, *args, **kwargs)

    def get_success_message(self, cleaned_data):
        return f'Asset {self.object.ticker} was successfully deleted.'

