# core/models.py

from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone


class Discipline(models.Model):
    name = models.CharField(max_length=60, unique=True)
    slug = models.SlugField(unique=True, editable=False)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Course(models.Model):
    discipline = models.ForeignKey(Discipline, on_delete=models.CASCADE)
    code = models.CharField(max_length=10)
    title = models.CharField(max_length=100)
    description = models.TextField()
    slug = models.SlugField(unique=True, editable=False)

    class Meta:
        unique_together = ("discipline", "code")

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(f"{self.code}-{self.title}")
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.code} – {self.title}"


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(blank=True)
    avatar = models.ImageField(upload_to="avatars/", default="avatars/default.png")
    github_url = models.URLField(blank=True, null=True)
    linkedin_url = models.URLField(blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    joined_courses = models.ManyToManyField(Course, blank=True, related_name="members")

    def __str__(self):
        return f"{self.user.username} Profili"


# Kullanıcı oluşturulduğunda Profile da otomatik gelsin:
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()


class Post(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="posts")
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="posts")
    title = models.CharField(max_length=150)
    content = models.TextField(blank=True)
    file = models.FileField(upload_to="uploads/", blank=True, null=True)

    # ————— Yeni alan: AI ile oluşturulacak özet metni
    pdf_summary = models.TextField(
        blank=True,
        null=True,
        help_text="HuggingFace AI ile oluşturulan PDF/metin özeti",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    slug = models.SlugField(unique=True, editable=False)
    likes = models.ManyToManyField(
        User, through="Like", related_name="liked_posts", blank=True
    )

    def save(self, *args, **kwargs):
        if not self.slug:
            ts = int(self.created_at.timestamp()) if self.created_at else ""
            self.slug = slugify(f"{self.title}-{self.author.username}-{ts}")
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments")
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Yorum by {self.user.username} on {self.post.title}"


class Like(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "post")

    def __str__(self):
        return f"{self.user.username} liked {self.post.title}"


# Notification modelini burada, **sınıfın dışında**, en sona ekle!
class Notification(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="notifications"
    )
    from_user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="sent_notifications"
    )
    post = models.ForeignKey("Post", on_delete=models.CASCADE, null=True, blank=True)
    comment = models.ForeignKey(
        "Comment", on_delete=models.CASCADE, null=True, blank=True
    )
    message = models.CharField(max_length=255)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Notification for {self.user.username} from {self.from_user.username}: {self.message}"


# Opsiyonel: Etkinlik takvimi ileride eklemek istersen:
# class Event(models.Model):
#     title       = models.CharField(max_length=100)
#     description = models.TextField()
#     datetime    = models.DateTimeField()
#     course      = models.ForeignKey(Course, on_delete=models.CASCADE, blank=True, null=True)
#     attendees   = models.ManyToManyField(Profile, blank=True, related_name="events")
#
#     def __str__(self):
#         return self.title
