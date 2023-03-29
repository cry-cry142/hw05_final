from django.shortcuts import redirect, get_object_or_404
from functools import wraps
from posts.models import Post


def user_valid_edit_post(func):
    @wraps(func)
    def wrapper(request, *args, **kwargs):
        post = get_object_or_404(Post, id=kwargs['post_id'])
        if post.author == request.user:
            return func(request, *args, **kwargs)
        return redirect('posts:post_detail', kwargs['post_id'])
    return wrapper
