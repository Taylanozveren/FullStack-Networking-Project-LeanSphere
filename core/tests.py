# core/tests.py

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from core.models import Discipline, Course

User = get_user_model()

class SmokeTests(TestCase):
    def setUp(self):
        # Test client
        self.client = Client()

        # 1️⃣ Test kullanıcısını oluştur
        self.username = "testuser"
        self.password = "testpass123"
        self.user = User.objects.create_user(
            username=self.username,
            password=self.password
        )

        # 2️⃣ Discipline örneği yarat
        self.discipline = Discipline.objects.create(
            name="Test Discipline",
            slug="test-discipline"
        )

        # 3️⃣ Course örneği yarat ve discipline atamasını yap
        self.course = Course.objects.create(
            code="TST101",
            title="Test Course",
            slug="test-course",
            description="Test açıklama",
            discipline=self.discipline
        )

    def test_register_and_login(self):
        # Kayıt sayfası GET 200 dönmeli
        response = self.client.get(reverse("register"))
        self.assertEqual(response.status_code, 200)

        # Mevcut kullanıcıyla login olabiliyor muyuz?
        login_ok = self.client.login(
            username=self.username,
            password=self.password
        )
        self.assertTrue(login_ok)

    def test_post_crud_flow(self):
        # Öne önce login ol
        self.client.login(username=self.username, password=self.password)

        # 1) Yeni post formuna GET isteği
        url_create = reverse("create_post", kwargs={"slug": self.course.slug})
        response_get = self.client.get(url_create)
        self.assertEqual(response_get.status_code, 200)

        # 2) POST ile gönderi oluştur
        response_post = self.client.post(url_create, {
            "title": "Test Başlık",
            "content": "Test içerik"
        })
        # Başarılıysa redirect (302) bekliyoruz
        self.assertEqual(response_post.status_code, 302)

        # 3) Gerçekten DB'ye kayıt oldu mu?
        # related_name='posts' kullanıldığı için user.posts üzerinden geliyor
        post = self.user.posts.get(title="Test Başlık")

        # 4) Detay sayfasına doğru yönlendirme
        detail_url = reverse("post_detail", kwargs={"slug": post.slug})
        self.assertRedirects(response_post, detail_url)
