from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse


class AdminSiteTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.admin_user = get_user_model().objects.create_superuser(
            email='kims_admin@gmail.com',
            password='password123'
        )
        self.client.force_login(self.admin_user)
        self.user = get_user_model().objects.create_user(
            email='test_user@gmail.com',
            password='password123',
            name='Test user'
        )

    def test_users_listed(self):
        # Test that users are listed on user page
        url = reverse('admin:core_user_changelist')
        resp = self.client.get(url)
        self.assertContains(resp, self.user.name)
        self.assertContains(resp, self.user.email)

    def test_user_change_page(self):
        # Test that the user edit page works
        url = reverse('admin:core_user_change', args=[self.user.id])
        resp = self.client.get(url)
        self.assertEquals(resp.status_code, 200)

    def test_create_user_page(self):
        # Test that the create user page works.
        url = reverse('admin:core_user_add')
        resp = self.client.get(url)
        self.assertEquals(resp.status_code, 200)
