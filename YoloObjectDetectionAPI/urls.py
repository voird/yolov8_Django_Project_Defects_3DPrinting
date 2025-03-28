from django.urls import path
from .views import UploadImageView, index, upload_image, defect_analysis, register_view, login_view, logout_view, order_view

urlpatterns = [
    path('', index, name='home'),
    path('process_image/', upload_image, name='process_image'),
    path('upload/', UploadImageView.as_view(), name='upload-image'),
    path('defect_analysis/', defect_analysis, name='defect_analysis'),
    path('register/', register_view, name='register'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('order/', order_view, name='order'),
]
