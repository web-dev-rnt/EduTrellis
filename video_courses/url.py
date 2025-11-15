from django.urls import path
from . import views

urlpatterns = [
    path("video-courses/create/", views.video_course_create, name="video_course_create"),
    path("video-courses/<int:pk>/edit/", views.video_course_edit_by_pk, name="video_course_edit_by_pk"),  # Changed name here
    path("video-courses/<int:pk>/delete/", views.video_course_delete, name="video_course_delete"),
    path("video-courses/manage/", views.video_course_manage, name="video_course_manage"),
]
