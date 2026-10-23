from decimal import Decimal
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

EXCHANGE_RATES_TO_PLN = {
    'PLN': Decimal('1.0'),
    'USD': Decimal('4.0'),
    'EUR': Decimal('4.3'),
    'GBP': Decimal('5.1'),
}


class Asset(models.Model):
    ticker = models.CharField(max_length=15, unique=True)
    name = models.CharField(max_length=100)
    currency = models.CharField(max_length=3, default='PLN')

    @property
    def exchange_rate_to_pln(self) -> Decimal:
        return EXCHANGE_RATES_TO_PLN.get(self.currency, Decimal('1.0'))

    def __str__(self):
        return f"{self.ticker} ({self.currency})"


class TransactionType(models.TextChoices):
    BUY = 'BUY', 'Buy'
    SELL = 'SELL', 'Sell'


class TransactionQuerySet(models.QuerySet):
    def portfolio_summary(self) -> dict:
        portfolio: dict[str, dict] = {}
        total_invested = Decimal('0.00')
        realized_pnl = Decimal('0.00')

        tx_list = list(self.select_related('asset').order_by('date', 'created_at'))

        for t in tx_list:
            ticker = t.asset.ticker
            rate = t.asset.exchange_rate_to_pln

            if ticker not in portfolio:
                portfolio[ticker] = {
                    'ticker': ticker,
                    'name': t.asset.name,
                    'currency': t.asset.currency,
                    'exchange_rate': rate,
                    'quantity': Decimal('0'),
                    'total_cost': Decimal('0.00'),
                    'avg_buy_price': Decimal('0.00'),
                }

            item = portfolio[ticker]

            if t.transaction_type == TransactionType.BUY:
                item['quantity'] += t.quantity
                item['total_cost'] += t.total_cost
                total_invested += t.total_cost_pln
                if item['quantity'] > Decimal('0'):
                    item['avg_buy_price'] = item['total_cost'] / item['quantity']

            elif t.transaction_type == TransactionType.SELL:
                if item['quantity'] > Decimal('0'):
                    unit_cost = item['total_cost'] / item['quantity']
                    cost_of_sold_shares = unit_cost * t.quantity
                    cost_of_sold_shares_pln = cost_of_sold_shares * rate

                    revenue = (t.quantity * t.price) - t.fee
                    revenue_pln = revenue * rate
                    realized_pnl += (revenue_pln - cost_of_sold_shares_pln)

                    item['quantity'] -= t.quantity
                    item['total_cost'] -= cost_of_sold_shares
                    total_invested -= cost_of_sold_shares_pln

                    if item['quantity'] <= Decimal('0'):
                        item['quantity'] = Decimal('0')
                        item['total_cost'] = Decimal('0.00')
                        item['avg_buy_price'] = Decimal('0.00')
                    else:
                        item['avg_buy_price'] = item['total_cost'] / item['quantity']

        active_holdings = [
            item for item in portfolio.values() if item['quantity'] > Decimal('0')
        ]

        return {
            'total_transactions': len(tx_list),
            'active_assets_count': len(active_holdings),
            'assets_count': len(active_holdings),
            'total_invested': total_invested,
            'realized_pnl': realized_pnl,
            'portfolio': active_holdings,
        }


class Transaction(models.Model):
    TransactionType = TransactionType

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions')
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(
        max_length=4,
        choices=TransactionType.choices,
        default=TransactionType.BUY,
    )
    quantity = models.DecimalField(max_digits=12, decimal_places=4)
    price = models.DecimalField(max_digits=12, decimal_places=4)
    fee = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    date = models.DateField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = TransactionQuerySet.as_manager()

    class Meta:
        ordering = ['-date', '-created_at']

    @property
    def total_cost(self) -> Decimal:
        return (self.quantity * self.price) + self.fee

    @property
    def total_cost_pln(self) -> Decimal:
        return self.total_cost * self.asset.exchange_rate_to_pln

    @property
    def net_value(self) -> Decimal:
        return self.quantity * self.price

    @property
    def net_value_pln(self) -> Decimal:
        return self.net_value * self.asset.exchange_rate_to_pln

    def __str__(self):
        return f"{self.get_transaction_type_display()} {self.quantity} {self.asset.ticker} @ {self.price}"