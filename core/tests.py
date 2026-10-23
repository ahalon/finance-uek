from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from decimal import Decimal
from datetime import date
from core.models import Asset, Transaction
from core.forms import TransactionForm, AssetForm


class ModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password123')
        self.asset = Asset.objects.create(ticker='AAPL', name='Apple Inc.', currency='USD')

    def test_asset_str(self):
        self.assertEqual(str(self.asset), 'AAPL (USD)')

    def test_transaction_cost_and_str(self):
        tx = Transaction.objects.create(
            user=self.user,
            asset=self.asset,
            transaction_type=Transaction.TransactionType.BUY,
            quantity=Decimal('10.0000'),
            price=Decimal('150.0000'),
            fee=Decimal('5.00'),
            date=date(2026, 1, 15)
        )
        self.assertEqual(tx.total_cost, Decimal('1505.00'))
        self.assertEqual(str(tx), 'Buy 10.0000 AAPL @ 150.0000')


class FormTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password123')
        self.asset = Asset.objects.create(ticker='MSFT', name='Microsoft', currency='USD')

    def test_asset_form_clean(self):
        form = AssetForm(data={'ticker': ' nvda ', 'name': 'NVIDIA Corp', 'currency': 'usd'})
        self.assertTrue(form.is_valid())
        asset = form.save()
        self.assertEqual(asset.ticker, 'NVDA')
        self.assertEqual(asset.currency, 'USD')

    def test_transaction_form_save_with_user(self):
        form = TransactionForm(
            data={
                'asset': self.asset.id,
                'transaction_type': 'BUY',
                'quantity': '5',
                'price': '200.00',
                'fee': '1.00',
                'date': '2026-05-10',
            },
            user=self.user
        )
        self.assertTrue(form.is_valid())
        tx = form.save()
        self.assertEqual(tx.user, self.user)


class ViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='investor', password='password123')
        self.client = Client()
        self.asset = Asset.objects.create(ticker='VOO', name='Vanguard S&P 500', currency='USD')
        self.tx = Transaction.objects.create(
            user=self.user,
            asset=self.asset,
            transaction_type=Transaction.TransactionType.BUY,
            quantity=Decimal('2'),
            price=Decimal('400.00'),
            fee=Decimal('2.00'),
            date=date(2026, 3, 1)
        )

    def test_dashboard_unauthenticated(self):
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 302)

    def test_dashboard_authenticated(self):
        self.client.login(username='investor', password='password123')
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Dashboard')
        self.assertContains(response, 'VOO')

    def test_transaction_list_and_create(self):
        self.client.login(username='investor', password='password123')
        response = self.client.get(reverse('transaction_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Your Transactions')

        create_response = self.client.post(reverse('transaction_list'), {
            'asset': self.asset.id,
            'transaction_type': 'SELL',
            'quantity': '1',
            'price': '420.00',
            'fee': '1.50',
            'date': '2026-04-01'
        })
        self.assertEqual(create_response.status_code, 302)
        self.assertEqual(Transaction.objects.filter(user=self.user).count(), 2)

    def test_transaction_edit(self):
        self.client.login(username='investor', password='password123')
        response = self.client.get(reverse('transaction_edit', kwargs={'pk': self.tx.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Edit Transaction')

        update_response = self.client.post(reverse('transaction_edit', kwargs={'pk': self.tx.pk}), {
            'asset': self.asset.id,
            'transaction_type': 'BUY',
            'quantity': '3',
            'price': '400.00',
            'fee': '2.00',
            'date': '2026-03-01'
        })
        self.assertEqual(update_response.status_code, 302)
        self.tx.refresh_from_db()
        self.assertEqual(self.tx.quantity, Decimal('3.0000'))

    def test_transaction_delete(self):
        self.client.login(username='investor', password='password123')
        response = self.client.post(reverse('transaction_delete', kwargs={'pk': self.tx.pk}))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Transaction.objects.filter(pk=self.tx.pk).exists())

    def test_asset_list_and_create(self):
        self.client.login(username='investor', password='password123')
        response = self.client.get(reverse('asset_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Available Assets')

        create_response = self.client.post(reverse('asset_list'), {
            'ticker': 'GOOGL',
            'name': 'Alphabet Inc.',
            'currency': 'USD'
        })
        self.assertEqual(create_response.status_code, 302)
        self.assertTrue(Asset.objects.filter(ticker='GOOGL').exists())

    def test_asset_delete_protected_with_transactions(self):
        self.client.login(username='investor', password='password123')
        # self.asset has self.tx attached
        response = self.client.post(reverse('asset_delete', kwargs={'pk': self.asset.pk}))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Asset.objects.filter(pk=self.asset.pk).exists())

    def test_asset_delete_without_transactions(self):
        unused_asset = Asset.objects.create(ticker='TSLA', name='Tesla Inc.', currency='USD')
        self.client.login(username='investor', password='password123')
        response = self.client.post(reverse('asset_delete', kwargs={'pk': unused_asset.pk}))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Asset.objects.filter(pk=unused_asset.pk).exists())

