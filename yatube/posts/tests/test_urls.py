from http import HTTPStatus
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.core.cache import cache
from ..models import Post, Group


User = get_user_model()
COUNT = 5


class StaticURLTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_homepage(self):
        response = self.guest_client.get('/')
        self.assertEqual(response.status_code, 200)


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        user = User.objects.create(username='author')
        Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание ' * COUNT,
        )
        cls.post = Post.objects.create(
            text='Тестовый текст ' * COUNT,
            author=user,
            group=Group.objects.get(slug='test_slug')
        )

    def setUp(self):
        cache.clear()
        self.guest_client = Client()
        self.author = User.objects.get(username='author')
        self.authorized_author_client = Client()
        self.authorized_author_client.force_login(self.author)
        self.user = User.objects.create(username='TestUser')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

        access = {
            0: 'All',
            1: 'Authorizated',
            2: 'Author',
        }

        self.urls_templates = {
            '/': {
                'access': access[0],
                'template': 'posts/index.html',
            },
            f'/group/{self.post.group.slug}/': {
                'access': access[0],
                'template': 'posts/group_list.html',
            },
            f'/profile/{self.user.username}/': {
                'access': access[0],
                'template': 'posts/profile.html',
            },
            f'/posts/{self.post.id}/': {
                'access': access[0],
                'template': 'posts/post_detail.html',
            },
            f'/posts/{self.post.id}/edit/': {
                'access': access[2],
                'template': 'posts/create_post.html',
            },
            '/create/': {
                'access': access[1],
                'template': 'posts/create_post.html',
            },
        }

    def test_guest_url_exists_at_desired_location(self):
        """Проверка страниц доступных любому пользователю."""
        for url, data in self.urls_templates.items():
            if data['access'] == 'All':
                with self.subTest(url=url):
                    response = self.guest_client.get(url)
                    self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        for url, data in self.urls_templates.items():
            with self.subTest(url=url):
                response = self.authorized_author_client.get(url)
                self.assertTemplateUsed(response, data['template'])

    def test_url_404(self):
        """Проверка несуществующей страницы."""
        url = '/asdaf/'
        response = self.guest_client.get(url)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_authorized_url_exists_at_desired_location(self):
        """Проверка страниц доступных авторизированному пользователю."""
        for url, data in self.urls_templates.items():
            if data['access'] == 'Authorizated':
                with self.subTest(url=url):
                    response = self.authorized_client.get(url)
                    self.assertEqual(response.status_code, HTTPStatus.OK)
                    response = self.guest_client.get(url, follow=True)
                    self.assertRedirects(response,
                                         '/auth/login/?next=/create/')

    def test_author_url_exists_at_desired_location(self):
        """Проверка страниц доступных автору."""
        for url, data in self.urls_templates.items():
            if data['access'] == 'Author':
                with self.subTest(url=url):
                    response = self.authorized_author_client.get(url)
                    self.assertEqual(response.status_code, HTTPStatus.OK)
                    response = self.authorized_client.get(url, follow=True)
                    self.assertRedirects(response,
                                         f'/posts/{self.post.id}/')
