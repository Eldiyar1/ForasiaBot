from django.db import models


class TelegramUser(models.Model):
    user_id = models.IntegerField(verbose_name="ID пользователя", unique=True)
    first_name = models.CharField(verbose_name="Имя", max_length=255)
    last_name = models.CharField(verbose_name="Фамилия", max_length=255, blank=True, null=True)
    username = models.CharField(verbose_name="Имя пользователя", max_length=255, blank=True, null=True)
    date_joined = models.DateTimeField(verbose_name="Дата присоединения", auto_now_add=True)
    is_admin = models.BooleanField(verbose_name="Администратор", default=False)
    is_active = models.BooleanField(verbose_name="Активен", default=True)

    def __str__(self):
        return self.username

    class Meta:
        verbose_name = "Пользователь Telegram"
        verbose_name_plural = "Пользователи Telegram"


class Order(models.Model):
    operator = models.ForeignKey(
        TelegramUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="оператор",
        default=None,
        verbose_name="Оператор"
    )
    user = models.ForeignKey(
        TelegramUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="пользователь",
        verbose_name="Пользователь"
    )
    is_active = models.BooleanField(verbose_name="Активен", default=True)

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name} {self.user.username}"

    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"
