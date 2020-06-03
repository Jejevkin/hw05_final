from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Group(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    description = models.TextField()

    def __str__(self):
        return f'{self.pk} - {self.title}'


class Post(models.Model):
    text = models.TextField()
    pub_date = models.DateTimeField('date published', auto_now_add=True,
                                    db_index=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE,
                               related_name='author_posts')
    group = models.ForeignKey(Group, on_delete=models.SET_NULL,
                              related_name='group_posts',
                              blank=True, null=True)
    image = models.ImageField(upload_to='posts/', blank=True, null=True)

    def __str__(self):
        return f'{self.pk} - {self.author} - {self.text[:20]}'


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE,
                             related_name='post_comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE,
                               related_name='author_comments')
    text = models.TextField()
    created = models.DateTimeField('date published', auto_now_add=True,
                                   db_index=True)

    class Meta:
        ordering = ['-created']

    def __str__(self):
        return f'{self.pk} - {self.author} - {self.text[:20]}'


class FollowManager(models.Manager):
    def is_following(self, user, author):
        return self.filter(user=user, author=author).exists()

    @staticmethod
    def following_posts(user, tag):
        follows = Follow.objects.filter(user=user).all()
        authors = follows.values_list(tag, flat=True)
        post_list = Post.objects.filter(author__in=authors).order_by(
            '-pub_date').all()
        return post_list


class Follow(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE,
                             related_name='follower')
    author = models.ForeignKey(User, on_delete=models.CASCADE,
                               related_name='following')
    objects = FollowManager()

    def __str__(self):
        return f'{self.pk} - {self.user} - {self.author}'
