from decimal import Decimal
from typing import Dict, Any
from core.models import Transaction


def calculate_portfolio_summary(transactions) -> Dict[str, Any]:
    portfolio: Dict[str, Any] = {}
    total_invested = Decimal('0.00')
    realized_pnl = Decimal('0.00')

    tx_list = list(transactions)

    for t in tx_list:
        ticker = t.asset.ticker
        if ticker not in portfolio:
            portfolio[ticker] = {
                'ticker': ticker,
                'name': t.asset.name,
                'currency': t.asset.currency,
                'quantity': Decimal('0'),
                'total_cost': Decimal('0.00'),
                'avg_buy_price': Decimal('0.00'),
            }

        item = portfolio[ticker]

        if t.transaction_type == Transaction.TransactionType.BUY:
            item['quantity'] += t.quantity
            item['total_cost'] += t.total_cost
            total_invested += t.total_cost
            item['avg_buy_price'] = item['total_cost'] / item['quantity']

        elif t.transaction_type == Transaction.TransactionType.SELL:
            if item['quantity'] > Decimal('0'):
                unit_cost = item['total_cost'] / item['quantity']
                cost_of_sold_shares = unit_cost * t.quantity

                revenue = (t.quantity * t.price) - t.fee
                realized_pnl += (revenue - cost_of_sold_shares)

                item['quantity'] -= t.quantity
                item['total_cost'] -= cost_of_sold_shares
                total_invested -= cost_of_sold_shares

                if item['quantity'] == Decimal('0'):
                    item['total_cost'] = Decimal('0.00')
                    item['avg_buy_price'] = Decimal('0.00')

    active_holdings = [
        item for item in portfolio.values() if item['quantity'] > Decimal('0')
    ]

    return {
        'total_transactions': len(tx_list),
        'active_assets_count': len(active_holdings),
        'total_invested': total_invested,
        'realized_pnl': realized_pnl,
        'portfolio': active_holdings,
    }