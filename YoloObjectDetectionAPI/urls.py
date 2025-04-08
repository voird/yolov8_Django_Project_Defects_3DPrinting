from django.urls import path
from .views import UploadImageView, camera_page, get_order_details,  index, upload_image, defect_analysis, register_view, login_view, logout_view, order_view, client_orders, update_order_status, admin_panel # camera_page
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path('', index, name='home'),
    path('process_image/', upload_image, name='process_image'),
    path('upload/', UploadImageView.as_view(), name='upload-image'),
    path('defect_analysis/', defect_analysis, name='defect_analysis'),
    path('register/', register_view, name='register'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('order/', order_view, name='order'),
    path('update_order_status/', update_order_status, name='update_order_status'),
    path('my_orders/', client_orders, name='client_orders'),
    path('admin_panel/', admin_panel, name='admin_panel'),
    path('camera_page/', camera_page, name='camera_page'),
    path('get_order_details/<int:order_id>/', get_order_details, name='get_order_details'),
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
