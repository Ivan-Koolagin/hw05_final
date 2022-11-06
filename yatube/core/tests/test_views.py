from http import HTTPStatus
from django.test import Client, TestCase


class ViewTestClass(TestCase):
    def setUp(self):
        self.user = Client()

    def test_error_page(self):
        response = self.user.get('/nonexist-page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertTemplateUsed(response, 'core/404.html')
