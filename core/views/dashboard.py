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
            .order_by('date', 'created_at')
        )

        summary = calculate_portfolio_summary(transactions)

        recent_transactions = transactions.order_by('-date', '-created_at')[:5]

        context.update(summary)
        context.update({
            'username': self.request.user.username,
            'recent_transactions': recent_transactions,
        })
        return context