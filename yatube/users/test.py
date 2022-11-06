from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm
from django.test import Client, TestCase
from django.urls import reverse

from .forms import CreationForm

User = get_user_model()


class CreationFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.form = CreationForm()

    def setUp(self):
        self.guest_client = Client()

    def test_create_user(self):
        """Проверьте, что при заполнении формы reverse('users:signup')
        создаётся новый пользователь."""
        response = self.guest_client.get(reverse('users:login'))
        self.assertIsInstance(response.context['form'], AuthenticationForm)
        user_count = User.objects.count()
        form_data = {
            'first_name': 'User',
            'last_name': 'User',
            'username': 'user',
            'email': 'user@gmail.com',
            'password1': '198019801980Iv',
            'password2': '198019801980Iv',
        }
        # Отправляем POST-запрос
        response = self.guest_client.post(
            reverse('users:signup'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse('posts:index'))
        self.assertEqual(User.objects.count(), user_count + 1)
        user = User.objects.last()
        self.assertEqual(user.first_name, form_data['first_name'])
        self.assertEqual(user.last_name, form_data['last_name'])
        self.assertEqual(user.username, form_data['username'])
        self.assertEqual(user.email, form_data['email'])
