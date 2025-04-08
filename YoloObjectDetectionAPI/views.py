from django.shortcuts import render, redirect
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from .forms import OrderForm, CustomUserCreationForm
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import ImageUpload, Detections
from .serializers import ImageUploadSerializer
from .detection_models.yolov8 import YOLOv8Detector 
import cv2
from django.utils import timezone
from django.core.files.base import ContentFile
from django.http import HttpResponseServerError, HttpResponse  
from django.db.models import Count, Avg
from django.db.models.functions import TruncDate
import logging

#Пароль для тест аккааунтов Test123!

logger = logging.getLogger(__name__)

def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('yolov8:home')
    else:
        form = CustomUserCreationForm()
    
    # Always return index, passing both forms
    return index(request, register_form=form, login_form=AuthenticationForm())

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('yolov8:home')
    else:
        form = AuthenticationForm()
    
    # Always return index, passing both forms
    return index(request, login_form=form, register_form=CustomUserCreationForm())

def logout_view(request):
    logout(request)
    return redirect('yolov8:home')

from django.http import JsonResponse

@login_required
def order_view(request):
    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.user = request.user 
            order.save()

            return JsonResponse({"success": True, "order_name": order.order_name})

        return JsonResponse({"success": False, "errors": form.errors}, status=400)

    return JsonResponse({"success": False, "error": "Только POST-запросы разрешены"}, status=405)


def upload_image(request):
    current_date = timezone.now().date()
    images = ImageUpload.objects.filter(upload_timestamp__date=current_date)
    context = {'images': images}
    return render(request, 'process_image.html', context)

import base64
import cv2
import numpy as np
from io import BytesIO
from PIL import Image
from rest_framework.views import APIView
import tempfile
import uuid
import os
from django.core.files import File
import traceback

