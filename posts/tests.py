import os

from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse
from django.utils.http import urlencode
from PIL import Image

from users.tests import UserFactory

from .models import Comment, Group, Post


class TestPosting(TestCase):
    def setUp(self):
        self.client = Client()
        self.new_text = 'Новая тестовая запись'
        self.user = UserFactory.create()

    def test_get_new_post_form_if_logged_in(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('new_post'))
        self.assertEqual(response.status_code, 200,
                         msg='Авторизованный пользователь'
                             ' не может получить форму публикации поста.')

    def test_create_new_post_if_logged_in(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse('new_post'),
                                    {'text': self.new_text}, follow=True)
        self.assertRedirects(response, reverse('index'),
                             msg_prefix='Пользователь не перенаправлен'
                                        ' на главную страницу.')
        posts_count = Post.objects.count()
        self.assertEqual(posts_count, 1,
                         msg='Пользователь не смог создать пост.')
        post_exists = self.user.author_posts.filter(
            text=self.new_text).exists()
        self.assertTrue(post_exists,
                        msg='Содержимое поста не равно переданному в запросе.')

    def test_display_new_post(self):
        created_post = Post.objects.create(text=self.new_text,
                                           author=self.user)
        cache.clear()
        response = self.client.get(reverse('index'))
        self.assertContains(response, self.new_text,
                            msg_prefix='Новая запись не появляется на'
                                       ' главной странице сайта.')
        response = self.client.get(
            reverse('profile', args=[self.user.username]))
        self.assertContains(response, self.new_text,
                            msg_prefix='Новая запись не появляется на'
                                       ' персональной странице пользователя.')
        response = self.client.get(reverse('post_view', kwargs={
            'username': self.user.username, 'post_id': created_post.pk}))
        self.assertContains(response, self.new_text,
                            msg_prefix='Новая запись не появляется на'
                                       ' отдельной странице поста.')

    def test_get_new_post_form_if_not_logged_in(self):
        response = self.client.get(reverse('new_post'), follow=True)
        url = '?'.join(
            [reverse('login'), urlencode({'next': reverse('new_post')})])
        self.assertRedirects(response, url,
                             msg_prefix='Неавторизованный посетитель'
                                        ' не перенаправляется страницу'
                                        ' авторизации.')

    def test_create_new_post_if_not_logged_in(self):
        response = self.client.post(reverse('new_post'),
                                    {'text': self.new_text},
                                    follow=True)
        url = '?'.join(
            [reverse('login'), urlencode({'next': reverse('new_post')})])
        self.assertRedirects(response, url,
                             msg_prefix='Неавторизованный посетитель'
                                        ' не перенаправляется страницу'
                                        ' авторизации.')
        posts_count = Post.objects.count()
        self.assertEqual(posts_count, 0, msg='Неавторизованный посетитель'
                                             ' создал пост.')


class TestEditPost(TestCase):
    def setUp(self):
        self.client = Client()
        self.user1 = UserFactory.create()
        self.user2 = UserFactory.create()
        self.old_text = 'Тестовая запись'
        self.edited_text = 'Отредактированная тестовоая запись'
        self.post = Post.objects.create(text=self.old_text, author=self.user1)
        self.context = {'username': self.user1.username,
                        'post_id': self.post.pk}

    def test_get_edit_post_form_if_author(self):
        self.client.force_login(self.user1)
        response = self.client.get(reverse('post_edit', kwargs=self.context))
        self.assertEqual(response.status_code, 200,
                         msg='Автор'
                             ' не может получить форму редактирования поста.')

    def test_author_edits_post(self):
        self.client.force_login(self.user1)
        response = self.client.post(reverse('post_edit', kwargs=self.context),
                                    {'text': self.edited_text}, follow=True)
        self.assertRedirects(response,
                             reverse('post_view', kwargs=self.context),
                             msg_prefix='Автор не перенаправлен'
                                        ' на страницу просмотра поста.')
        text = self.user1.author_posts.get(pk=self.post.pk).text
        self.assertEqual(text, self.edited_text,
                         msg='Автор не смог изменить пост.')
        posts_count = self.user1.author_posts.count()
        self.assertEqual(posts_count, 1, msg='Автор изменил'
                                             ' количество постов.')

    def test_display_edited_post(self):
        Post.objects.filter(text=self.old_text).update(text=self.edited_text)
        cache.clear()
        response = self.client.get(reverse('index'))
        self.assertContains(response, self.edited_text,
                            msg_prefix='Измененная запись не появляется на'
                                       ' главной странице сайта.')
        response = self.client.get(
            reverse('profile', args=[self.user1.username]))
        self.assertContains(response, self.edited_text,
                            msg_prefix='Измененная запись не появляется на'
                                       ' персональной странице пользователя.')
        response = self.client.get(reverse('post_view', kwargs=self.context))
        self.assertContains(response, self.edited_text,
                            msg_prefix='Измененная запись не появляется на'
                                       ' отдельной странице поста.')

    def test_get_edit_post_form_if_not_author(self):
        self.client.force_login(self.user2)
        response = self.client.get(reverse('post_edit', kwargs=self.context))
        self.assertRedirects(response,
                             reverse('post_view', kwargs=self.context),
                             msg_prefix='Сторонний пользователь'
                                        ' не перенаправляется страницу'
                                        ' просмотра поста.')

    def test_not_author_edits_post(self):
        self.client.force_login(self.user2)
        response = self.client.post(reverse('post_edit', kwargs=self.context),
                                    {'text': self.edited_text}, follow=True)
        self.assertRedirects(response,
                             reverse('post_view', kwargs=self.context),
                             msg_prefix='Сторонний пользователь'
                                        ' не перенаправляется страницу'
                                        ' просмотра поста.')
        text = self.user1.author_posts.get(pk=self.post.pk).text
        self.assertEqual(text, self.old_text, msg='Сторонний пользователь смог'
                                                  ' изменить текст поста.')


