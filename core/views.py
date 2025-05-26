# core/views.py

import re
import requests
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Count
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.utils import timezone
import logging
from django.core.mail import send_mail

from .models import Profile, Discipline, Course, Post, Comment, Like, Notification, User
from .forms import CommentForm, PostForm, ProfileForm, UserRegisterForm, NewsletterForm
from .utils import (
    extract_text_from_pdf,
    chunk_text,
    generate_summary,
    generate_explanation,
)


def home(request):
    return render(request, "home.html")


def register(request):
    if request.method == "POST":
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f"Account created for {user.username}!")
            return redirect("home")
    else:
        form = UserRegisterForm()
    return render(request, "register.html", {"form": form})


def login_view(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)
        if user is not None:
            Profile.objects.get_or_create(user=user)
            auth_login(request, user)
            messages.success(request, f"Welcome back, {user.username}!")
            return redirect("home")
        else:
            messages.error(request, "Invalid username or password.")
    return render(request, "login.html")


def logout_view(request):
    auth_logout(request)
    messages.success(request, "You have been logged out.")
    return redirect("home")


@login_required
def profile_view(request):
    profile = request.user.profile
    posts = Post.objects.filter(author=request.user).order_by("-created_at")
    posts_count = posts.count()
    active_course = (
        Course.objects.filter(members=profile)
        .annotate(post_count=Count("posts"))
        .order_by("-post_count")
        .first()
    )

    return render(
        request,
        "profile.html",
        {
            "profile": profile,
            "joined_courses": profile.joined_courses.all(),
            "posts": posts,
            "posts_count": posts_count,
            "active_course": active_course,
        },
    )


@login_required
def edit_profile(request):
    profile = request.user.profile
    if request.method == "POST":
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated!")
            return redirect("profile")
    else:
        form = ProfileForm(instance=profile)
    return render(request, "profile_form.html", {"form": form})


@login_required
def course_list(request):
    disciplines = Discipline.objects.prefetch_related(
        "course_set",
        "course_set__members",
        "course_set__posts",
        "course_set__posts__likes",
        "course_set__posts__comments",
    ).all()

    for discipline in disciplines:
        for course in discipline.course_set.all():
            course.total_likes = sum(post.likes.count() for post in course.posts.all())
            course.total_comments = sum(
                post.comments.count() for post in course.posts.all()
            )

    return render(request, "course_list.html", {"disciplines": disciplines})


@login_required
def course_detail(request, slug):
    course = get_object_or_404(Course, slug=slug)

    filter_type = request.GET.get("filter", "all")
    all_posts = course.posts.all().order_by("-created_at")
    if filter_type == "pdf":
        posts = all_posts.filter(file__iendswith=".pdf")
    elif filter_type == "image":
        posts = all_posts.filter(file__iregex=r"\.(png|jpe?g)$")
    elif filter_type == "text":
        posts = all_posts.filter(file__iendswith=".txt")
    else:
        posts = all_posts

    is_joined = course in request.user.profile.joined_courses.all()
    filter_choices = [
        ("all", "All"),
        ("pdf", "PDF"),
        ("image", "Images"),
        ("text", "Text"),
    ]

    return render(
        request,
        "course_detail.html",
        {
            "course": course,
            "posts": posts,
            "is_joined": is_joined,
            "filter_type": filter_type,
            "filter_choices": filter_choices,
        },
    )


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
    return redirect("course_detail", slug=slug)


@login_required
def create_post(request, slug):
    course = get_object_or_404(Course, slug=slug)
    if request.method == "POST":
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.course = course
            post.save()
            messages.success(request, "Your post has been created!")
            return redirect("post_detail", slug=post.slug)
    else:
        form = PostForm()
    return render(
        request,
        "post_form.html",
        {
            "form": form,
            "course": course,
        },
    )


@login_required
def post_detail(request, slug):
    post = get_object_or_404(Post, slug=slug)
    comment_form = CommentForm()

    # kısa içerikse explain, uzun içerikse summary butonu göstermek için
    TEXT_EXPLAIN_THRESHOLD = 200
    content_text = post.content or ""
    is_short_content = (
        bool(content_text.strip()) and len(content_text) <= TEXT_EXPLAIN_THRESHOLD
    )

    comments = post.comments.all().order_by("-created_at")  # Most recent first

    return render(
        request,
        "post_detail.html",
        {
            "post": post,
            "comment_form": comment_form,
            "is_short_content": is_short_content,
            "comments": comments,
        },
    )


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    user = request.user

    if request.method == "POST":
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.user = user
            comment.post = post
            comment.save()

            # Create notification if needed
            if post.author != user:
                Notification.objects.create(
                    user=post.author,
                    from_user=user,
                    post=post,
                    comment=comment,
                    message=f'{user.username} commented on your post "{post.title}"',
                )

        # Always return updated comments list, regardless of form validity
        comments = post.comments.all().order_by("-created_at")
        return render(
            request,
            "_comments_list.html",
            {
                "comments": comments,
                "user": user,
                "form": form if not form.is_valid() else CommentForm(),
            },
        )

    return redirect("post_detail", slug=post.slug)


