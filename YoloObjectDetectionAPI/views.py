from django.shortcuts import render, redirect
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from .forms import OrderForm, CustomUserCreationForm
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import ImageUpload, Detections
from .serializers import ImageUploadSerializer
from .detection_models.yolov8 import YOLOv8Detector  # Замените на ваш путь
import cv2
from django.utils import timezone
from django.core.files.base import ContentFile
from django.http import HttpResponseServerError, HttpResponse  # Для обработки ошибок
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

class UploadImageView(APIView):
    detector = YOLOv8Detector('last.pt')  # Замените на ваш путь к модели

    def post(self, request, format=None):
        def draw_labels(image, detections):
            for det in detections:
                x_min, y_min, x_max, y_max = int(det['x_min']), int(det['x_max']), int(det['x_max']), int(det['y_max'])
                label = det['label']
                cv2.rectangle(image, (x_min, y_min), (x_max, y_max), (0, 255, 0), 2)
                cv2.putText(image, label, (x_min, y_min - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (36, 255, 12), 2)
            return image

        serializer = ImageUploadSerializer(data=request.data)
        if serializer.is_valid():
            image_upload = serializer.save()

            try:
                detection_result = self.detector.run_detection(image_path=image_upload.image_file.path, confidence_threshold=image_upload.confidence_threshold)
                image_upload.status = ImageUpload.STATUS_COMPLETED

                image_with_detections = cv2.imread(image_upload.image_file.path)
                image_with_labels = draw_labels(image_with_detections, detection_result)

                labeled_image = cv2.imencode('.jpg', image_with_labels)[1].tobytes()
                image_upload.image_file.save(image_upload.image_file.name, ContentFile(labeled_image))

                image_upload.processed_timestamp = timezone.now()
                image_upload.save()

                for detection in detection_result:
                    Detections.objects.create(
                        object_detection=image_upload,
                        label=detection['label'],
                        confidence=detection['confidence'],
                        x_min=detection['x_min'],
                        x_max=detection['x_max'],
                        y_min=detection['y_min'],
                        y_max=detection['y_max']
                    )

            except Exception as e:
                image_upload.status = ImageUpload.STATUS_FAILED
                image_upload.save()
                logger.error(f"Ошибка при обработке изображения: {e}", exc_info=True)
                return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            return Response({'detections': detection_result}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# modified to accept optional form data for initial rendering or error handling
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
