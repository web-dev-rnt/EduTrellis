# live_class/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # E-Library Management URLs
    path('elibrary/', views.elibrary_manage, name='elibrary_manage'),
    path('elibrary/course/create/', views.elibrary_course_create, name='elibrary_course_create'),
    path('elibrary/course/<int:pk>/', views.elibrary_course_detail, name='elibrary_course_detail'),
    path('elibrary/course/<int:pk>/edit/', views.elibrary_course_edit, name='elibrary_course_edit'),
    path('elibrary/course/<int:pk>/delete/', views.elibrary_course_delete, name='elibrary_course_delete'),
    path('elibrary/course/<int:pk>/toggle-status/', views.elibrary_toggle_course_status, name='elibrary_toggle_course_status'),
    path('elibrary/course/<int:course_pk>/upload-pdfs/', views.elibrary_pdf_upload_multiple, name='elibrary_pdf_upload_multiple'),
    path('elibrary/pdf/<int:pk>/delete/', views.elibrary_pdf_delete, name='elibrary_pdf_delete'),
]
