from django import forms
from .models import Asset, Transaction


class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['asset', 'transaction_type', 'quantity', 'price', 'fee', 'date']
        labels = {
            'asset': 'Asset (Stock / ETF)',
            'transaction_type': 'Transaction Type',
            'quantity': 'Quantity',
            'price': 'Unit Price',
            'fee': 'Fee / Commission',
            'date': 'Transaction Date',
        }
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'quantity': forms.NumberInput(attrs={'step': 'any', 'min': '0.0001', 'placeholder': 'e.g. 10'}),
            'price': forms.NumberInput(attrs={'step': 'any', 'min': '0.0001', 'placeholder': 'e.g. 120.50'}),
            'fee': forms.NumberInput(attrs={'step': 'any', 'min': '0', 'placeholder': 'e.g. 5.00'}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        self.fields['date'].input_formats = ['%Y-%m-%d']
        self.fields['asset'].queryset = Asset.objects.all().order_by('ticker')

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.user and not getattr(instance, 'user_id', None):
            instance.user = self.user
        if commit:
            instance.save()
        return instance


class AssetForm(forms.ModelForm):
    class Meta:
        model = Asset
        fields = ['ticker', 'name', 'currency']
        labels = {
            'ticker': 'Symbol / Ticker',
            'name': 'Full Name',
            'currency': 'Currency (3 letters)',
        }
        widgets = {
            'ticker': forms.TextInput(attrs={'placeholder': 'e.g. AAPL, MSFT, VWCE'}),
            'name': forms.TextInput(attrs={'placeholder': 'e.g. Apple Inc., Microsoft'}),
            'currency': forms.TextInput(attrs={'placeholder': 'USD', 'maxlength': 3}),
        }

    def clean_ticker(self):
        ticker = self.cleaned_data.get('ticker')
        if ticker:
            return ticker.strip().upper()
        return ticker

    def clean_currency(self):
        currency = self.cleaned_data.get('currency')
        if currency:
            return currency.strip().upper()
        return currency