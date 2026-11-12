import json

from django.contrib.auth import get_user_model
from django.test import TestCase


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


class ProductApiPermissionTests(TestCase):
    def setUp(self):
        from .models import Category, Product

        self.category = Category.objects.create(name='Books', slug='books')
        self.product = Product.objects.create(
            category=self.category,
            name='Test book',
            slug='test-book',
            price='10.00',
            stock=3,
        )

    def test_anonymous_user_can_read_products(self):
        response = self.client.get('/api/products/')
        self.assertEqual(response.status_code, 200)

    def test_anonymous_user_cannot_create_products(self):
        response = self.client.post('/api/products/', {
            'category': self.category.pk,
            'name': 'Another book',
            'slug': 'another-book',
            'price': '12.00',
            'stock': 2,
        })
        self.assertEqual(response.status_code, 403)

    def test_staff_user_can_create_products(self):
        staff = get_user_model().objects.create_user(
            username='store_admin', password='SafePassword928!', is_staff=True,
        )
        self.client.force_login(staff)
        response = self.client.post('/api/products/', {
            'category': self.category.pk,
            'name': 'Another book',
            'slug': 'another-book',
            'price': '12.00',
            'stock': 2,
        })
        self.assertEqual(response.status_code, 201)
