# core/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),

    path('courses/', views.course_list, name='course_list'),
    path('courses/<slug:slug>/', views.course_detail, name='course_detail'),
    path('courses/<slug:slug>/join/', views.join_course, name='join_course'),
    path('courses/<slug:slug>/post/new/', views.create_post, name='create_post'),

    path('posts/<slug:slug>/', views.post_detail, name='post_detail'),
    path('posts/<slug:slug>/edit/', views.edit_post, name='edit_post'),
    path('posts/<slug:slug>/delete/', views.delete_post, name='delete_post'),

    # Yeni: Yorum ekleme rotası
    path('posts/<int:post_id>/comment/', views.add_comment, name='add_comment'),
    path('comment/<int:comment_id>/edit/',   views.edit_comment,   name='edit_comment'),
    path('comment/<int:comment_id>/delete/', views.delete_comment, name='delete_comment'),
    
     # Like toggle için eklenen rota:
    path('posts/<int:post_id>/like/',       views.toggle_like,    name='toggle_like'),
]
