from typing import Dict, Any
from decimal import Decimal
from core.models import Transaction


def calculate_portfolio_summary(transactions) -> Dict[str, Any]:
    if hasattr(transactions, 'count'):
        total_transactions = transactions.count()
    else:
        total_transactions = len(transactions)

    if hasattr(transactions, 'values'):
        assets_count = transactions.values('asset').distinct().count()
    else:
        assets_count = len({t.asset_id for t in transactions})

    recent_transactions = transactions[:5]

    portfolio: Dict[str, Any] = {}
    for t in transactions:
        ticker = t.asset.ticker
        if ticker not in portfolio:
            portfolio[ticker] = {
                'name': t.asset.name,
                'quantity': Decimal('0'),
                'total_cost': Decimal('0'),
                'currency': t.asset.currency,
            }
        if t.transaction_type == Transaction.TransactionType.BUY:
            portfolio[ticker]['quantity'] += t.quantity
            portfolio[ticker]['total_cost'] += t.total_cost
        elif t.transaction_type == Transaction.TransactionType.SELL:
            portfolio[ticker]['quantity'] -= t.quantity
            portfolio[ticker]['total_cost'] -= t.total_cost

    return {
        'total_transactions': total_transactions,
        'assets_count': assets_count,
        'recent_transactions': recent_transactions,
        'portfolio': portfolio,
    }