from django.contrib.auth import get_user_model
from django.test import TestCase
from ..models import Group, Post


User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание. ' * 20,
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост. ' * 20,
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        self.assertEqual(PostModelTest.group.__str__(),
                         PostModelTest.group.title,
                         '__str__ группы не было определено как title')
        self.assertEqual(PostModelTest.post.__str__(),
                         PostModelTest.post.text[:15],
                         '__str__ поста не было определено как text[:15]')

    def test_models_have_correct_verbose_name(self):
        """Проверяем, что у моделей корректно работает verbose_name."""
        field_help_texts_post = {
            'text': 'Текст поста',
            'pub_date': 'Дата публикации',
            'author': 'Автор',
            'group': 'Группа',
        }
        field_help_texts_group = {
            'title': 'Название группы',
            'slug': 'Путь',
            'description': 'Описание группы',
        }
        post = PostModelTest.post
        group = PostModelTest.group
        for field, expected_value in field_help_texts_post.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).verbose_name,
                    expected_value
                )

        for field, expected_value in field_help_texts_group.items():
            with self.subTest(field=field):
                self.assertEqual(
                    group._meta.get_field(field).verbose_name,
                    expected_value
                )
