from decimal import Decimal
from datetime import date
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User

from core.models import Asset, Transaction, EXCHANGE_RATES_TO_PLN
from core.forms import TransactionForm, AssetForm


class ModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password123')
        self.asset_usd = Asset.objects.create(ticker='AAPL', name='Apple Inc.', currency='USD')
        self.asset_eur = Asset.objects.create(ticker='SAP', name='SAP SE', currency='EUR')
        self.asset_gbp = Asset.objects.create(ticker='AZN', name='AstraZeneca', currency='GBP')
        self.asset_pln = Asset.objects.create(ticker='CDR', name='CD Projekt', currency='PLN')
        self.asset_other = Asset.objects.create(ticker='CHF_ASSET', name='Swiss Asset', currency='CHF')

    def test_exchange_rates_to_pln(self):
        self.assertEqual(EXCHANGE_RATES_TO_PLN['PLN'], Decimal('1.0'))
        self.assertEqual(EXCHANGE_RATES_TO_PLN['USD'], Decimal('4.0'))
        self.assertEqual(EXCHANGE_RATES_TO_PLN['EUR'], Decimal('4.3'))
        self.assertEqual(EXCHANGE_RATES_TO_PLN['GBP'], Decimal('5.1'))

    def test_asset_exchange_rate_property(self):
        self.assertEqual(self.asset_usd.exchange_rate_to_pln, Decimal('4.0'))
        self.assertEqual(self.asset_eur.exchange_rate_to_pln, Decimal('4.3'))
        self.assertEqual(self.asset_gbp.exchange_rate_to_pln, Decimal('5.1'))
        self.assertEqual(self.asset_pln.exchange_rate_to_pln, Decimal('1.0'))
        self.assertEqual(self.asset_other.exchange_rate_to_pln, Decimal('1.0'))

    def test_asset_str(self):
        self.assertEqual(str(self.asset_usd), 'AAPL (USD)')

    def test_transaction_cost_and_fx_properties(self):
        tx = Transaction.objects.create(
            user=self.user,
            asset=self.asset_usd,
            transaction_type=Transaction.TransactionType.BUY,
            quantity=Decimal('10.0000'),
            price=Decimal('150.0000'),
            fee=Decimal('5.00'),
            date=date(2026, 1, 15)
        )
        self.assertEqual(tx.net_value, Decimal('1500.0000'))
        self.assertEqual(tx.net_value_pln, Decimal('6000.0000'))
        self.assertEqual(tx.total_cost, Decimal('1505.0000'))
        self.assertEqual(tx.total_cost_pln, Decimal('6020.0000'))
        self.assertEqual(str(tx), 'Buy 10.0000 AAPL @ 150.0000')


class QuerySetPortfolioSummaryTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='investor', password='password123')
        self.asset_usd = Asset.objects.create(ticker='AAPL', name='Apple Inc.', currency='USD')
        self.asset_pln = Asset.objects.create(ticker='PKO', name='PKO BP', currency='PLN')

    def test_empty_portfolio(self):
        summary = Transaction.objects.filter(user=self.user).portfolio_summary()
        self.assertEqual(summary['total_transactions'], 0)
        self.assertEqual(summary['active_assets_count'], 0)
        self.assertEqual(summary['total_invested'], Decimal('0.00'))
        self.assertEqual(summary['realized_pnl'], Decimal('0.00'))
        self.assertEqual(len(summary['portfolio']), 0)

    def test_portfolio_summary_buy_and_sell_with_fx(self):
        Transaction.objects.create(
            user=self.user,
            asset=self.asset_usd,
            transaction_type=Transaction.TransactionType.BUY,
            quantity=Decimal('10'),
            price=Decimal('150'),
            fee=Decimal('5'),
            date=date(2026, 1, 1)
        )

        Transaction.objects.create(
            user=self.user,
            asset=self.asset_usd,
            transaction_type=Transaction.TransactionType.SELL,
            quantity=Decimal('5'),
            price=Decimal('200'),
            fee=Decimal('2'),
            date=date(2026, 2, 1)
        )

        Transaction.objects.create(
            user=self.user,
            asset=self.asset_pln,
            transaction_type=Transaction.TransactionType.BUY,
            quantity=Decimal('100'),
            price=Decimal('50'),
            fee=Decimal('10'),
            date=date(2026, 3, 1)
        )

        summary = Transaction.objects.filter(user=self.user).portfolio_summary()

        self.assertEqual(summary['total_transactions'], 3)
        self.assertEqual(summary['active_assets_count'], 2)
        self.assertEqual(summary['realized_pnl'], Decimal('982.00'))
        self.assertEqual(summary['total_invested'], Decimal('8020.00'))

        holdings = {item['ticker']: item for item in summary['portfolio']}
        self.assertIn('AAPL', holdings)
        self.assertEqual(holdings['AAPL']['quantity'], Decimal('5'))
        self.assertEqual(holdings['AAPL']['total_cost'], Decimal('752.50'))
        self.assertEqual(holdings['AAPL']['avg_buy_price'], Decimal('150.50'))

        self.assertIn('PKO', holdings)
        self.assertEqual(holdings['PKO']['quantity'], Decimal('100'))
        self.assertEqual(holdings['PKO']['total_cost'], Decimal('5010.00'))


class FormTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password123')
        self.asset = Asset.objects.create(ticker='MSFT', name='Microsoft', currency='USD')

    def test_asset_form_clean_ticker_and_currency(self):
        form = AssetForm(data={'ticker': '  nvda  ', 'name': 'NVIDIA Corp', 'currency': '  usd  '})
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
        self.other_user = User.objects.create_user(username='other_user', password='password123')
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
        self.assertIn('total_invested', response.context)
        self.assertIn('realized_pnl', response.context)
        self.assertIn('portfolio', response.context)
        self.assertIn('recent_transactions', response.context)

    def test_register_view_get(self):
        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Create an Account')

    def test_register_view_authenticated_redirect(self):
        self.client.login(username='investor', password='password123')
        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('dashboard'))

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

    def test_transaction_user_isolation(self):
        other_tx = Transaction.objects.create(
            user=self.other_user,
            asset=self.asset,
            transaction_type=Transaction.TransactionType.BUY,
            quantity=Decimal('50'),
            price=Decimal('999.00'),
            fee=Decimal('0.00'),
            date=date(2026, 3, 1)
        )
        self.client.login(username='investor', password='password123')

        response = self.client.get(reverse('transaction_list'))
        self.assertNotContains(response, '999.00')

        edit_response = self.client.get(reverse('transaction_edit', kwargs={'pk': other_tx.pk}))
        self.assertEqual(edit_response.status_code, 404)

        del_response = self.client.post(reverse('transaction_delete', kwargs={'pk': other_tx.pk}))
        self.assertEqual(del_response.status_code, 404)

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
        response = self.client.post(reverse('asset_delete', kwargs={'pk': self.asset.pk}))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Asset.objects.filter(pk=self.asset.pk).exists())

    def test_asset_delete_without_transactions(self):
        unused_asset = Asset.objects.create(ticker='TSLA', name='Tesla Inc.', currency='USD')
        self.client.login(username='investor', password='password123')
        response = self.client.post(reverse('asset_delete', kwargs={'pk': unused_asset.pk}))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Asset.objects.filter(pk=unused_asset.pk).exists())