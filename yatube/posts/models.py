from django.contrib.auth import get_user_model
from django.db import models
from core.models import CreatedModel

User = get_user_model()


class Group(models.Model):
    title = models.CharField(
        max_length=200,
        verbose_name='Название'
    )
    slug = models.SlugField(
        unique=True,
        max_length=50,
        verbose_name='Ссылка на группу'
    )
    description = models.TextField(
        verbose_name='Описание'
    )

    class Meta:
        verbose_name_plural = 'Группы'
        verbose_name = 'Группу'

    def __str__(self):
        return self.title


class Post(models.Model):
    text = models.TextField(
        verbose_name='Текст записи',
        help_text='Введите текст поста'
    )
    pub_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата публикации'
    )
    author = models.ForeignKey(
        User,
        verbose_name='Автор публикации',
        on_delete=models.CASCADE,
        related_name='posts',
    )
    group = models.ForeignKey(
        Group,
        verbose_name='Группа',
        blank=True,
        null=True,
        related_name='posts',
        on_delete=models.SET_NULL,
        help_text='Группа, к которой будет относиться пост',
    )
    image = models.ImageField(
        'Картинка',
        upload_to='posts/',
        blank=True,
        null=True,
    )

    class Meta:
        ordering = ["-pub_date"]
        verbose_name_plural = 'Посты'
        verbose_name = 'Пост'

    def __str__(self):
        return self.text[:15]


class Comment(CreatedModel):
    post = models.ForeignKey(
        Post,
        verbose_name='Комментарий',
        on_delete=models.CASCADE,
        related_name='comments',
    )
    author = models.ForeignKey(
        User,
        verbose_name='Автор комментария',
        on_delete=models.CASCADE,
        related_name='comments',
    )
    text = models.TextField(
        verbose_name='Текст комментария',
    )

    class Meta:
        ordering = ['-created']
        verbose_name_plural = 'Комментарий'
        verbose_name = 'Комментарий'

    def __str__(self):
        return self.text[:15]


class Follow(CreatedModel):
    user = models.ForeignKey(
        User,
        verbose_name='Подписчик',
        on_delete=models.CASCADE,
        related_name='follower',
    )
    author = models.ForeignKey(
        User,
        verbose_name='Автор',
        on_delete=models.CASCADE,
        related_name='following',
    )

    class Meta:
        verbose_name_plural = 'Подписки'
        verbose_name = 'Подписки'
        models.UniqueConstraint(
            fields=['user', 'author'],
            name='unique_follow'
        )

    def __str__(self):
        return f'{self.user} подписан на {self.author}'
