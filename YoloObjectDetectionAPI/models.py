from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth.models import User

class ImageUpload(models.Model):
    STATUS_PROCESSING = 'pending'
    STATUS_PROCESSING = 'processing'
    STATUS_COMPLETED = 'completed'
    STATUS_FAILED = 'failed'

    STATUS_CHOICES = [
        (STATUS_PROCESSING, 'Pending'),
        (STATUS_PROCESSING, 'Processing'),
        (STATUS_COMPLETED, 'Completed'),
        (STATUS_FAILED, 'Failed'),
    ]

    image_file = models.ImageField(upload_to='media/images/')
    upload_timestamp = models.DateTimeField(auto_now_add=True)
    processed_timestamp = models.DateTimeField(null=True, blank=True)
    confidence_threshold = models.FloatField(validators=[MinValueValidator(0.0), MaxValueValidator(1.0)])
    status = models.CharField(
        max_length=50,
        choices=STATUS_CHOICES,
        default=STATUS_PROCESSING
    )


class Detections(models.Model):
    object_detection = models.ForeignKey(ImageUpload, on_delete=models.CASCADE, related_name='detections')
    label = models.CharField(max_length=100)
    confidence = models.FloatField()
    x_min = models.FloatField()
    x_max = models.FloatField()
    y_min = models.FloatField()
    y_max = models.FloatField()
    detection_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.label} ({self.confidence})"
    


from django.db import models
from django.contrib.auth.models import User

class Order(models.Model):
    MATERIAL_CHOICES = [
        ('PLA', 'PLA'),
        ('ABS', 'ABS'),
        ('PETG', 'PETG'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="orders")  # Кто оформил заказ
    order_name = models.CharField("Название заказа", max_length=255)
    description = models.TextField("Описание")
    material = models.CharField("Материал", max_length=10, choices=MATERIAL_CHOICES)
    created_at = models.DateTimeField("Дата создания", auto_now_add=True)  # Дата оформления
    updated_at = models.DateTimeField("Дата обновления", auto_now=True)  # Дата последнего изменения

    def __str__(self):
        return f"Заказ {self.order_name} ({self.material})"
