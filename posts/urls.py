from django.urls import path
from . import views

urlpatterns = [
    path("", views.post_list, name="post_list"),
    path("<int:post_id>/", views.post_detail, name="post_detail"),
    path("create/", views.create_post, name="create_post"),
    path("<int:post_id>/edit/", views.edit_post, name="edit_post"),
    path("<int:post_id>/delete/", views.delete_post, name="delete_post"),
    path("<int:post_id>/explain/", views.explain_post, name="explain_post"),
]
