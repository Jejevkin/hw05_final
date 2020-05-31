from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post, User


def index(request):
    post_list = Post.objects.order_by('-pub_date').all()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, 'index.html',
                  {'page': page, 'paginator': paginator})


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    post_list = group.group_posts.order_by('-pub_date').all()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, 'group.html',
                  {'group': group, 'page': page, 'paginator': paginator})


@login_required
def new_post(request):
    form = PostForm(request.POST or None, files=request.FILES or None)
    context = {'form': form}
    if request.method != 'POST':
        return render(request, 'new_post.html', context)
    else:
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('index')
        return render(request, 'new_post.html', context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    post_list = author.author_posts.order_by('-pub_date').all()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    if request.user is True:
        follower = author.following.filter(user=request.user)
        return render(request, 'profile.html',
                      {'author': author, 'page': page, 'paginator': paginator,
                       'follower': follower})
    else:
        return render(request, 'profile.html',
                      {'author': author, 'page': page, 'paginator': paginator})


def post_view(request, username, post_id):
    author = get_object_or_404(User, username=username)
    post = get_object_or_404(author.author_posts, pk=post_id)
    post_comment = post.post_comments.order_by('-created').all()
    form = CommentForm()
    return render(request, 'post.html',
                  {'author': author, 'post': post, 'form': form,
                   'items': post_comment})


@login_required
def post_edit(request, username, post_id):
    author = get_object_or_404(User, username=username)
    post = get_object_or_404(author.author_posts, pk=post_id)
    if author != request.user:
        return redirect('post_view', username, post_id)
    else:
        form = PostForm(request.POST or None, files=request.FILES or None,
                        instance=post)
        if request.method == 'POST':
            if form.is_valid():
                form.save()
                return redirect('post_view', username, post_id)
        return render(request, 'new_post.html', {'form': form, 'post': post})


def page_not_found(request, exception):
    return render(request, 'misc/404.html', {'path': request.path},
                  status=404)


def server_error(request):
    return render(request, 'misc/500.html', status=500)


@login_required
def add_comment(request, username, post_id):
    author = get_object_or_404(User, username=username)
    post = get_object_or_404(author.author_posts, pk=post_id)
    form = CommentForm(request.POST)
    if request.method != 'POST':
        return redirect('post_view', username, post_id)
    else:
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.author = request.user
            comment.save()
    return redirect('post_view', username, post_id)


@login_required
def follow_index(request):
    follows = request.user.follower.all()
    authors = []
    for follow in follows:
        authors.append(follow.author)
    post_list = Post.objects.filter(author__in=authors).order_by(
        '-pub_date').all()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, 'follow.html',
                  {'page': page, 'paginator': paginator})


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    follow = request.user.follower.filter(author=author).exists()
    if follow is False and author != request.user:
        Follow.objects.create(user=request.user, author=author)
    return redirect('profile', username=username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    follow = request.user.follower.filter(author=author).exists()
    if follow is True:
        Follow.objects.filter(user=request.user, author=author).delete()
    return redirect('profile', username=username)
