from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.test import TestCase, Client
from django.urls import reverse
from course_management.models import Profile
from course_management.signals import create_or_update_user_profile


class HomeViewTest(TestCase):

    def test_home_view(self):
        client = Client()
        response = client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/home.html')


class RoleBasedLoginViewTest(TestCase):
    
    def setUp(self):
        self.client = Client()
        class_name = self.__class__.__name__.lower()
        self.user = User.objects.create_user(
            username=f'{class_name}_student',
            password='testpass123'
        )
        profile, _ = Profile.objects.get_or_create(user=self.user)
        profile.role = 'student'
        profile.save()
    
    def test_login_with_correct_role(self):
        """Doğru role ile giriş testi"""
        response = self.client.post(
            reverse('login') + '?role=student',
            {'username': self.user.username, 'password': 'testpass123'},
            follow=True
        )
        
        self.assertRedirects(response, reverse('student_dashboard'), status_code=302)
    
    def test_login_with_wrong_role(self):
        response = self.client.post(
            reverse('login') + '?role=instructor',
            {'username': self.user.username, 'password': 'testpass123'},
            follow=True
        )
        
        self.assertContains(response, 'Kullanıcı adı veya şifre hatalı', status_code=200)
    
    def test_login_without_role_parameter(self):
        response = self.client.get(reverse('login'))
        
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('home'))
    
    def test_login_page_displays_selected_role(self):
        response = self.client.get(reverse('login') + '?role=student')
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Öğrenci')
    
    def test_login_with_invalid_credentials(self):
        response = self.client.post(
            reverse('login') + '?role=student',
            {'username': 'wronguser', 'password': 'wrongpass'},
            follow=True
        )
        
        self.assertContains(response, 'hatalı', status_code=200)


class DashboardRedirectTest(TestCase):
    
    def setUp(self):
        self.client = Client()
    
    def test_student_dashboard_redirect(self):
        class_name = self.__class__.__name__.lower()
        user = User.objects.create_user(
            username=f'{class_name}_student',
            password='testpass123'
        )
        profile, _ = Profile.objects.get_or_create(user=user)
        profile.role = 'student'
        profile.save()
        
        self.client.login(username=user.username, password='testpass123')
        
        response = self.client.get(reverse('dashboard_redirect'))
        self.assertRedirects(response, reverse('student_dashboard'))
    
    def test_instructor_dashboard_redirect(self):
        class_name = self.__class__.__name__.lower()
        user = User.objects.create_user(
            username=f'{class_name}_instructor',
            password='testpass123'
        )
        profile, _ = Profile.objects.get_or_create(user=user)
        profile.role = 'instructor'
        profile.save()
        
        self.client.login(username=user.username, password='testpass123')
        
        response = self.client.get(reverse('dashboard_redirect'))
        self.assertRedirects(response, reverse('instructor_dashboard'))
    
    def test_department_head_dashboard_redirect(self):
        class_name = self.__class__.__name__.lower()
        user = User.objects.create_user(
            username=f'{class_name}_head',
            password='testpass123'
        )
        profile, _ = Profile.objects.get_or_create(user=user)
        profile.role = 'department_head'
        profile.save()
        
        self.client.login(username=user.username, password='testpass123')
        
        response = self.client.get(reverse('dashboard_redirect'))
        self.assertRedirects(response, reverse('department_head_dashboard'))
    
    def test_dashboard_redirect_without_profile(self):
        post_save.disconnect(create_or_update_user_profile, sender=User)
        
        try:
            class_name = self.__class__.__name__.lower()
            user = User.objects.create_user(
                username=f'{class_name}_noprofile',
                password='testpass123'
            )
            Profile.objects.filter(user=user).delete()
            
            self.client.login(username=user.username, password='testpass123')
            
            response = self.client.get(reverse('dashboard_redirect'))
            self.assertEqual(response.status_code, 302)
            self.assertEqual(response.url, reverse('login'))
        finally:
            post_save.connect(create_or_update_user_profile, sender=User)
    
    def test_dashboard_redirect_requires_login(self):
        response = self.client.get(reverse('dashboard_redirect'))
        
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('login'), response.url)

