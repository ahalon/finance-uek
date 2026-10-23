from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView

from core.models import Transaction
from core.services import calculate_portfolio_summary


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'core/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        transactions = (
            Transaction.objects
            .filter(user=self.request.user)
            .select_related('asset')
        )
        summary = calculate_portfolio_summary(transactions)
        context.update(summary)
        context['username'] = self.request.user.username
        return context