class TestImage(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = UserFactory.create()
        self.client.force_login(self.user)
        self.group = Group.objects.create(title='Test Group',
                                          slug='testgroup',
                                          description='test group')
        self.post = Post.objects.create(text='Test post', author=self.user)
        self.context = {'username': self.user.username,
                        'post_id': self.post.pk}
        self.path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        img = Image.new("RGB", (100, 100), (0, 0, 0))
        img.save('testimg.jpg')
        f = open('testfile.txt', 'tw', encoding='utf-8')
        f.write('Test')
        f.close()

    def test_img_upload(self):
        with open('testimg.jpg', 'rb') as img:
            self.client.post(reverse('post_edit', kwargs=self.context),
                             {'text': 'New text', 'group': 1, 'image': img})
        cache.clear()
        response = self.client.get(reverse('index'))
        self.assertContains(response, '<img class="card-img"',
                            msg_prefix='Изображение не появляется на'
                                       ' главной странице сайта.')
        response = self.client.get(
            reverse('profile', args=[self.user.username]))
        self.assertContains(response, '<img class="card-img"',
                            msg_prefix='Изображение не появляется на'
                                       ' персональной странице пользователя.')
        response = self.client.get(reverse('post_view', kwargs=self.context))
        self.assertContains(response, '<img class="card-img"',
                            msg_prefix='Изображение не появляется на'
                                       ' отдельной странице поста.')
        response = self.client.get(
            reverse('group_posts', args=[self.group.slug]))
        self.assertContains(response, '<img class="card-img"',
                            msg_prefix='Изображение не появляется на'
                                       ' отдельной странице группы.')
        path_media = os.path.join(self.path, 'media/posts/testimg.jpg')
        os.remove(path_media)

    def test_img_error(self):
        with open('testfile.txt', 'rb') as test_file:
            response = self.client.post(reverse('new_post'),
                                        {'text': 'Test post', 'group': 1,
                                         'image': test_file})
        self.assertFormError(response, 'form', 'image',
                             errors='Загрузите правильное изображение. Файл,'
                                    ' который вы загрузили, поврежден или не'
                                    ' является изображением.',
                             msg_prefix='Загружено изображение')

    def tearDown(self):
        path_img = os.path.join(self.path, 'testimg.jpg')
        os.remove(path_img)
        path_file = os.path.join(self.path, 'testfile.txt')
        os.remove(path_file)


class TestCache(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = UserFactory.create()
        self.client.force_login(self.user)

    def test_cache_index(self):
        self.client.post(reverse('new_post'), {'text': 'Test post'})
        response = self.client.get(reverse('index'))
        self.assertContains(response, 'Test post',
                            msg_prefix='Пост не отображается на'
                                       ' главной странице сайта.')
        self.client.post(reverse('new_post'), {'text': 'New test post'})
        response = self.client.get(reverse('index'))
        self.assertNotContains(response, 'New test post',
                               msg_prefix='Новый пост отображается на'
                                          ' главной странице сайта.')
        cache.clear()
        response = self.client.get(reverse('index'))
        self.assertContains(response, 'New test post',
                            msg_prefix='Новый пост не отображается на'
                                       ' главной странице сайта.')


class TestComment(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = UserFactory.create()
        self.comment = 'Test comment'
        self.post = Post.objects.create(text='Test post', author=self.user)
        self.context = {'username': self.user.username,
                        'post_id': self.post.pk}

    def test_comment_if_logged_in(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse('add_comment', kwargs=self.context),
            {'text': self.comment}, follow=True)
        self.assertRedirects(response,
                             reverse('post_view', kwargs=self.context),
                             msg_prefix='Комментатор не перенаправлен'
                                        ' на страницу просмотра поста.')
        comment_count = Comment.objects.count()
        self.assertEqual(comment_count, 1,
                         msg='Пользователь не смог написать комментарий.')
        comment_exists = self.user.author_comments.filter(
            text=self.comment).exists()
        self.assertTrue(comment_exists,
                        msg='Содержимое комментария'
                            ' не равно переданному в запросе.')

    def test_comment_display_if_logged_in(self):
        Comment.objects.create(text=self.comment, author=self.user,
                               post=self.post)
        response = self.client.get(reverse('post_view', kwargs=self.context))
        self.assertContains(response, self.comment,
                            msg_prefix='Комментарий не появляется на'
                                       ' отдельной странице поста.')

    def test_comment_if_not_logged_in(self):
        response = self.client.post(
            reverse('add_comment', kwargs=self.context),
            {'text': self.comment}, follow=True)
        url = '?'.join(
            [reverse('login'),
             urlencode({'next': reverse('add_comment', kwargs=self.context)})])
        self.assertRedirects(response, url,
                             msg_prefix='Неавторизованный посетитель'
                                        ' не перенаправляется страницу'
                                        ' авторизации.')
        comment_count = Comment.objects.count()
        self.assertEqual(comment_count, 0, msg='Неавторизованный посетитель'
                                               ' прокомментировал пост.')


class TestFollow(TestCase):
    def setUp(self):
        self.client = Client()
        self.user1 = UserFactory.create()
        self.user2 = UserFactory.create()
        self.user3 = UserFactory.create()
        self.text = 'Test post'
        self.post = Post.objects.create(text=self.text, author=self.user3)

    def test_profile_follow_if_logged_in(self):
        self.client.force_login(self.user1)
        follow = self.user1.follower.filter(author=self.user3).exists()
        self.assertFalse(follow, msg='Пользователь подписан на автора.')
        self.client.get(reverse('profile_follow', args=[self.user3.username]))
        follow = self.user1.follower.filter(author=self.user3).exists()
        self.assertTrue(follow,
                        msg='Пользователь не смог подписаться на автора.')
        self.client.get(
            reverse('profile_unfollow', args=[self.user3.username]))
        follow = self.user1.follower.filter(author=self.user3).exists()
        self.assertFalse(follow,
                         msg='Пользователь не смог отписаться от автора.')

    def test_double_follow(self):
        self.client.force_login(self.user1)
        response = self.client.get(
            reverse('profile', args=[self.user3.username]))
        self.assertContains(response, 'Подписаться',
                            msg_prefix='Предложение подписаться не появляется '
                                       'персональной странице пользователя.')
        self.client.get(reverse('profile_follow', args=[self.user3.username]))
        response = self.client.get(
            reverse('profile', args=[self.user3.username]))
        self.assertContains(response, 'Отписаться',
                            msg_prefix='Предложение отписаться не появляется '
                                       'на персональной странице '
                                       'пользователя.')
        self.client.get(reverse('profile_follow', args=[self.user3.username]))
        response = self.client.get(
            reverse('profile', args=[self.user3.username]))
        self.assertContains(response, 'Отписаться',
                            msg_prefix='После второй попытки подписаться, '
                                       'исчезло предложение отписаться.')
        following = self.user3.following.count()
        self.assertEqual(following, 1, msg='Пользователь отписался после '
                                           'двойной подписки.')

    def test_double_unfollow(self):
        self.client.force_login(self.user1)
        self.client.get(
            reverse('profile_unfollow', args=[self.user3.username]))
        response = self.client.get(
            reverse('profile', args=[self.user3.username]))
        self.assertContains(response, 'Подписаться',
                            msg_prefix='После отписки без подписки, '
                                       'исчезло предложение подписаться.')
        following = self.user3.following.count()
        self.assertEqual(following, 0, msg='Пользователь подписался '
                                           'после двойной отписки.')

    def test_follow_yourself(self):
        self.client.force_login(self.user1)
        response = self.client.get(
            reverse('profile', args=[self.user1.username]))
        self.assertNotContains(response, 'Подписаться',
                               msg_prefix='На собственной персональной '
                                          'странице есть предложение '
                                          'подписаться.')

        self.client.get(reverse('profile_follow', args=[self.user1.username]))
        response = self.client.get(
            reverse('profile', args=[self.user1.username]))
        self.assertNotContains(response, 'Отписаться',
                               msg_prefix='На На собственной персональной '
                                          'странице есть предложение '
                                          'отписаться.')
        following = self.user1.following.count()
        self.assertEqual(following, 0,
                         msg='Удалось подписаться на самого себя.')

    def test_profile_follow_if_not_logged_in(self):
        self.client.get(reverse('profile_follow', args=[self.user3.username]))
        follow = self.user1.follower.filter(author=self.user3).exists()
        self.assertFalse(follow,
                         msg='Неавторизованный посетитель смог'
                             ' подписаться на автора.')

    def test_display_favorite_authors_post(self):
        self.client.force_login(self.user1)
        self.client.get(reverse('profile_follow', args=[self.user3.username]))
        response = self.client.get(reverse('follow_index'))
        self.assertContains(response, self.text,
                            msg_prefix='Пост не отображается на'
                                       ' странице избранных авторов'
                                       ' подписанного пользователя.')
        self.client.force_login(self.user2)
        response = self.client.get(reverse('follow_index'))
        self.assertNotContains(response, self.text,
                               msg_prefix='Пост отображается на'
                                          ' странице избранных авторов '
                                          'неподписанного пользователя.')
