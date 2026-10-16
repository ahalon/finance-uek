from django.contrib import admin
from .models import Asset, Transaction

@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = ('ticker', 'name', 'currency')
    search_fields = ('ticker', 'name')

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('date', 'user', 'asset', 'transaction_type', 'quantity', 'price', 'total_cost')
    list_filter = ('transaction_type', 'asset')


