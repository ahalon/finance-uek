from django.urls import path
from core.views import (
    RegisterView,
    DashboardView,
    TransactionListView,
    TransactionCreateView,
    TransactionUpdateView,
    TransactionDeleteView,
    AssetListView,
    AssetCreateView,
    AssetUpdateView,
    AssetDeleteView,
)

urlpatterns = [
    path('', DashboardView.as_view(), name='dashboard'),
    path('accounts/register/', RegisterView.as_view(), name='register'),
    path('transactions/', TransactionListView.as_view(), name='transaction_list'),
    path('transactions/create/', TransactionCreateView.as_view(), name='transaction_create'),
    path('transactions/<int:pk>/edit/', TransactionUpdateView.as_view(), name='transaction_edit'),
    path('transactions/<int:pk>/delete/', TransactionDeleteView.as_view(), name='transaction_delete'),
    path('assets/', AssetListView.as_view(), name='asset_list'),
    path('assets/create/', AssetCreateView.as_view(), name='asset_create'),
    path('assets/<int:pk>/edit/', AssetUpdateView.as_view(), name='asset_edit'),
    path('assets/<int:pk>/delete/', AssetDeleteView.as_view(), name='asset_delete'),
]

