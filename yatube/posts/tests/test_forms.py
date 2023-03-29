import tempfile
import shutil
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from posts.forms import PostForm
from posts.models import Post, Group, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.form = PostForm()
        cls.user = User.objects.create(username='user')
        cls.group = Group.objects.create(
            title='Group',
            slug='group',
            description='Тестовая группа',
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.text = 'Тестовый текст.'

    def test_create_post(self):
        """Валидная форма создает запись в Post."""
        posts_count = Post.objects.count()
        last_post_before = Post.objects.select_related('group').first()

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
            'text': self.text,
            'group': self.group.id,
            'image': uploaded,
        }
        self.authorized_client.post(
            reverse('posts:post_create'),
            form_data,
            follow=True,
        )
        last_post_after = Post.objects.first()

        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertNotEqual(last_post_after, last_post_before)
        self.assertEqual(form_data['text'], last_post_after.text)
        self.assertEqual(form_data['group'], last_post_after.group_id)
        self.assertEqual(last_post_after.image, 'posts/small.gif')

    def test_edit_post(self):
        """Валидная форма редакитует запись в Post."""
        post = Post.objects.create(
            text='Ещё - текст.',
            author=self.user,
        )
        form_data = {
            'text': self.text,
            'group': self.group.id,
        }

        self.authorized_client.post(reverse(
            'posts:post_edit',
            args=(post.id,)
        ), form_data, follow=True)
        new_post = Post.objects.get(id=post.id)

        self.assertEqual(form_data['text'], new_post.text)
        self.assertEqual(form_data['group'], new_post.group_id)

    def test_correct_create_comments_post(self):
        """Проверка успешного создания комментирия к посту."""
        post = Post.objects.create(
            text='Тестовый текст поста.',
            author=self.user,
        )
        url_post = reverse('posts:post_detail', kwargs={'post_id': post.id})
        response = self.authorized_client.get(url_post)
        before_last_comment = response.context['comments_list'].last()

        text = 'Тестовый текст.'
        response = self.authorized_client.post(reverse(
            'posts:add_comment',
            kwargs={'post_id': post.id}
        ), {'text': text}, follow=True)

        self.assertRedirects(response, url_post)

        response = self.authorized_client.get(url_post)
        after_last_comment = response.context['comments_list'].last()

        self.assertNotEqual(before_last_comment, after_last_comment)

    def test_guest_client_not_create_comments_post(self):
        """Неавторизованный пользователь не создаст комментарий."""
        post = Post.objects.create(
            text='Тестовый текст поста.',
            author=self.user,
        )
        count_comments_before = post.comments.count()
        guest_client = Client()

        text = 'Тестовый текст.'
        guest_client.post(reverse(
            'posts:add_comment',
            kwargs={'post_id': post.id}
        ), {'text': text}, follow=True)

        count_comments_after = post.comments.count()
        self.assertEqual(count_comments_before, count_comments_after)
