import json
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from .models import Category, Order, OrderItem, Product, Review


class AuthenticationFlowTests(TestCase):
    registration_data = {
        'username': 'new_customer',
        'first_name': 'New',
        'last_name': 'Customer',
        'email': 'new.customer@example.com',
        'password1': 'SafePassword928!',
        'password2': 'SafePassword928!',
    }

    def test_registration_hashes_password_and_starts_session(self):
        response = self.client.post('/register/', self.registration_data)

        self.assertRedirects(response, '/base/profile/')
        user = get_user_model().objects.get(username='new_customer')
        self.assertTrue(user.check_password(self.registration_data['password1']))
        self.assertNotEqual(user.password, self.registration_data['password1'])
        self.assertEqual(
            self.client.session['_auth_user_id'],
            str(user.pk),
        )

    def test_invalid_registration_returns_field_errors_without_creating_user(self):
        data = {
            **self.registration_data,
            'email': 'not-an-email',
            'password2': 'different-password',
        }

        response = self.client.post('/register/', data)

        self.assertEqual(response.status_code, 200)
        self.assertIn('email', response.context['form'].errors)
        self.assertEqual(get_user_model().objects.count(), 0)

    def test_sign_in_authenticates_and_rejects_external_next_url(self):
        user = get_user_model().objects.create_user(
            username='existing_customer',
            email='existing.customer@example.com',
            password='SafePassword928!',
        )

        response = self.client.post(
            '/sign_in/',
            {
                'username': user.username,
                'password': 'SafePassword928!',
                'next': 'https://attacker.example/',
            },
        )

        self.assertRedirects(response, '/base/profile/')
        self.assertEqual(self.client.session['_auth_user_id'], str(user.pk))

    def test_json_registration_returns_validation_errors_for_non_object_body(self):
        response = self.client.post(
            '/api/register/',
            data='[]',
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['detail'], 'The JSON payload must be an object.')

    def test_json_registration_creates_user_and_issues_session(self):
        response = self.client.post(
            '/api/register/',
            data=json.dumps(self.registration_data),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 201)
        user = get_user_model().objects.get(username='new_customer')
        self.assertTrue(user.check_password(self.registration_data['password1']))
        self.assertEqual(self.client.session['_auth_user_id'], str(user.pk))

    def test_invalid_sign_in_keeps_user_anonymous_and_shows_error(self):
        get_user_model().objects.create_user(
            username='existing_customer',
            email='existing.customer@example.com',
            password='SafePassword928!',
        )

        response = self.client.post(
            '/sign_in/',
            {'username': 'existing_customer', 'password': 'wrong-password'},
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['form'].non_field_errors())
        self.assertNotIn('_auth_user_id', self.client.session)


class StoreSecurityAndOrderTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name='Books', slug='books')
        self.product = Product.objects.create(
            category=self.category, name='Django', slug='django', price=Decimal('20.00'), stock=3,
        )

    def test_anonymous_api_user_cannot_create_product(self):
        response = self.client.post('/api/products/', {
            'category': self.category.pk, 'name': 'Injected', 'slug': 'injected', 'price': '1.00',
        })
        self.assertEqual(response.status_code, 403)
        self.assertFalse(Product.objects.filter(slug='injected').exists())

    def test_public_product_api_is_readable(self):
        response = self.client.get('/api/products/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['results'][0]['slug'], 'django')

    def test_storefront_templates_render(self):
        catalog = self.client.get('/')
        detail = self.client.get('/product/django/')
        checkout = self.client.get('/order/create/django/')
        self.assertEqual(catalog.status_code, 200)
        self.assertEqual(detail.status_code, 200)
        self.assertEqual(checkout.status_code, 200)

    def test_catalog_search_price_sort_and_pagination(self):
        cheap = Product.objects.create(
            category=self.category, name='Cheap item', slug='cheap-item', price=5, stock=2,
        )
        digital = Product.objects.create(
            category=self.category, name='Digital item', slug='digital-item', price=30,
            pdf_price=4, stock=0, file='products/files/sample.pdf',
        )
        expensive = Product.objects.create(
            category=self.category, name='Expensive item', slug='expensive-item', price=50, stock=2,
        )

        response = self.client.get('/', {'q': 'digital'})
        self.assertEqual(list(response.context['products']), [digital])

        response = self.client.get('/', {'sort': 'price_asc'})
        self.assertEqual(response.context['products'][0], digital)
        self.assertEqual(response.context['products'][1], cheap)
        self.assertEqual(response.context['products'][2], self.product)
        self.assertEqual(response.context['products'][3], expensive)

        for index in range(10):
            Product.objects.create(
                category=self.category,
                name=f'Extra item {index}',
                slug=f'extra-item-{index}',
                price=10 + index,
                stock=1,
            )
        response = self.client.get('/', {'q': 'item', 'sort': 'price_asc', 'page': 2})
        self.assertEqual(response.context['page_obj'].number, 2)
        self.assertContains(response, 'q=item&amp;sort=price_asc&amp;page=1')

    def test_catalog_uses_database_products_and_links_to_detail_and_order(self):
        response = self.client.get('/', {'q': 'Django'})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'href="/product/django/"')
        self.assertContains(response, 'href="/order/create/django/"')
        self.assertContains(response, 'name="q"')
        self.assertContains(response, 'name="sort"')
        self.assertContains(response, 'product-availability--in')
        self.assertNotContains(response, 'Cloud Ceramic Vase')
        self.assertNotContains(response, 'Shopping bag')

        category_response = self.client.get('/category/books/', {'q': 'Django', 'sort': 'price_asc'})
        self.assertEqual(category_response.status_code, 200)
        self.assertContains(category_response, 'href="/category/books/?q=Django&amp;sort=price_asc"')

    def test_catalog_empty_state_keeps_search_and_category_filters_usable(self):
        response = self.client.get('/', {'q': 'not-a-real-product'})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'empty-state')
        self.assertContains(response, 'Очистить поиск')
        self.assertContains(response, 'value="not-a-real-product"')

    def test_legacy_home_route_leads_to_catalog(self):
        response = self.client.get('/base/')
        self.assertRedirects(response, '/')

    def test_language_switching_uses_django_catalogs_and_persists(self):
        translated_catalog_headings = {
            'ru': 'Все товары',
            'en': 'All products',
            'ja': 'すべての商品',
            'uz': 'Barcha mahsulotlar',
        }
        translated_filter_buttons = {
            'ru': 'Применить',
            'en': 'Apply filters',
            'ja': '適用',
            'uz': 'Qo‘llash',
        }
        translated_password_error = {
            'ru': 'Пароль должен содержать хотя бы одну заглавную букву.',
            'en': 'Password must include at least one uppercase letter.',
            'ja': 'パスワードには大文字を1文字以上含めてください。',
            'uz': 'Parolda kamida bitta bosh harf bo‘lishi kerak.',
        }
        user = get_user_model().objects.create_user(username='language_user', password='pass')
        public_pages = (
            '/', '/product/django/', '/order/create/django/',
            '/sign_in/', '/register/',
        )
        for language, heading in translated_catalog_headings.items():
            self.client.logout()
            switch_response = self.client.post(
                '/i18n/setlang/',
                {'language': language, 'next': '/'},
            )
            self.assertEqual(switch_response.status_code, 302)
            invalid_registration = self.client.post('/register/', {
                'username': f'new_{language}', 'email': f'{language}@example.com',
                'password1': 'badpassword', 'password2': 'badpassword',
            })
            self.assertEqual(invalid_registration.status_code, 200)
            self.assertContains(invalid_registration, translated_password_error[language])
            for page in public_pages:
                response = self.client.get(page)
                self.assertEqual(response.status_code, 200, f'{language} page failed: {page}')
                self.assertContains(response, f'<html lang="{language}">', html=False)
                if page == '/':
                    self.assertContains(response, heading)
                    self.assertContains(response, translated_filter_buttons[language])
            self.client.force_login(user)
            for page in ('/profile/', '/profile/edit/'):
                response = self.client.get(page)
                self.assertEqual(response.status_code, 200, f'{language} page failed: {page}')
                self.assertContains(response, f'<html lang="{language}">', html=False)

    def test_order_uses_server_price_and_reduces_stock(self):
        response = self.client.post('/order/create/django/', {
            'first_name': 'A', 'last_name': 'B', 'email': 'a@example.com',
            'address': 'Address', 'quantity': 2,
        })
        order = Order.objects.get()
        self.assertRedirects(response, f'/base/order/created/{order.pk}/')
        self.assertEqual(order.total_price, Decimal('40.00'))
        self.assertEqual(order.items.get().price, Decimal('20.00'))
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 1)

    def test_order_rejects_quantity_above_stock(self):
        response = self.client.post('/order/create/django/', {
            'first_name': 'A', 'last_name': 'B', 'email': 'a@example.com',
            'address': 'Address', 'quantity': 4,
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Order.objects.exists())
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 3)

    def test_order_confirmation_is_private(self):
        user1 = get_user_model().objects.create_user(username='one', password='pass')
        user2 = get_user_model().objects.create_user(username='two', password='pass')
        order = Order.objects.create(user=user1, first_name='A', last_name='B', email='a@example.com', address='X')
        self.client.force_login(user2)
        self.assertEqual(self.client.get(f'/order/created/{order.pk}/').status_code, 404)

    def test_pdf_download_requires_paid_order(self):
        pdf = Product.objects.create(
            category=self.category, name='PDF book', slug='pdf-book', price=10, pdf_price=5,
            stock=0, file=SimpleUploadedFile('book.pdf', b'%PDF-1.4 test', content_type='application/pdf'),
        )
        user = get_user_model().objects.create_user(username='buyer', password='pass')
        self.client.force_login(user)
        url = f'/product/{pdf.pk}/download/'
        self.assertEqual(self.client.get(url).status_code, 404)
        order = Order.objects.create(
            user=user, first_name='A', last_name='B', email='a@example.com', address='X',
            status=Order.StatusChoices.PAID,
        )
        OrderItem.objects.create(order=order, product=pdf, price=5, quantity=1)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response['Content-Disposition'].startswith('attachment;'))

    def test_duplicate_review_is_rejected(self):
        user = get_user_model().objects.create_user(username='reviewer', password='pass')
        Review.objects.create(user=user, product=self.product, rating=5, text='First')
        self.client.force_login(user)
        response = self.client.post('/product/django/', {'rating': 4, 'text': 'Second'})
        self.assertEqual(Review.objects.filter(user=user, product=self.product).count(), 1)
        self.assertEqual(response.status_code, 200)

    def test_account_templates_render(self):
        user = get_user_model().objects.create_user(username='profile_user', password='pass')
        self.client.force_login(user)
        self.assertEqual(self.client.get('/profile/').status_code, 200)
        self.assertEqual(self.client.get('/profile/edit/').status_code, 200)
