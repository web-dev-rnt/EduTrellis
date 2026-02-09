# base/urls.py - Add these URL patterns
from django.urls import path, include
from base import views

from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.home, name='home'),
    path('login_user', views.loginuser, name='login'),
    path('signup_user', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout_user'),
    path('apply-coupon/', views.apply_coupon, name='apply_coupon'),
    path('my-coupons/', views.my_coupons, name='my_coupons'),
    path('category/<slug:slug>/', views.category_detail, name='category_detail'),
    
    # OTP Verification
    path('verify-otp/', views.verify_otp_view, name='verify_otp'),
    path('resend-otp/', views.resend_otp_view, name='resend_otp'),
    
    # Password Reset with OTP
    path('forgot-password/', views.forgot_password_request, name='forgot_password_request'),
    path('verify-reset-otp/', views.verify_reset_otp, name='verify_reset_otp'),
    path('reset-password/', views.reset_password, name='reset_password'),
    
    # Profile
    path('profile/edit/', views.profile_edit, name='profile_edit'),
    path('profile/password/', views.change_password, name='change_password'),
    
    # Courses
    path("course/<int:pk>/", views.video_course_detail, name="video_course_detail"),
    path("live-class/<int:pk>/", views.live_class_detail, name="live_class_detail"),
    
    # Test Series - Frontend URLs
    path('exam-series/<int:pk>/', views.test_series_detail, name='front_exam_series_detail'),
    path('exam/<int:test_id>/start/', views.start_test, name='front_exam_start'),
    path('exam/session/<uuid:attempt_id>/', views.take_test, name='front_exam_session'),
    path('exam/session/<uuid:attempt_id>/submit/', views.submit_test, name='front_exam_submit'),
    path('exam/session/<uuid:attempt_id>/result/', views.test_result, name='front_exam_result'),
    path('exam/session/<uuid:attempt_id>/review/', views.review_answers, name='front_exam_review'),
    
    # Product Bundles - NEW
    # path('bundles/', views.product_bundles_list, name='product_bundles_list'),
    path('bundle/<slug:slug>/', views.product_bundle_detail, name='product_bundle_detail'),
    
    # Search
    path('search/', views.search_results, name='search_results'),
    path('api/search-suggestions/', views.search_suggestions, name='search_suggestions'),

    # E-Library
    path('ebook/<int:pk>/', views.elibrary_course_detail, name='course_detail'),
    path('pdf/<int:pdf_id>/view/', views.elibrary_view_pdf, name='view_pdf'),
    path('pdf/<int:pdf_id>/download/', views.elibrary_download_pdf, name='download_pdf'),
    path('my-library/', views.my_elibrary, name='my_library'),

    #Payment URLs
    path('payment/create/<str:course_type>/<int:course_id>/',views.create_payment_order, name='create_payment_order'),
    path('payment/handler/', views.payment_handler,name='payment_handler'),
    path('my_purchases/', views.my_purchases, name='my_purchases'),

    # Notifications


path('notifications/', views.notifications_list, name='notifications_list'),
path('notifications/<int:notification_id>/read/', views.mark_notification_read, name='mark_notification_read'),
path('notifications/<int:notification_id>/delete/', views.delete_notification, name='delete_notification'),
path('notifications/mark-all-read/', views.mark_all_notifications_read, name='mark_all_notifications_read'),
path('notifications/clear-all/', views.clear_all_notifications, name='clear_all_notifications'),

   # PWA URLs
    path('manifest.json', views.manifest, name='manifest1'),
    path('offline/', views.offline, name='offline'),
    path('serviceworker.js', views.service_worker, name='service-worker'),
]
