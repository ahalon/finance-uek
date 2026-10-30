from .auth import RegisterView
from .dashboard import DashboardView
from .transactions import (
    TransactionListView,
    TransactionCreateView,
    TransactionUpdateView,
    TransactionDeleteView,
    TransactionEstimateView,
)
from .assets import (
    AssetListView,
    AssetCreateView,
    AssetUpdateView,
    AssetDeleteView,
)

register = RegisterView.as_view()
dashboard = DashboardView.as_view()
transaction_list = TransactionListView.as_view()
transaction_edit = TransactionUpdateView.as_view()
transaction_delete = TransactionDeleteView.as_view()
asset_list = AssetListView.as_view()
asset_edit = AssetUpdateView.as_view()
asset_delete = AssetDeleteView.as_view()

__all__ = [
    'RegisterView',
    'DashboardView',
    'TransactionListView',
    'TransactionCreateView',
    'TransactionUpdateView',
    'TransactionDeleteView',
    'TransactionEstimateView',
    'AssetListView',
    'AssetCreateView',
    'AssetUpdateView',
    'AssetDeleteView',
    'register',
    'dashboard',
    'transaction_list',
    'transaction_edit',
    'transaction_delete',
    'asset_list',
    'asset_edit',
    'asset_delete',
]
