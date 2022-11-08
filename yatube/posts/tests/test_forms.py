import shutil
import tempfile
from django.core.cache import cache
from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from posts.models import Group, Post, Comment
from http import HTTPStatus
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings


User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Test_Author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='tests_lug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовая запись',
            group=cls.group,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_authorized_user_create_post(self):
        """Проверка создания записи авторизированным клиентом."""
        posts_count = Post.objects.count()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Тестовый текст',
            'group': self.group.id,
            'image': uploaded,
        }
        # Отправляем POST-запрос
        response = self.authorized_client.post(
            reverse('posts:create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            reverse(
                'posts:profile',
                kwargs={'username': self.user.username})
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        post = Post.objects.latest('id')
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.author, self.user)
        self.assertEqual(post.group_id, form_data['group'])
        self.assertEqual(post.image, 'posts/small.gif')

    def test_edit_post(self):
        """Проверка редактирования записи авторизированным клиентом."""

        post_count = Post.objects.count()
        form_data = {
            'text': 'Тестовая часть текста.',
            'group': self.group.pk,
        }
        response = self.authorized_client.post(
            reverse('posts:edit', kwargs={'post_id': str(self.post.pk)}),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(
            response,
            reverse(
                'posts:post_detail', kwargs={'post_id': str(self.post.pk)}
            ),
        )
        self.assertEqual(Post.objects.count(), post_count)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        post = Post.objects.first()
        self.assertEqual(post.author, self.user)
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.group_id, form_data['group'])

    def test_guest_create_post(self):
        """Проверка создания поста неавторизованным пользователем."""
        post_count = Post.objects.count()

        form_data = {'text': 'Тестовый текст', 'group': self.group.pk}

        response = self.guest_client.post(
            reverse('posts:create'), data=form_data, follow=True
        )
        # Проверяем, сработал ли редирект
        self.assertRedirects(
            response,
            reverse('users:login') + '?next=' + reverse('posts:create'),
        )
        self.assertEqual(Post.objects.count(), post_count)
        self.assertEqual(response.status_code, HTTPStatus.OK)

@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Test_Author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='tests_lug',
            description='Тестовое описание',
            )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовая запись',
            group=cls.group,
            )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_authorized_user_create_comment(self):
        """Проверка создания коментария авторизированным клиентом."""
        comments_count = Comment.objects.count()

        form_data = {'text': 'Тестовый коментарий'}

        response = self.authorized_client.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': str(self.post.pk)}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response, reverse('posts:post_detail', args={self.post.pk}))
        self.assertEqual(Comment.objects.count(), comments_count + 1)
        comment = Comment.objects.latest('id')
        self.assertEqual(comment.text, form_data['text'])
        self.assertEqual(comment.author, self.user)
        self.assertEqual(comment.post_id, self.post.pk)

    def test_user_create_comment(self):
        """Проверка создания коментария не авторизированным клиентом."""
        comments_count = Comment.objects.count()

        form_data = {'text': 'Тестовый коментарий'}

        response = self.guest_client.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': str(self.post.pk)}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            reverse('login') + '?next=' + reverse(
                'posts:add_comment', kwargs={'post_id': self.post.pk}),
        )
        self.assertEqual(Comment.objects.count(), comments_count)
        self.assertEqual(response.status_code, HTTPStatus.OK)
