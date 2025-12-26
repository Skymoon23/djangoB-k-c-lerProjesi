from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.test import TestCase, Client
from django.urls import reverse
from course_management.models import Profile
from course_management.signals import create_or_update_user_profile


class HomeViewTest(TestCase):
    """Home view testleri"""
    
    def test_home_view(self):
        """Home sayfası erişim testi"""
        client = Client()
        response = client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/home.html')


class RoleBasedLoginViewTest(TestCase):
    """Role-based login testleri"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='teststudent',
            password='testpass123'
        )
        profile, _ = Profile.objects.get_or_create(user=self.user)
        profile.role = 'student'
        profile.save()
    
    def test_login_with_correct_role(self):
        """Doğru role ile giriş testi"""
        response = self.client.post(
            reverse('login') + '?role=student',
            {'username': 'teststudent', 'password': 'testpass123'},
            follow=True
        )
        # Dashboard'a yönlendirilmeli (role'e göre student_dashboard'a gider)
        self.assertRedirects(response, reverse('student_dashboard'), status_code=302)
    
    def test_login_with_wrong_role(self):
        """Yanlış role ile giriş testi"""
        response = self.client.post(
            reverse('login') + '?role=instructor',
            {'username': 'teststudent', 'password': 'testpass123'},
            follow=True
        )
        # Hata mesajı gösterilmeli ve login sayfasında kalmalı
        self.assertContains(response, 'Kullanıcı adı veya şifre hatalı', status_code=200)
    
    def test_login_without_role_parameter(self):
        """Role parametresi olmadan login testi"""
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 302)  # Home'a redirect
        self.assertRedirects(response, reverse('home'))
    
    def test_login_page_displays_selected_role(self):
        """Login sayfasında seçilen role gösterilmeli"""
        response = self.client.get(reverse('login') + '?role=student')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Öğrenci')
    
    def test_login_with_invalid_credentials(self):
        """Geçersiz kullanıcı adı/şifre ile giriş testi"""
        response = self.client.post(
            reverse('login') + '?role=student',
            {'username': 'wronguser', 'password': 'wrongpass'},
            follow=True
        )
        self.assertContains(response, 'hatalı', status_code=200)


class DashboardRedirectTest(TestCase):
    """Dashboard redirect testleri"""
    
    def setUp(self):
        self.client = Client()
    
    def test_student_dashboard_redirect(self):
        """Öğrenci dashboard yönlendirme testi"""
        user = User.objects.create_user(
            username='student',
            password='testpass123'
        )
        profile, _ = Profile.objects.get_or_create(user=user)
        profile.role = 'student'
        profile.save()
        self.client.login(username='student', password='testpass123')
        
        response = self.client.get(reverse('dashboard_redirect'))
        self.assertRedirects(response, reverse('student_dashboard'))
    
    def test_instructor_dashboard_redirect(self):
        """Öğretmen dashboard yönlendirme testi"""
        user = User.objects.create_user(
            username='instructor',
            password='testpass123'
        )
        profile, _ = Profile.objects.get_or_create(user=user)
        profile.role = 'instructor'
        profile.save()
        self.client.login(username='instructor', password='testpass123')
        
        response = self.client.get(reverse('dashboard_redirect'))
        self.assertRedirects(response, reverse('instructor_dashboard'))
    
    def test_department_head_dashboard_redirect(self):
        """Bölüm başkanı dashboard yönlendirme testi"""
        user = User.objects.create_user(
            username='head',
            password='testpass123'
        )
        profile, _ = Profile.objects.get_or_create(user=user)
        profile.role = 'department_head'
        profile.save()
        self.client.login(username='head', password='testpass123')
        
        response = self.client.get(reverse('dashboard_redirect'))
        self.assertRedirects(response, reverse('department_head_dashboard'))
    
    def test_dashboard_redirect_without_profile(self):
        """Profile olmadan dashboard redirect testi"""
        # Signal'i geçici olarak devre dışı bırakıyoruz
        post_save.disconnect(create_or_update_user_profile, sender=User)
        
        try:
            user = User.objects.create_user(
                username='noprofile',
                password='testpass123'
            )
            Profile.objects.filter(user=user).delete()
            self.client.login(username='noprofile', password='testpass123')
            
            response = self.client.get(reverse('dashboard_redirect'))
            self.assertEqual(response.status_code, 302)
            self.assertEqual(response.url, reverse('login'))
        finally:
            post_save.connect(create_or_update_user_profile, sender=User)
    
    def test_dashboard_redirect_requires_login(self):
        """Dashboard redirect login gerektirir"""
        response = self.client.get(reverse('dashboard_redirect'))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('login'), response.url)