@login_required
def edit_post(request, slug):
    post = get_object_or_404(Post, slug=slug, author=request.user)
    if request.method == "POST":
        form = PostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            form.save()
            messages.success(request, "Post updated successfully!")
            return redirect("post_detail", slug=post.slug)
    else:
        form = PostForm(instance=post)
    return render(
        request,
        "post_form.html",
        {
            "form": form,
            "course": post.course,
            "post": post,
        },
    )


@login_required
def delete_post(request, slug):
    post = get_object_or_404(Post, slug=slug, author=request.user)
    if request.method == "POST":
        course_slug = post.course.slug
        post.delete()
        messages.success(request, "Post deleted successfully.")
        return redirect("course_detail", slug=course_slug)
    return render(request, "post_confirm_delete.html", {"post": post})


@login_required
def edit_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    if comment.user != request.user and not request.user.is_superuser:
        raise PermissionDenied

    if request.method == "POST":
        form = CommentForm(request.POST, instance=comment)
        if form.is_valid():
            form.save()
            # Return the updated comment in its normal display format
            return render(
                request,
                "_comments_list.html",
                {
                    "comments": [comment],  # Pass as single-item list
                    "user": request.user,
                },
            )
    else:
        form = CommentForm(instance=comment)

    return render(request, "comment_form.html", {"form": form, "comment": comment})


@login_required
def delete_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    if comment.user != request.user and not request.user.is_superuser:
        raise PermissionDenied

    post = comment.post
    if request.method == "POST":
        comment.delete()
        comments = post.comments.all().order_by("-created_at")
        return render(
            request, "_comments_list.html", {"comments": comments, "user": request.user}
        )

    return JsonResponse({"status": "error"}, status=400)


@login_required
def search(request):
    q = request.GET.get("q", "").strip()
    results = Post.objects.filter(
        Q(title__icontains=q)
        | Q(content__icontains=q)
        | Q(course__title__icontains=q)
        | Q(course__discipline__name__icontains=q)
    ).order_by("-created_at")
    return render(
        request,
        "search_results.html",
        {
            "results": results,
            "q": q,
        },
    )


@login_required
def toggle_like(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    user = request.user

    # Like / Unlike
    if user in post.likes.all():
        Like.objects.filter(user=user, post=post).delete()
    else:
        Like.objects.create(user=user, post=post)
        if post.author != user:
            Notification.objects.create(
                user=post.author,
                from_user=user,
                post=post,
                message=f'{user.username} liked your post "{post.title}"',
            )

    # HTMX request ise sadece like form partial
    if request.headers.get("Hx-Request"):
        return render(
            request,
            "partials/like_form.html",
            {
                "post": post,
                "user": user,
            },
        )

    return redirect("post_detail", slug=post.slug)


@login_required
def dashboard(request):
    profile = request.user.profile
    total_posts = Post.objects.filter(author=request.user).count()
    top_liked = (
        Post.objects.filter(author=request.user)
        .annotate(like_count=Count("likes"))
        .order_by("-like_count")
        .first()
    )
    active_course = (
        Course.objects.filter(members=profile)
        .annotate(post_count=Count("posts"))
        .order_by("-post_count")
        .first()
    )
    course_stats = (
        Course.objects.filter(members=profile)
        .annotate(post_count=Count("posts"))
        .values("title", "post_count")
    )
    top5_posts = (
        Post.objects.filter(author=request.user)
        .annotate(like_count=Count("likes"))
        .order_by("-like_count")[:5]
        .values("title", "like_count")
    )
    return render(
        request,
        "dashboard.html",
        {
            "total_posts": total_posts,
            "top_liked": top_liked,
            "active_course": active_course,
            "course_stats": list(course_stats),
            "top5_posts": list(top5_posts),
        },
    )


@login_required
def notifications(request):
    notes = request.user.notifications.all()
    request.user.notifications.filter(is_read=False).update(is_read=True)
    return render(
        request,
        "notifications.html",
        {
            "all_notifications": notes,
        },
    )


@login_required
@require_POST
def mark_notification_read(request, pk):
    note = get_object_or_404(Notification, pk=pk, user=request.user)
    if not note.is_read:
        note.is_read = True
        note.save()
    return JsonResponse({"success": True})


@login_required
@require_POST
def delete_notification(request, pk):
    note = get_object_or_404(Notification, pk=pk, user=request.user)
    note.delete()
    return JsonResponse({"success": True})


@login_required
def post_explain(request, slug):
    post = get_object_or_404(Post, slug=slug)
    text = (post.content or "").strip()
    if not text:
        return render(
            request,
            "partials/ai_summary.html",
            {"error": "No text content to explain."},
        )
    try:
        explanation = generate_explanation(text)
        return render(
            request,
            "partials/ai_summary.html",
            {
                "summary": explanation,
                "title": "AI Explanation",
                "now": timezone.localtime(),
            },
        )
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"AI explanation error: {str(e)}")

        error_msg = str(e)
        if "API_TOKEN" in error_msg:
            error_msg = (
                "API configuration error. Please check your Hugging Face API settings."
            )
        elif "timeout" in error_msg.lower():
            error_msg = "API request timed out. The server might be busy, please try again later."
        else:
            error_msg = "Could not generate AI explanation. Please try again later."

        return render(request, "partials/ai_summary.html", {"error": error_msg})


