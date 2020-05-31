from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from factory import Faker
from factory.django import DjangoModelFactory

User = get_user_model()


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User

    username = Faker('first_name')
    email = 'factory@yatube.com'
    password = 'password_factory'


class TestProfile(TestCase):
    def setUp(self):
        self.client = Client()
        self.users = UserFactory.build_batch(10)
        self.user = UserFactory.build()
        self.context = {'username': self.user.username,
                        'email': self.user.email,
                        'password1': self.user.password,
                        'password2': self.user.password}

    def test_unregistered_user_profile_does_not_exist(self):
        for user in self.users:
            with self.subTest(user=user):
                response = self.client.get(
                    reverse('profile', args=[user.username]))
                self.assertEqual(response.status_code, 404,
                                 msg='Существуют персональные страницы '
                                     'незарегистрированных пользователей.')

    def test_registered_user_profile_exists(self):
        response = self.client.get(
            reverse('profile', args=[self.user.username]))
        self.assertEqual(response.status_code, 404,
                         msg='Существует персональная страница'
                             ' незарегистрированного пользователя.')
        self.client.post(reverse('signup'), self.context, follow=True)
        response = self.client.get(
            reverse('profile', args=[self.user.username]))
        self.assertEqual(response.status_code, 200,
                         msg='После регистрации пользователя'
                             ' не создается его персональная страница.')


class TestCode404Error(TestCase):
    def setUp(self):
        self.client = Client()

    def test_404(self):
        users = UserFactory.build()
        response = self.client.get(reverse('profile', args=[users]))
        self.assertEqual(response.status_code, 404,
                         msg='Сервер не возвращает код 404,')
        users = UserFactory.create()
        response = self.client.get(reverse('profile', args=[users]))
        self.assertEqual(response.status_code, 200,
                         msg='Сервер не возвращает код 200,')
