from django.urls import path
from . import views

app_name = 'schedule' # Uygulama adı namespace için

urlpatterns = [
    path('view/', views.view_schedule, name='view_schedule'), # Yeni görüntüleme sayfası
    path('export/excel/', views.export_schedule_excel, name='export_excel'),
    path('import/courses/', views.import_courses_view, name='import_courses'),
    path('generate/', views.trigger_schedule_generation, name='generate_schedule'),
    path('update-slot-position/', views.update_slot_position, name='update_slot_position'), # AJAX için yeni URL
    # Diğer schedule URL'leri buraya eklenecek
] 