from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.shortcuts import render, get_object_or_404, redirect
from users.decorators import user_valid_edit_post
from .utils import page_pagik
from .models import Post, Group, User, Follow
from .forms import PostForm, CommentForm


def index(request):
    template = 'posts/index.html'
    title = 'Это главная страница проекта Yatube'
    name_cache = 'main_post_list'
    post_list = cache.get(name_cache)
    if not post_list:
        post_list = (
            Post.objects.select_related().all()
        )
        cache.set(name_cache, post_list, settings.TIME_CACHE)
    page_obj = page_pagik(request, post_list)
    context = {
        'title': title,
        'page_obj': page_obj,
        'count_words': settings.COUNT_WORDS_POST,
    }
    return render(request, template, context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    template = 'posts/group_list.html'
    title = 'Здесь будет информация о группах проекта Yatube'
    name_cache = f'gr[{slug}]_post_list'
    post_list = cache.get(name_cache)
    if not post_list:
        post_list = group.posts.select_related('author').all()
        cache.set(name_cache, post_list, settings.TIME_CACHE)
    page_obj = page_pagik(request, post_list)
    context = {
        'title': title,
        'group': group,
        'page_obj': page_obj,
        'count_words': settings.COUNT_WORDS_POST,
    }
    return render(request, template, context)


def profile(request, username):
    template = 'posts/profile.html'
    author = get_object_or_404(User, username=username)
    user = request.user
    following = False
    if user.is_authenticated:
        following = Follow.objects.filter(
            author=author,
            user=user
        ).exists()
    name_cache = f'pf[{username}]_post_list'
    post_list = cache.get(name_cache)
    if not post_list:
        post_list = author.posts.select_related().all()
        cache.set(name_cache, post_list, settings.TIME_CACHE)
    page_obj = page_pagik(request, post_list)
    context = {
        'author': author,
        'count_posts': post_list.count,
        'page_obj': page_obj,
        'count_words': settings.COUNT_WORDS_POST,
        'following': following,
    }
    return render(request, template, context)


def post_detail(request, post_id):
    template = 'posts/post_detail.html'
    post = get_object_or_404(Post.objects.select_related(), id=post_id)
    is_read = (post.author == request.user)
    comments_list = post.comments.all()
    context = {
        'post': post,
        'count_chars': settings.COUNT_CHAR_POST_TITLE,
        'is_read': is_read,
        'form_comment': CommentForm(),
        'comments_list': comments_list,
    }
    return render(request, template, context)


@login_required
def post_create(request):
    template = 'posts/create_post.html'
    context = {
        'title': 'Создать новый пост',
        'button_name': 'Добавить',
    }
    form = PostForm(request.POST or None,
                    files=request.FILES or None,)
    if form.is_valid():
        form = form.save(commit=False)
        form.author = request.user
        form.save()
        return redirect('posts:profile', username=request.user.username)
    context['form'] = form
    return render(request, template, context)


@user_valid_edit_post
@login_required
def post_edit(request, post_id):
    template = 'posts/create_post.html'
    instance = get_object_or_404(Post.objects.select_related(), id=post_id)
    context = {
        'title': 'Редактировать пост',
        'button_name': 'Сохранить',
    }
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=instance
    )
    if form.is_valid():

        form.save()

        return redirect('posts:post_detail', post_id)
    context['form'] = form
    return render(request, template, context)


@user_valid_edit_post
@login_required
def post_delete(request, post_id):
    Post.objects.filter(id=post_id).delete()
    return redirect('posts:main')


@login_required
def add_comment(request, post_id):
    post = Post.objects.get(id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    authors = [obj.author for obj in request.user.follower.all()]
    post_list = Post.objects.filter(author__in=authors)
    page_obj = page_pagik(request, post_list)
    context = {
        'title': 'Избранные авторы',
        'page_obj': page_obj,
        'count_words': settings.COUNT_WORDS_POST,
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    author = User.objects.get(username=username)
    if author != request.user:
        Follow.objects.get_or_create(
            author=author,
            user=request.user,
        )
    return redirect('posts:profile', username)


@login_required
def profile_unfollow(request, username):
    author = User.objects.get(username=username)
    if Follow.objects.filter(author=author, user=request.user).exists():
        Follow.objects.get(author=author, user=request.user).delete()
    return redirect('posts:profile', username)
