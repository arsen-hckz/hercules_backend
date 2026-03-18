from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models


class UserManager(BaseUserManager):
    def create_user(self, email, username, password=None, **extra_fields):
        if not email:
            raise ValueError('Email is required')
        email = self.normalize_email(email)
        user = self.model(email=email, username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, username, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    GENDER_CHOICES = [('M', 'Male'), ('F', 'Female'), ('O', 'Other')]
    GOAL_CHOICES = [('bulk', 'Bulk'), ('cut', 'Cut'), ('maintain', 'Maintain')]
    ACTIVITY_CHOICES = [
        ('sedentary', 'Sedentary'),
        ('light', 'Lightly Active'),
        ('moderate', 'Moderately Active'),
        ('active', 'Active'),
        ('very_active', 'Very Active'),
    ]

    email = models.EmailField(unique=True)
    username = models.CharField(max_length=50, unique=True)
    first_name = models.CharField(max_length=50, blank=True)
    last_name = models.CharField(max_length=50, blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    bio = models.TextField(blank=True)

    # Body stats
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    height_cm = models.FloatField(null=True, blank=True)
    weight_kg = models.FloatField(null=True, blank=True)

    # Goals
    goal = models.CharField(max_length=10, choices=GOAL_CHOICES, default='maintain')
    target_weight_kg = models.FloatField(null=True, blank=True)
    goal_deadline = models.DateField(null=True, blank=True)
    activity_level = models.CharField(max_length=20, choices=ACTIVITY_CHOICES, default='moderate')

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.username

    @property
    def full_name(self):
        return f'{self.first_name} {self.last_name}'.strip()

    def calculate_bmi(self):
        if self.weight_kg and self.height_cm:
            height_m = self.height_cm / 100
            return round(self.weight_kg / (height_m ** 2), 1)
        return None

    def calculate_tdee(self):
        """Mifflin-St Jeor BMR * activity multiplier, adjusted for goal."""
        if not all([self.weight_kg, self.height_cm, self.date_of_birth, self.gender]):
            return None

        from datetime import date
        age = (date.today() - self.date_of_birth).days // 365

        if self.gender == 'M':
            bmr = 10 * self.weight_kg + 6.25 * self.height_cm - 5 * age + 5
        else:
            bmr = 10 * self.weight_kg + 6.25 * self.height_cm - 5 * age - 161

        multipliers = {
            'sedentary': 1.2,
            'light': 1.375,
            'moderate': 1.55,
            'active': 1.725,
            'very_active': 1.9,
        }
        tdee = bmr * multipliers.get(self.activity_level, 1.55)

        if self.goal == 'bulk':
            tdee += 300
        elif self.goal == 'cut':
            tdee -= 500

        return round(tdee)


class Follow(models.Model):
    follower = models.ForeignKey(User, related_name='following', on_delete=models.CASCADE)
    following = models.ForeignKey(User, related_name='followers', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('follower', 'following')

    def __str__(self):
        return f'{self.follower} -> {self.following}'