class UploadImageView(APIView):
    detector = YOLOv8Detector('last.pt')  # Путь к вашей YOLOv8 модели

    def post(self, request, format=None):
        image_data = request.data.get('image_data')
        order_id = request.data.get('order_id')
        if not image_data:
            return JsonResponse({'error': 'No image data provided'}, status=400)

        try:
            # Декодируем base64 изображение
            image_data = image_data.split(',')[1]  # Удаляем "data:image/jpeg;base64,"
            img_bytes = base64.b64decode(image_data)
            img_array = np.frombuffer(img_bytes, dtype=np.uint8)
            img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)

            # Генерируем имя файла
            random_filename = str(uuid.uuid4())
            media_dir = os.path.join('media', 'uploads')
            os.makedirs(media_dir, exist_ok=True)

            # Пути к оригинальному и обработанному изображениям
            original_filename = f'{random_filename}_original.jpg'
            processed_filename = f'{random_filename}_processed.jpg'

            original_img_path = os.path.join(media_dir, original_filename)
            processed_img_path = os.path.join(media_dir, processed_filename)

            # Сохраняем оригинальное изображение
            cv2.imwrite(original_img_path, img)

            # Сохраняем в базу через File, но с относительным путем
            with open(original_img_path, 'rb') as tmp_file:
                django_file = File(tmp_file)
                image_upload = ImageUpload(status=ImageUpload.STATUS_PENDING, confidence_threshold=0.5, order_id=order_id,)
                image_upload.image_file.save(original_filename, django_file, save=True)

            # Детекция YOLO
            detection_result = self.detector.run_detection(image_path=original_img_path)

            # Сохраняем результаты в базу
            for det in detection_result:
                Detections.objects.create(
                    object_detection=image_upload,
                    label=det['label'],
                    confidence=det['confidence'],
                    x_min=det['x_min'],
                    x_max=det['x_max'],
                    y_min=det['y_min'],
                    y_max=det['y_max'],
                )

            # Рисуем рамки
            for det in detection_result:
                x_min = int(det['x_min'])
                y_min = int(det['y_min'])
                x_max = int(det['x_max'])
                y_max = int(det['y_max'])

                cv2.rectangle(img, (x_min, y_min), (x_max, y_max), (0, 255, 0), 2)
                cv2.putText(img, det['label'], (x_min, y_min - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

            # Сохраняем обработанное изображение
            cv2.imwrite(processed_img_path, img)

            # Обновляем запись в базе, заменяя изображение и устанавливая статус
            with open(processed_img_path, 'rb') as tmp_file:
                django_file = File(tmp_file)
                image_upload.image_file.save(processed_filename, django_file, save=True)
                image_upload.status = ImageUpload.STATUS_COMPLETED
                image_upload.processed_timestamp = timezone.now()
                image_upload.save()

                        # Конвертируем обработанное изображение в base64
            _, img_encoded = cv2.imencode('.jpg', img)
            img_base64 = base64.b64encode(img_encoded).decode('utf-8')

            # Приведение всех значений к сериализуемым типам Python
            serialized_detections = []
            for det in detection_result:
                serialized_detections.append({
                    'label': str(det['label']),
                    'confidence': float(det['confidence']),
                    'x_min': int(det['x_min']),
                    'x_max': int(det['x_max']),
                    'y_min': int(det['y_min']),
                    'y_max': int(det['y_max']),
                })

            return JsonResponse({
                'processed_image_url': f"data:image/jpeg;base64,{img_base64}",
                'detections': serialized_detections
            })


        except Exception as e:
            traceback_str = traceback.format_exc()
            print(traceback_str)
            return JsonResponse({'error': str(e), 'trace': traceback_str}, status=500)


def index(request, form=None, register_form=None, login_form=None):
    total_images = ImageUpload.objects.all().count()
    images_processed = ImageUpload.objects.filter(status=ImageUpload.STATUS_COMPLETED).count()
    images_pending = ImageUpload.objects.filter(status=ImageUpload.STATUS_PROCESSING).count()

    defect_count = Detections.objects.count()
    defect_count_by_label = Detections.objects.values('label').annotate(count=Count('label'))

    images_processed_data = [total_images, images_processed, images_pending]
    defects_found_data = [defect['count'] for defect in defect_count_by_label]

    # If not explicitly given, initialize a form
    if not form:
        form = OrderForm()

    # If not explicitly given, initialize a registration form
    if not register_form:
        register_form = CustomUserCreationForm()

    if not login_form:
      login_form = AuthenticationForm()

    context = {
        'total_images': total_images,
        'images_processed': images_processed,
        'images_pending': images_pending,
        'user': request.user,
        'images_processed_data': images_processed_data,
        'defects_found_data': defects_found_data,
        'form': form, # The form gets passed to the template
        'register_form': register_form, # The register form gets passed to the template
        'login_form': login_form # The login form gets passed to the template
    }
    return render(request, 'home/index.html', context)

def defect_analysis(request):
    try:
        image_statuses = ImageUpload.objects.values('status').annotate(count=Count('status'))
        defect_types = Detections.objects.values('label').annotate(count=Count('label'))
        defect_dates = Detections.objects.annotate(day=TruncDate('detection_date')).values('day').annotate(count=Count('day')).order_by('day')
        average_defects_per_image = Detections.objects.aggregate(average_defects=Avg('object_detection'))

        statuses = {status['status']: status['count'] for status in image_statuses}
        labels = [defect['label'] for defect in defect_types]
        defect_counts = [defect['count'] for defect in defect_types]
        dates = [date['day'] for date in defect_dates]
        counts = [date['count'] for date in defect_dates]
        average_defects = average_defects_per_image['average_defects'] or 0

        return render(request, 'defect_analysis.html', {
            'statuses': statuses,
            'labels': labels,
            'defect_counts': defect_counts,
            'dates': dates,
            'counts': counts,
            'average_defects': average_defects
        })

    except Exception as e:
        logger.error(f"Ошибка при анализе дефектов: {e}", exc_info=True)
        return HttpResponseServerError("Произошла ошибка при обработке данных.")

from .models import Order
from .forms import OrderForm
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from .models import Order

def is_admin(user):
    return user.is_staff

@login_required
@user_passes_test(is_admin)
def admin_panel(request):
    if request.user.is_staff:
        orders = Order.objects.all()
        return render(request, 'admin_panel.html', {'orders': orders})
    else:
        return redirect('home')  # Перенаправление на главную для не-администраторов


@login_required
@user_passes_test(is_admin)
def update_order_status(request, order_id, status):
    try:
        order = Order.objects.get(id=order_id)
        order.status = status
        order.save()
        return JsonResponse({'success': True, 'status': order.get_status_display()})
    except Order.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Order not found'})


@login_required
def client_orders(request):
    orders = Order.objects.filter(user=request.user)
    return render(request, 'client_orders.html', {'orders': orders})

from django.shortcuts import render
from django.http import JsonResponse
from .models import Order

from django.shortcuts import render
from .models import Order

def camera_page(request):
    """Отображает страницу со списком заказов"""
    orders = Order.objects.all().order_by('-created_at')  # Все заказы, новые сверху
    return render(request, 'camera_page.html', {'orders': orders})

def get_order_details(request, order_id):
    """Возвращает детали заказа"""
    try:
        order = Order.objects.get(id=order_id)
        return JsonResponse({
            'order_name': order.order_name,
            'description': order.description,
            'material': order.material,
            'status': order.get_status_display(),
            'created_at': order.created_at.strftime('%Y-%m-%d %H:%M'),
        })
    except Order.DoesNotExist:
        return JsonResponse({'error': 'Заказ не найден'}, status=404)

from django.views.decorators.csrf import csrf_exempt

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json


from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json
from django.shortcuts import get_object_or_404

@csrf_exempt  # Отключает проверку CSRF (только для тестирования, в production нужно использовать CSRF токен!)
def update_order_status(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            order_id = data.get('order_id')  # Используем get, чтобы избежать KeyError
            new_status = data.get('status')  # Используем get, чтобы избежать KeyError

            order = get_object_or_404(Order, id=order_id)  # !!!Укажите правильную модель!!!
            order.status = new_status
            order.save()

            return JsonResponse({'success': True, 'status': order.get_status_display()})

        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    else:
        return JsonResponse({'success': False, 'message': 'Метод не разрешен'}, status=405)