@login_required
def post_summary(request, slug):
    post = get_object_or_404(Post, slug=slug)
    summary_type = request.GET.get("type", "pdf")  # 'pdf' veya 'text'

    # Kaynak metni al
    try:
        if summary_type == "pdf":
            if not post.file:
                return render(
                    request, "partials/ai_summary.html", {"error": "No PDF attached."}
                )
            text = extract_text_from_pdf(post.file.path)
            if not text.strip():
                return render(
                    request,
                    "partials/ai_summary.html",
                    {
                        "error": "Could not extract text from PDF. The file might be empty or protected."
                    },
                )
        else:
            text = (post.content or "").strip()
            if not text:
                return render(
                    request,
                    "partials/ai_summary.html",
                    {"error": "No text content to process."},
                )

        # Özet üret
        chunks = chunk_text(text, max_chars=8000)
        summaries = []

        for block in chunks:
            try:
                summaries.append(generate_summary(block))
            except Exception as e:
                logger = logging.getLogger(__name__)
                logger.error(f"Chunk summarization error: {str(e)}")
                return render(
                    request,
                    "partials/ai_summary.html",
                    {"error": f"Error during summarization: {str(e)}"},
                )

        final_summary = "\n\n".join(summaries)

        # PDF özeti ise kaydet
        if summary_type == "pdf":
            post.pdf_summary = final_summary
            post.save()

        return render(
            request,
            "partials/ai_summary.html",
            {
                "summary": final_summary,
                "title": "AI Summary",
                "now": timezone.localtime(),
            },
        )

    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"AI summary error: {str(e)}")

        error_msg = str(e)
        if "API_TOKEN" in error_msg:
            error_msg = (
                "API configuration error. Please check your Hugging Face API settings."
            )
        elif "timeout" in error_msg.lower():
            error_msg = "API request timed out. The server might be busy, please try again later."
        elif "extract_text" in error_msg:
            error_msg = "Could not extract text from PDF. The file might be corrupted or password protected."
        else:
            error_msg = "Could not generate AI summary. Please try again later."

        return render(request, "partials/ai_summary.html", {"error": error_msg})


@login_required
def change_username(request):
    if request.method == "POST":
        new_username = request.POST.get("new_username")
        current_password = request.POST.get("current_password")

        # Validate current password
        if not request.user.check_password(current_password):
            messages.error(request, "Current password is incorrect.")
            return redirect("profile")

        # Check if username is available
        if (
            User.objects.filter(username=new_username)
            .exclude(id=request.user.id)
            .exists()
        ):
            messages.error(request, "This username is already taken.")
            return redirect("profile")

        try:
            # Update username
            request.user.username = new_username
            request.user.save()
            messages.success(request, "Username updated successfully!")
        except Exception as e:
            messages.error(request, "An error occurred while updating username.")

    return redirect("profile")


def subscribe_newsletter(request):
    if request.method == "POST":
        form = NewsletterForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data["email"]
            messages.success(
                request, f"Thank you for subscribing! We will keep you updated."
            )
            return redirect(request.META.get("HTTP_REFERER", "home"))
    return redirect("home")
