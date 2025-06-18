from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth.models import User
import uuid

class Order(models.Model):
    MATERIAL_CHOICES = [
        ('PLA', 'PLA'),
        ('ABS', 'ABS'),
        ('PETG', 'PETG'),
    ]

    STATUS_CHOICES = [
        ('not_started', 'Не начат'),
        ('processing', 'В процессе'),
        ('completed', 'Готов'),
        ('paused', 'Приостановлен'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="orders") 
    model_file = models.FileField(upload_to='models/', null=True, blank=True)
    order_name = models.CharField("Название заказа", max_length=255)
    description = models.TextField("Описание")
    material = models.CharField("Материал", max_length=10, choices=MATERIAL_CHOICES)
    status = models.CharField("Статус", max_length=20, choices=STATUS_CHOICES, default='not_started')
    created_at = models.DateTimeField("Дата создания", auto_now_add=True)  
    updated_at = models.DateTimeField("Дата обновления", auto_now=True) 

    def __str__(self):
        return f"Заказ {self.order_name} ({self.material}) - {self.get_status_display()}"


class ImageUpload(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_PROCESSING = 'processing'
    STATUS_COMPLETED = 'completed'
    STATUS_FAILED = 'failed'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_PROCESSING, 'Processing'),
        (STATUS_COMPLETED, 'Completed'),
        (STATUS_FAILED, 'Failed'),
    ]

    order = models.ForeignKey('Order', on_delete=models.CASCADE, related_name='image_uploads', null=True, blank=True)

    image_file = models.ImageField(upload_to='images/')
    upload_timestamp = models.DateTimeField(auto_now_add=True)
    processed_timestamp = models.DateTimeField(null=True, blank=True)
    confidence_threshold = models.FloatField(validators=[MinValueValidator(0.0), MaxValueValidator(1.0)])
    status = models.CharField(
        max_length=50,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING
    )


class Detections(models.Model):
    object_detection = models.ForeignKey(ImageUpload, on_delete=models.CASCADE, related_name='detections')
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='detections', null=True, blank=True)

    label = models.CharField(max_length=100)
    confidence = models.FloatField()
    x_min = models.FloatField()
    x_max = models.FloatField()
    y_min = models.FloatField()
    y_max = models.FloatField()
    detection_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.label} ({self.confidence})"
    
class Camera(models.Model):
    name = models.CharField(max_length=255)
    camera_id = models.IntegerField(default=0)  
    is_active = models.BooleanField(default=False) 

    def __str__(self):
        return self.name

class CameraStream(models.Model):
    stream_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    camera_id = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
