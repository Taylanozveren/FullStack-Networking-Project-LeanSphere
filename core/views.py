from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import (
    login as auth_login,
    authenticate,
    logout as auth_logout
)
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from .forms import UserRegisterForm, PostForm, ProfileForm
from .models import Profile, Discipline, Course, Post

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
    course    = get_object_or_404(Course, slug=slug)
    posts     = course.posts.all().order_by('-created_at')
    is_joined = course in request.user.profile.joined_courses.all()
    return render(request, 'course_detail.html', {
        'course': course,
        'posts': posts,
        'is_joined': is_joined,
    })

@login_required
def join_course(request, slug):
    course  = get_object_or_404(Course, slug=slug)
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
    return render(request, 'post_detail.html', {'post': post})

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
