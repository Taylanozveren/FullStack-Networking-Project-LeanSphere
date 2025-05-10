# core/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import (
    login as auth_login,
    authenticate,
    logout as auth_logout
)
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Q, Count

from .forms import UserRegisterForm, PostForm, ProfileForm, CommentForm
from .models import Profile, Discipline, Course, Post, Comment, Like


def home(request):
    return render(request, 'home.html')


def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f'Account created for {user.username}!')
            return redirect('home')
    else:
        form = UserRegisterForm()
    return render(request, 'register.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            Profile.objects.get_or_create(user=user)
            auth_login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            return redirect('home')
        else:
            messages.error(request, 'Invalid username or password.')
    return render(request, 'login.html')


def logout_view(request):
    auth_logout(request)
    messages.success(request, "You have been logged out.")
    return redirect('home')


@login_required
def profile_view(request):
    profile = request.user.profile
    return render(request, 'profile.html', {
        'profile': profile,
        'joined_courses': profile.joined_courses.all(),
    })


@login_required
def edit_profile(request):
    profile = request.user.profile
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated!')
            return redirect('profile')
    else:
        form = ProfileForm(instance=profile)
    return render(request, 'profile_form.html', {'form': form})


@login_required
def course_list(request):
    disciplines = Discipline.objects.prefetch_related('course_set').all()
    return render(request, 'course_list.html', {'disciplines': disciplines})


@login_required
def course_detail(request, slug):
    course = get_object_or_404(Course, slug=slug)

    # File-type filter param: all/pdf/image/text
    filter_type = request.GET.get('filter', 'all')
    all_posts = course.posts.all().order_by('-created_at')

    if filter_type == 'pdf':
        posts = all_posts.filter(file__iendswith='.pdf')
    elif filter_type == 'image':
        posts = all_posts.filter(file__iregex=r'\.(png|jpe?g)$')
    elif filter_type == 'text':
        posts = all_posts.filter(file__iendswith='.txt')
    else:
        posts = all_posts

    is_joined = course in request.user.profile.joined_courses.all()
    return render(request, 'course_detail.html', {
        'course': course,
        'posts': posts,
        'is_joined': is_joined,
        'filter_type': filter_type,
    })


@login_required
def join_course(request, slug):
    course = get_object_or_404(Course, slug=slug)
    profile = request.user.profile
    if course in profile.joined_courses.all():
        profile.joined_courses.remove(course)
        messages.info(request, f"You left {course.code}")
    else:
        profile.joined_courses.add(course)
        messages.success(request, f"You joined {course.code}")
    return redirect('course_detail', slug=slug)


@login_required
def create_post(request, slug):
    course = get_object_or_404(Course, slug=slug)
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.course = course
            post.save()
            messages.success(request, 'Your post has been created!')
            return redirect('post_detail', slug=post.slug)
    else:
        form = PostForm()
    return render(request, 'post_form.html', {
        'form': form,
        'course': course,
    })


@login_required
def post_detail(request, slug):
    post = get_object_or_404(Post, slug=slug)
    comment_form = CommentForm()
    return render(request, 'post_detail.html', {
        'post': post,
        'comment_form': comment_form,
    })


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.user = request.user
            comment.post = post
            comment.save()
    return redirect('post_detail', slug=post.slug)


@login_required
def edit_post(request, slug):
    post = get_object_or_404(Post, slug=slug, author=request.user)
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            form.save()
            messages.success(request, 'Post updated successfully!')
            return redirect('post_detail', slug=post.slug)
    else:
        form = PostForm(instance=post)
    return render(request, 'post_form.html', {
        'form': form,
        'course': post.course,
        'post': post,
    })


@login_required
def delete_post(request, slug):
    post = get_object_or_404(Post, slug=slug, author=request.user)
    if request.method == 'POST':
        course_slug = post.course.slug
        post.delete()
        messages.success(request, 'Post deleted successfully.')
        return redirect('course_detail', slug=course_slug)
    return render(request, 'post_confirm_delete.html', {'post': post})


@login_required
def edit_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    if comment.user != request.user and not request.user.is_superuser:
        raise PermissionDenied
    if request.method == 'POST':
        form = CommentForm(request.POST, instance=comment)
        if form.is_valid():
            form.save()
            return redirect('post_detail', slug=comment.post.slug)
    else:
        form = CommentForm(instance=comment)
    return render(request, 'comment_form.html', {
        'form': form,
        'comment': comment,
    })


@login_required
def delete_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    if comment.user != request.user and not request.user.is_superuser:
        raise PermissionDenied
    if request.method == 'POST':
        post_slug = comment.post.slug
        comment.delete()
        return redirect('post_detail', slug=post_slug)
    return render(request, 'comment_confirm_delete.html', {
        'comment': comment,
    })


# --- GLOBAL SEARCH ---
@login_required
def search(request):
    q = request.GET.get('q', '').strip()
    results = Post.objects.filter(
        Q(title__icontains=q) |
        Q(content__icontains=q) |
        Q(course__title__icontains=q) |
        Q(course__discipline__name__icontains=q)
    ).order_by('-created_at')
    return render(request, 'search_results.html', {
        'results': results,
        'q': q,
    })


# --- LIKE TOGGLE ---
@login_required
def toggle_like(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if request.user in post.likes.all():
        Like.objects.filter(user=request.user, post=post).delete()
    else:
        Like.objects.create(user=request.user, post=post)
    return redirect('post_detail', slug=post.slug)


# --- DASHBOARD & ANALYTICS ---
@login_required
def dashboard(request):
    profile = request.user.profile

    # 1. Toplam post sayısı
    total_posts = Post.objects.filter(author=request.user).count()

    # 2. En çok beğeni alan gönderi
    top_liked = (
        Post.objects
            .filter(author=request.user)
            .annotate(like_count=Count('likes'))
            .order_by('-like_count')
            .first()
    )

    # 3. Kullanıcının en aktif olduğu ders
    active_course = (
        Course.objects
            .filter(members=profile)
            .annotate(post_count=Count('posts'))
            .order_by('-post_count')
            .first()
    )

    # 4. Derslere göre post dağılımı (donut chart)
    course_stats = (
        Course.objects
            .filter(members=profile)
            .annotate(post_count=Count('posts'))
            .values('title', 'post_count')
    )

    # 5. Top 5 beğeni alan post (bar chart)
    top5_posts = (
        Post.objects
            .filter(author=request.user)
            .annotate(like_count=Count('likes'))
            .order_by('-like_count')[:5]
            .values('title', 'like_count')
    )

    return render(request, 'dashboard.html', {
        'total_posts': total_posts,
        'top_liked': top_liked,
        'active_course': active_course,
        'course_stats': list(course_stats),
        'top5_posts': list(top5_posts),
    })
