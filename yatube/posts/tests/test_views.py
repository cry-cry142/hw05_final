import tempfile
import shutil

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Post, Group, Follow
from posts.forms import PostForm

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(TestCase):
    COUNT_POSTS: int = 10
    COUNT_WORDS_POST: int = 30
    COUNT_CHAR_POST_TITLE: int = 30
    COUNT_CREATE_GROUPS: int = 2
    COUNT_CREATE_POSTS_IN_GROUP: int = 12

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = []

        for i in range(1, cls.COUNT_CREATE_GROUPS + 1):
            cls.user.insert(i - 1, User.objects.create(username=f'User_{i}'))
            Group.objects.create(
                title=f'Группа {i}',
                slug=f'gr_{i}',
                description='Описание'
            )
        for j in range(cls.COUNT_CREATE_POSTS_IN_GROUP):
            for i in range(1, cls.COUNT_CREATE_GROUPS + 1):
                small_gif = (
                    b'\x47\x49\x46\x38\x39\x61\x02\x00'
                    b'\x01\x00\x80\x00\x00\x00\x00\x00'
                    b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
                    b'\x00\x00\x00\x2C\x00\x00\x00\x00'
                    b'\x02\x00\x01\x00\x00\x02\x02\x0C'
                    b'\x0A\x00\x3B'
                )
                uploaded = SimpleUploadedFile(
                    name=f'small_{j}_{i}.gif',
                    content=small_gif,
                    content_type='image/gif'
                )
                Post.objects.create(
                    text=f'ТекстP{j}G{i}',
                    author=cls.user[i - 1],
                    group=Group.objects.get(id=i),
                    image=uploaded,
                )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        cache.clear()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user[0])

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        post = Post.objects.get(id=1)
        templates_pages_names = [
            (
                'posts/index.html', reverse('posts:main')
            ),
            (
                'posts/group_list.html',
                reverse('posts:group_list', kwargs={'slug': post.group.slug})
            ),
            (
                'posts/profile.html',
                reverse('posts:profile',
                        kwargs={'username': self.user[0].username})
            ),
            (
                'posts/post_detail.html',
                reverse('posts:post_detail', kwargs={'post_id': post.id})
            ),
            (
                'posts/create_post.html',
                reverse('posts:post_edit', kwargs={'post_id': post.id})
            ),
            (
                'posts/create_post.html',
                reverse('posts:post_create')
            ),
        ]

        for template, reverse_name in templates_pages_names:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def compare_fields_posts(self, post_1: Post, post_2: Post):
        """Сравнивает поля двух объектов класса Post."""
        fields = [field.attname for field in post_1._meta.fields]
        for field in fields:
            with self.subTest(field=field):
                self.assertEqual(
                    getattr(post_1, field),
                    getattr(post_2, field)
                )

    def test_main_page_show_correct_context(self):
        """Шаблон main сформирован с правильным контекстом."""
        post = Post.objects.select_related().latest('pub_date')
        response = self.authorized_client.get(reverse('posts:main'))

        title_page = response.context['title']
        first_object_context = response.context['page_obj'][0]

        self.assertEqual(title_page, 'Это главная страница проекта Yatube')
        self.compare_fields_posts(post, first_object_context)
        self.assertEqual(response.context['count_words'],
                         self.COUNT_WORDS_POST)
        self.assertEqual(response.context['page_obj'].object_list[0].image,
                         'posts/small_11_2.gif')

    def test_group_posts_page_show_correct_context(self):
        """Шаблон group_posts сформирован с правильным контекстом."""
        slug_group = 'gr_1'
        response = self.authorized_client.get(reverse(
            'posts:group_list',
            kwargs={'slug': slug_group}
        ))

        title_page = response.context['title']
        group = Group.objects.get(slug=slug_group)
        group_context = response.context['group']
        post = group.posts.first()
        post_context = response.context['page_obj'][0]

        self.assertEqual(title_page,
                         'Здесь будет информация о группах проекта Yatube')
        self.assertEqual(group_context, group)
        self.assertEqual(response.context['count_words'],
                         self.COUNT_WORDS_POST)
        self.compare_fields_posts(post_context, post)
        self.assertEqual(response.context['page_obj'].object_list[0].image,
                         'posts/small_11_1.gif')

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            'posts:profile',
            kwargs={'username': self.user[0].username}
        ))

        post = self.user[0].posts.first()
        post_context = response.context['page_obj'][0]

        self.assertEqual(response.context['author'], self.user[0])
        self.assertEqual(response.context['count_posts'](),
                         self.user[0].posts.all().count())
        self.assertEqual(response.context['count_words'],
                         self.COUNT_WORDS_POST)
        self.compare_fields_posts(post_context, post)
        self.assertEqual(response.context['page_obj'].object_list[0].image,
                         'posts/small_11_1.gif')

    def test_post_detail_page_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        post = Post.objects.last()
        response = self.authorized_client.get(reverse(
            'posts:post_detail',
            kwargs={'post_id': post.id}
        ))

        self.compare_fields_posts(response.context['post'], post)
        self.assertEqual(response.context['count_chars'],
                         self.COUNT_CHAR_POST_TITLE)
        self.assertEqual(response.context['is_read'], True)
        self.assertEqual(response.context['post'].image,
                         'posts/small_0_1.gif')

    def test_create_page_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        self.assertEqual(response.context['title'], 'Создать новый пост')
        self.assertEqual(response.context['button_name'], 'Добавить')
        self.assertIsInstance(response.context['form'], PostForm)

    def test_edit_page_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        post = Post.objects.last()
        response = self.authorized_client.get(reverse(
            'posts:post_edit',
            kwargs={'post_id': post.id}
        ))
        self.assertEqual(response.context['title'], 'Редактировать пост')
        self.assertEqual(response.context['button_name'], 'Сохранить')
        self.assertIsInstance(response.context['form'], PostForm)

    def test_create_post_group_show_correct(self):
        """Проверка на корректное отображение поста с группой."""
        group_1 = Group.objects.get(id=1)
        post = group_1.posts.select_related().first()

        urls_names = [
            reverse('posts:main'),
            reverse('posts:group_list', kwargs={'slug': post.group.slug}),
            reverse('posts:profile', kwargs={'username': post.author})
        ]

        for url in urls_names:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertIn(post,
                              response.context['page_obj'].object_list)

    def test_post_group_not_in_other_groups(self):
        """Проверка на отсутствие поста группы в других группах."""
        group_1 = Group.objects.get(id=1)
        group_2 = Group.objects.get(id=2)
        post = group_1.posts.select_related().first()
        response = self.authorized_client.get(reverse(
            'posts:group_list',
            kwargs={'slug': group_2.slug}
        ))
        self.assertNotIn(post, response.context['page_obj'].object_list)

    def test_paginator(self):
        """Тестирование паджинатора."""
        group = Group.objects.get(id=1)
        url_with_count_posts = [
            (reverse('posts:main'),
             self.COUNT_CREATE_POSTS_IN_GROUP * self.COUNT_CREATE_GROUPS),
            (reverse('posts:group_list',
                     kwargs={'slug': group.slug}),
             self.COUNT_CREATE_POSTS_IN_GROUP),
            (reverse('posts:profile',
                     kwargs={'username': self.user[0].username}),
             self.COUNT_CREATE_POSTS_IN_GROUP),
        ]
        for url, count_posts in url_with_count_posts:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                page_obj = response.context['page_obj']
                count_pages = page_obj.paginator.num_pages
                count_posts_page = 0
                for page in range(1, count_pages + 1):
                    with self.subTest(page=page):
                        response = self.authorized_client.get(url,
                                                              {'page': page})
                        if count_posts > self.COUNT_POSTS:
                            count_posts_page = self.COUNT_POSTS
                        else:
                            count_posts_page = count_posts
                        count_posts -= self.COUNT_POSTS
                        self.assertEqual(len(response.context['page_obj']),
                                         count_posts_page)

    def test_cache_main_page(self):
        """Тестирование кеша главной страницы."""
        guest_client = Client()
        response_before = guest_client.get(reverse('posts:main'))
        Post.objects.first().delete()
        response_after = guest_client.get(reverse('posts:main'))

        self.assertEqual(response_before.content, response_after.content)

        cache.clear()
        response_after = guest_client.get(reverse('posts:main'))

        self.assertNotEqual(response_before.content, response_after.content)

    def test_page_404(self):
        """Тестирование использования кастомного шаблона 404."""
        guest_client = Client()
        response = guest_client.get(reverse('posts:main') + 'qwes/')

        self.assertTemplateUsed(response, 'core/404.html')

    def test_followers(self):
        """Тестирование модуля подписок."""
        user = User.objects.create(username='TUser')
        user_client = Client()
        user_client.force_login(user)
        user_client.post(reverse('posts:profile_follow',
                                 args=(self.user[0].username,)))

        response = user_client.get(reverse('posts:follow_index'))
        posts = response.context['page_obj'].paginator.object_list
        for post in posts:
            with self.subTest(f'У поста {post} автор {post.author}'):
                self.assertEqual(post.author, self.user[0])

        self.assertTrue(
            Follow.objects.filter(author=self.user[0], user=user).exists(),
            'Пользователь не может подписаться.'
        )
        user_client.post(reverse('posts:profile_unfollow',
                                 args=(self.user[0].username,)))
        self.assertFalse(
            Follow.objects.filter(author=self.user[0], user=user).exists(),
            'Пользователь не может отписаться.'
        )
