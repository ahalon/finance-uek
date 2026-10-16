from django.db import models
from django.contrib.auth.models import User


class Asset(models.Model):
    ticker = models.CharField(max_length=15, unique=True)
    name = models.CharField(max_length=100)
    currency = models.CharField(max_length=3, default='PLN')

    def __str__(self):
        return f"{self.ticker} ({self.currency})"


class Transaction(models.Model):
    class TransactionType(models.TextChoices):
        BUY = 'BUY', 'Buy'
        SELL = 'SELL', 'Sell'

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
    date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def total_cost(self):
        return (self.quantity * self.price) + self.fee

    def __str__(self):
        return f"{self.transaction_type} {self.quantity} {self.asset.ticker} @ {self.price}"