from django.contrib import admin
from .models import Discipline, Course, Profile, Post, Comment, Like

admin.site.register(Discipline)
admin.site.register(Course)
admin.site.register(Profile)
admin.site.register(Post)
admin.site.register(Comment)
admin.site.register(Like)
