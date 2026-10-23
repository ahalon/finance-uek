from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView

from core.models import Transaction


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'core/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_txs = Transaction.objects.filter(user=self.request.user)
        summary = user_txs.portfolio_summary()
        recent_transactions = user_txs.select_related('asset').order_by('-date', '-created_at')[:5]

        context.update(summary)
        context['recent_transactions'] = recent_transactions
        context['username'] = self.request.user.username
        return context