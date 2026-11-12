from django.conf import settings
from django.db import models


class Review(models.Model):
    # Оценки от 1 до 5
    RATING_CHOICES = (
        (1, '★☆☆☆☆ (1)'),
        (2, '★★☆☆☆ (2)'),
        (3, '★★★☆☆ (3)'),
        (4, '★★★★☆ (4)'),
        (5, '★★★★★ (5)'),
    )

    product = models.ForeignKey('Product', on_delete=models.CASCADE, related_name='reviews', verbose_name='Товар')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name='Автор')
    text = models.TextField(verbose_name='Текст отзыва')
    rating = models.PositiveSmallIntegerField(choices=RATING_CHOICES, default=5, verbose_name='Оценка')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')

    class Meta:
        ordering = ['-created_at'] # Сначала свежие отзывы
        verbose_name = 'Отзыв'
        verbose_name_plural = 'Отзывы'

    def __str__(self):
        return f"Отзыв от {self.user.username} на {self.product.name}"
    
class UserProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile',
        null=True,
        blank=True,
    )
    photo = models.ImageField(
        upload_to='profile_photos/',
        blank=True,
        null=True,
    )

    def __str__(self):
        return f'Профиль {self.user.username if self.user else "без пользователя"}'

class Category(models.Model):
    name = models.CharField("Название", max_length=100)
    slug = models.SlugField("URL-слаг", unique=True)
    description = models.TextField("Описание", blank=True)
    Products = models.ManyToManyField('Product', related_name='categories', blank=True)

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Product(models.Model):
    category = models.ForeignKey(
        Category,
        related_name="products",
        on_delete=models.CASCADE,
        verbose_name="Категория"
    )

    image = models.ImageField(
        upload_to="products/",
        blank=True,
        null=True
    )

    file = models.FileField(
        "Файл",
        upload_to="products/files/",
        blank=True,
        null=True
    )

    name = models.CharField(
        "Название товара",
        max_length=200
    )

    author = models.CharField(
        "Автор",
        max_length=100,
        blank=True,
        null=True
    )

    slug = models.SlugField(
        "URL-слаг",
        unique=True
    )

    description = models.TextField(
        "Описание",
        blank=True
    )

    price = models.DecimalField(
        "Цена",
        max_digits=10,
        decimal_places=2
    )

    pdf_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Цена PDF-версии"
    )

    stock = models.PositiveIntegerField(
        "Остаток на складе",
        default=0
    )

    is_active = models.BooleanField(
        "Доступен для покупки",
        default=True
    )

    created_at = models.DateTimeField(
        "Дата создания",
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        "Дата обновления",
        auto_now=True
    )

    class Meta:
        verbose_name = "Товар"
        verbose_name_plural = "Товары"
        ordering = ["-created_at"]

    def __str__(self):
        return self.name
    def is_pdf(self):
        return bool(
            self.file and
            self.file.name.lower().endswith(".pdf")
        )

    @property
    def selling_price(self):
        if self.is_pdf() and self.pdf_price is not None:
            return self.pdf_price
        return self.price
    
class Order(models.Model):
    class StatusChoices(models.TextChoices):
        NEW = "new", "Новый"
        PAID = "paid", "Оплачен"
        SHIPPED = "shipped", "Отправлен"
        COMPLETED = "completed", "Завершен"
        CANCELED = "canceled", "Отменен"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="orders",
        on_delete=models.CASCADE,
        verbose_name="Покупатель",
        null=True,
        blank=True
    )
    total_price = models.DecimalField(
        "Общая цена",
        max_digits=10,
        decimal_places=2,
        default=0
    )
    first_name = models.CharField("Имя", max_length=45)
    last_name = models.CharField("Фамилия", max_length=50)
    email = models.EmailField("Email")
    address = models.CharField("Адрес доставки", max_length=250)
    status = models.CharField(
        "Статус заказа",
        max_length=20,
        choices=StatusChoices.choices,
        default=StatusChoices.NEW
    )
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Товар")
    created_at = models.DateTimeField("Дата создания", auto_now_add=True)
    updated_at = models.DateTimeField("Дата обновления", auto_now=True)
    quantity = models.PositiveIntegerField(default=1, verbose_name="Количество")
    

    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Заказ #{self.id}"

    def get_total_cost(self):
        """Расчет общей стоимости всего заказа"""
        return sum(item.get_cost() for item in self.items.all())


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        related_name="items",
        on_delete=models.CASCADE,
        verbose_name="Заказ"
    )
    product = models.ForeignKey(
        Product,
        related_name="order_items",
        on_delete=models.PROTECT,
        verbose_name="Товар"
    )
    price = models.DecimalField("Цена за единицу", max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField("Количество", default=1)

    class Meta:
        verbose_name = "Позиция заказа"
        verbose_name_plural = "Позиции заказа"

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"

    def get_cost(self):
        """Расчет стоимости единицы товара с учетом количества"""
        return self.price * self.quantity