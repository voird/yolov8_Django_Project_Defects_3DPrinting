from django import views
from django.urls import path
from .views import UploadImageView, add_camera, available_cameras, camera_list, delete_camera, delete_order, camera_page, client_defect_analysis, download_model_file, defect_analysis_client, download_images, download_summary, get_images_client, get_order_details, get_order_images, get_orders_client,  index, toggle_camera_status, upload_image, defect_analysis, register_view, login_view, logout_view, order_view, client_orders, update_order_status, admin_panel, get_orders, get_images, get_order_summary, watch_stream # camera_page
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
    path('delete_order/<int:order_id>/', delete_order, name='delete_order'),
    path('camera_page/', camera_page, name='camera_page'),
    path('available_cameras/', available_cameras),
    path('toggle_camera/', toggle_camera_status),
    path('get_order_details/<int:order_id>/', get_order_details, name='get_order_details'),
    path('defect_analysis/', defect_analysis, name='defect_analysis'),
    path('get_orders/<int:user_id>/', get_orders, name='get_orders'),
    path('get_images/<int:order_id>/', get_images, name='get_images'),
    path('get_summary/<int:order_id>/', get_order_summary, name='get_order_summary'),
    path('download_summary/<int:order_id>/', download_summary, name='download_summary'),
    path('download_images/<int:order_id>/', download_images, name='download_images'),
    path('get-images/<int:order_id>/', get_order_images, name='get_order_images'),
    path('client_defect_analysis/<int:client_id>/', client_defect_analysis, name='client_defect_analysis'),
    path('defect_analysis/client/<int:user_id>/', defect_analysis_client, name='defect_analysis_client'),
    path('defect_analysis/client/<int:user_id>/orders/', get_orders_client, name='get_orders_client'),
    path('get_images_client/<int:order_id>/', get_images_client, name='get_images_client'),
    path('download_model/<int:order_id>/', download_model_file, name='download_model'),
    path('cameras/', camera_list, name='camera_list'),
    path('cameras/add/', add_camera, name='add_camera'),
    path('cameras/delete/<int:pk>/', delete_camera, name='delete_camera'),
    path('watch/<int:stream_id>/', watch_stream, name='watch_stream')


]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
