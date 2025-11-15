# live_class/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.live_class_course_manage, name='liveclass'),  # /liveclass/ [1]
    path('create/', views.live_class_course_create, name='live_class_course_create'),  # /liveclass/create/ [2]
    path('edit/<int:pk>/', views.live_class_course_edit, name='live_class_course_edit'),  # /liveclass/edit/ID/ [2]
    path('delete/<int:pk>/', views.live_class_course_delete, name='live_class_course_delete'),  # /liveclass/delete/ID/ [2]

    # AJAX endpoints referenced by templates/JS [1]
    path('toggle-status/<int:pk>/', views.live_class_course_toggle_status, name='live_class_course_toggle_status'),  # /liveclass/toggle-status/ID/ [2]
    path('classes/<int:pk>/', views.live_class_course_classes, name='live_class_course_classes'),  # /liveclass/classes/ID/ [2]

    # Schedule CRUD used by JS [1]
    path('schedule/add/<int:course_id>/', views.add_scheduled_class, name='add_scheduled_class'),  # /liveclass/schedule/add/COURSE/ [2]
    path('schedule/delete/<int:session_id>/', views.live_class_schedule_delete, name='live_class_schedule_delete'),  # /liveclass/schedule/delete/ID/ [2]

    # Jitsi join route used by the Start button [1]
    path('session/<int:session_id>/join/', views.live_class_join, name='live_class_join'),  # /liveclass/session/ID/join/ [2]

]

