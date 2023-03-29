from django.db import models
from django.contrib.auth import get_user_model
from django.conf import settings


User = get_user_model()


class Post(models.Model):
    text = models.TextField('Текст поста')
    pub_date = models.DateTimeField('Дата публикации', auto_now_add=True)
    author = models.ForeignKey(
        User,
        verbose_name='Автор',
        on_delete=models.CASCADE,
        related_name='posts',
    )
    group = models.ForeignKey(
        'Group',
        verbose_name='Группа',
        on_delete=models.SET_NULL,
        related_name='posts',
        blank=True,
        null=True,
    )
    image = models.ImageField(
        'Картинка',
        upload_to='posts/',
        blank=True
    )

    class Meta:
        ordering = ['-pub_date']

    def __str__(self):
        return self.text[:settings.COUNT_CHAR_POST_STR]


class Group(models.Model):
    title = models.CharField('Название группы', max_length=200)
    slug = models.SlugField('Путь', unique=True)
    description = models.TextField('Описание группы')

    def __str__(self) -> str:
        return self.title


class Comment(models.Model):
    post = models.ForeignKey(
        Post,
        verbose_name='Пост',
        on_delete=models.CASCADE,
        related_name='comments',
    )
    author = models.ForeignKey(
        User,
        verbose_name='Автор',
        on_delete=models.CASCADE,
        related_name='comments',
    )
    text = models.TextField('Текст комментария')
    created = models.DateTimeField('Дата публикации', auto_now_add=True)


class Follow(models.Model):
    author = models.ForeignKey(
        User,
        verbose_name='Автор',
        on_delete=models.CASCADE,
        related_name='following',
    )
    user = models.ForeignKey(
        User,
        verbose_name='Подписчики',
        on_delete=models.CASCADE,
        related_name='follower',
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['author', 'user'],
                name='unique_author_user_following'
            ),
            models.CheckConstraint(
                check=~models.Q(user=models.F('author')),
                name='author_cannot_subscribe'
            ),
        ]
