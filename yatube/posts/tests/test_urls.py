from http import HTTPStatus
from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from ..models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='user')
        cls.another_user = User.objects.create_user(username='another_user')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='slug_test',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )

    def setUp(self):

        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_urls_guest(self):
        """Страницы доступные любому пользователю."""

        url_names = (
            "/",
            "/group/slug_test/",
            "/profile/user/",
            f"/posts/{self.post.pk}/",
        )
        for address in url_names:
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_autorized(self):
        """Страницы доступные авторизованному пользователю."""

        url_names = (
            "/",
            "/group/slug_test/",
            "/profile/user/",
            f"/posts/{self.post.pk}/",
            f"/posts/{self.post.pk}/edit/",
            "/create/",
        )
        for address in url_names:
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_list_url_redirect_anonymous_on_admin_login(self):
        """Страница по адресу /task/test_slug/, /task/ перенаправит
        анонимного пользователя на страницу логина.
        """

        url_names_redirects = {
            f'/posts/{self.post.pk}/edit/': (
                f'/auth/login/?next=/posts/{self.post.pk}/edit/'
            ),
            '/create/': '/auth/login/?next=/create/',
        }
        for address, redirect_address in url_names_redirects.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address, follow=True)
                self.assertRedirects(response, redirect_address)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            '/': 'posts/index.html',
            '/group/slug_test/': 'posts/group_list.html',
            '/profile/user/': 'posts/profile.html',
            f'/posts/{self.post.pk}/': 'posts/post_detail.html',
            f'/posts/{self.post.pk}/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html',
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_page_not_found(self):
        """Страница не найденна."""
        response = self.guest_client.get("/unexisting_page/")
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
