from datetime import datetime
import copy
from django import forms
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from posts.models import Group, Post, Follow
from django.core.cache import cache
User = get_user_model()


class PagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Test_Author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.group_second = Group.objects.create(
            title='Тестовая группа',
            slug='tests_lug_second',
            description='Тестовое описание второй группы',
        )

        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""

        page_name_template = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:group_list', kwargs={'slug': 'test_slug'}
            ): 'posts/group_list.html',
            reverse(
                'posts:profile', kwargs={'username': 'Test_Author'}
            ): 'posts/profile.html',
            reverse(
                'posts:post_detail', kwargs={'post_id': self.post.pk}
            ): 'posts/post_detail.html',
            reverse(
                'posts:edit', kwargs={'post_id': self.post.pk}
            ): 'posts/create_post.html',
            reverse('posts:create'): 'posts/create_post.html',
        }

        for reverse_name, template in page_name_template.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_cache_index_page(self):
        """Проверка работы кеша"""
        self.authorized_client.get(reverse('posts:index'))
        post_to_delete = Post.objects.first()
        post_to_find = copy.deepcopy(post_to_delete)
        post_to_delete.delete()
        response_1 = self.authorized_client.get(reverse('posts:index'))
        self.assertContains(response_1, post_to_find.text)

    def test_cache_page(self):
        """Проверка кеширования данных."""
        post = Post.objects.create(
            text='Тестовая запись',
            author=self.user)
        content_one = self.authorized_client.get(
            reverse('posts:index')).content
        post.delete()
        content_two = self.authorized_client.get(
            reverse('posts:index')).content
        self.assertEqual(content_one, content_two)
        cache.clear()
        content_three = self.authorized_client.get(
            reverse('posts:index')).content
        self.assertNotEqual(content_one, content_three)


class TaskPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = User.objects.create_user(username='Test_Author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='tests_lug',
            description='Тестовое описание',
        )
        cls.posts = Post.objects.create(
            author=cls.user,
            text='Тестовый текст',
            group=cls.group,
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(TaskPagesTests.user)
        self.username = TaskPagesTests.user.username

        self.link_list = (
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': self.group.slug}),
            reverse('posts:profile', kwargs={'username': self.user.username}),
        )

    def test_post_list_page_show_correct_context(self):
        """Шаблон сформирован с правильным контекстом."""
        for reverse_name in self.link_list:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)

                first_object = response.context['page_obj'][0]
                post_author_0 = first_object.author.username
                post_text_0 = first_object.text
                post_group_0 = first_object.group.title
                post_date_0 = first_object.pub_date
                self.assertEqual(post_author_0, self.username)
                self.assertEqual(post_text_0, self.posts.text)
                self.assertEqual(post_group_0, self.posts.group.title)
                self.assertIsInstance(post_date_0, datetime)


class ContextPaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = User.objects.create_user(username='Test_Author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='tests_lug',
            description='Тестовое описание',
        )
        cls.group2 = Group.objects.create(
            title='Тестовая группа',
            slug='tests_lug_second',
            description='Тестовое описание второй группы',
        )
        cls.posts = []
        for i in range(13):
            cls.posts.append(
                Post.objects.create(
                    author=cls.user,
                    text='Тестовый текст',
                    group=cls.group,
                )
            )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(ContextPaginatorViewsTest.user)
        self.username = ContextPaginatorViewsTest.user.username

        self.paginator_link_list = (
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': self.group.slug}),
            reverse('posts:profile', kwargs={'username': self.user.username}),
        )

    def test_first_page_contains_ten_records(self):
        """Проверка первой страницы."""
        for reverse_name in self.paginator_link_list:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertEqual(len(response.context['page_obj']), 10)

    def test_second_page_contains_three_records(self):
        """Проверка вторай страницы."""
        for reverse_name in self.paginator_link_list:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name + '?page=2')
                self.assertEqual(len(response.context['page_obj']), 3)

    def test_post_form_correct_context(self):
        """Проверка корректности ожидаемого контекста форм"""
        post_id = ContextPaginatorViewsTest.posts[0].pk
        pages_to_test = [
            reverse('posts:edit', kwargs={'post_id': post_id}),
            reverse('posts:create'),
        ]
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }

        for reverse_name in pages_to_test:
            for value, expected in form_fields.items():
                with self.subTest(reverse_name=reverse_name, value=value):
                    response = self.authorized_client.get(reverse_name)
                    form_field = response.context.get('form').fields.get(value)
                    self.assertIsInstance(form_field, expected)


class FollowViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.post_autor = User.objects.create(username='Test_Author')
        cls.post_follower = User.objects.create(username='Test_Follower')
        cls.post = Post.objects.create(
            text='Подписки',
            author=cls.post_autor,
        )

    def setUp(self):
        self.author_client = Client()
        self.author_client.force_login(self.post_follower)
        self.follower_client = Client()
        self.follower_client.force_login(self.post_autor)

    def test_follow_on_user(self):
        count = Follow.objects.count()
        self.follower_client.post(
            reverse(
                'posts:profile_follow',
                kwargs={'username': self.post_follower}))
        follow = Follow.objects.all().latest('id')
        self.assertEqual(Follow.objects.count(), count + 1)
        self.assertEqual(follow.author_id, self.post_follower.id)
        self.assertEqual(follow.user_id, self.post_autor.id)

    def test_unfollow_on_user(self):
        Follow.objects.create(
            user=self.post_autor,
            author=self.post_follower)
        count = Follow.objects.count()
        self.follower_client.post(
            reverse(
                'posts:profile_unfollow',
                kwargs={'username': self.post_follower}))
        self.assertEqual(Follow.objects.count(), count - 1)

    def test_follow_on_authors(self):
        post = Post.objects.create(
            author=self.post_autor,
            text='Подписки')
        Follow.objects.create(
            user=self.post_follower,
            author=self.post_autor)
        response = self.author_client.get(
            reverse('posts:follow_index'))
        self.assertIn(post, response.context['page_obj'].object_list)
