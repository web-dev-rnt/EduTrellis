from django.urls import path , include
from adminpanel import views
from live_class import views as live_class_views
from testseries import views as tviews

urlpatterns = [

    path('liveclass/', include('live_class.urls')),  # delegates to app 
    # Dashboard URLs
    path('admin_panel/', views.admin_dashboard, name='admindashboard'),
    path('signups/', views.signup_dashboard, name='signupdashboard'),
    path('payments/', views.payment_dashboard, name='paymentdashboard'),

    # User Management URLs - Put these FIRST before coupon URLs
    path('user/<int:user_id>/edit/', views.edit_user, name='edit_user'),
    path('user/<int:user_id>/delete/', views.delete_user, name='delete_user'),
    path('user/<int:user_id>/toggle-status/', views.toggle_user_status, name='toggle_user_status'),
    path('user/<int:user_id>/reset-password/', views.reset_user_password, name='reset_user_password'),

    # Coupon Management URLs
    path('coupons/', views.coupon_list, name='coupon_list'),
    path('coupons/create/', views.coupon_create, name='coupon_create'),
    path('coupons/<int:pk>/edit/', views.coupon_edit, name='coupon_edit'),
    path('coupons/<int:pk>/delete/', views.coupon_delete, name='coupon_delete'),
    path('coupons/analytics/', views.coupon_analytics, name='coupon_analytics'),

    # Public Coupon APIs
    path('api/coupons/apply/', views.apply_coupon, name='apply_coupon'),
    path('api/coupons/remove/', views.remove_coupon, name='remove_coupon'),
    path('api/coupons/validate/', views.validate_coupon, name='validate_coupon'),

    # Banner Management URLs
    path('banner-edit/', views.banner_edit, name='banneredit'),
    path('banner/create/', views.banner_create, name='banner_create'),
    path('banner/edit/<int:pk>/', views.banner_edit_single, name='banner_edit_single'),
    path('banner/delete/<int:pk>/', views.banner_delete, name='banner_delete'),
    path('banner/toggle/<int:pk>/', views.banner_toggle_status, name='banner_toggle_status'),

    # Other Details Management URLs
    path('other-details-edit/', views.other_details_edit, name='other_details_edit'),

    # Stat Card URLs
    path('stat-card/create/', views.stat_card_create, name='stat_card_create'),
    path('stat-card/edit/<int:pk>/', views.stat_card_edit, name='stat_card_edit'),
    path('stat-card/delete/<int:pk>/', views.stat_card_delete, name='stat_card_delete'),
    path('stat-card/toggle/<int:pk>/', views.stat_card_toggle_status, name='stat_card_toggle_status'),

   # CTA Section URLs
    path('cta-section/create/', views.cta_section_create, name='cta_section_create'),
    path('cta-section/<int:pk>/edit/', views.cta_section_edit, name='cta_section_edit'),
    path('cta-section/<int:pk>/delete/', views.cta_section_delete, name='cta_section_delete'),
    path('cta-section/<int:pk>/toggle-status/', views.cta_section_toggle_status, name='cta_section_toggle_status'),

    # About Us Management URLs
    path('about-us-edit/', views.about_us_edit, name='about_us_edit'),
    path('about-us-section/edit/', views.about_us_section_edit, name='about_us_section_edit'),

    # Why Choose Us URLs
    path('why-choose/create/', views.why_choose_create, name='why_choose_create'),
    path('why-choose/edit/<int:pk>/', views.why_choose_edit, name='why_choose_edit'),
    path('why-choose/delete/<int:pk>/', views.why_choose_delete, name='why_choose_delete'),
    path('why-choose/toggle/<int:pk>/', views.why_choose_toggle_status, name='why_choose_toggle_status'),

    # Service Item URLs
    path('service/create/', views.service_create, name='service_create'),
    path('service/edit/<int:pk>/', views.service_edit, name='service_edit'),
    path('service/delete/<int:pk>/', views.service_delete, name='service_delete'),
    path('service/toggle/<int:pk>/', views.service_toggle_status, name='service_toggle_status'),

    path('navbar-settings/', views.navbar_settings_edit, name='navbar_settings_edit'),

    # Footer Management URLs
    path('footer-edit/', views.footer_edit, name='footer_edit'),
    path('footer-settings/edit/', views.footer_settings_edit, name='footer_settings_edit'),

    # Footer Link URLs
    path('footer-link/create/', views.footer_link_create, name='footer_link_create'),
    path('footer-link/edit/<int:pk>/', views.footer_link_edit, name='footer_link_edit'),
    path('footer-link/delete/<int:pk>/', views.footer_link_delete, name='footer_link_delete'),
    path('footer-link/toggle/<int:pk>/', views.footer_link_toggle_status, name='footer_link_toggle_status'),

    # Footer Legal Link URLs
    path('footer-legal/create/', views.footer_legal_create, name='footer_legal_create'),
    path('footer-legal/edit/<int:pk>/', views.footer_legal_edit, name='footer_legal_edit'),
    path('footer-legal/delete/<int:pk>/', views.footer_legal_delete, name='footer_legal_delete'),
    path('footer-legal/toggle/<int:pk>/', views.footer_legal_toggle_status, name='footer_legal_toggle_status'),

    # Category Management URLs
    path('categories/', views.manage_categories, name='manage_categories'),
    path('categories/create/', views.create_category, name='create_category'),
    path('categories/edit/<int:category_id>/', views.edit_category, name='edit_category'),
    path('categories/delete/<int:category_id>/', views.delete_category, name='delete_category'),

    # SMTP Configuration URLs
    path('smtp/', views.smtp_configuration, name='smtp_configuration'),
    path('smtp/create/', views.smtp_create, name='smtp_create'),
    path('smtp/edit/<int:config_id>/', views.smtp_edit, name='smtp_edit'),
    path('smtp/test/<int:config_id>/', views.smtp_test, name='smtp_test'),
    path('smtp/delete/<int:config_id>/', views.smtp_delete, name='smtp_delete'),

    # Live Class Management URLs
    path('liveclass/', live_class_views.live_class_course_manage, name='liveclass'),
    path('liveclass/create/', live_class_views.live_class_course_create, name='live_class_course_create'),
    path('liveclass/edit/<int:pk>/', live_class_views.live_class_course_edit, name='live_class_course_edit'),
    path('liveclass/delete/<int:pk>/', live_class_views.live_class_course_delete, name='live_class_course_delete'),

    path('liveclass/toggle-status/<int:pk>/', live_class_views.live_class_course_toggle_status, name='live_class_course_toggle_status'),
    path('liveclass/classes/<int:pk>/', live_class_views.live_class_course_classes, name='live_class_course_classes'),

    path('liveclass/schedule/add/<int:course_id>/', live_class_views.add_scheduled_class, name='add_scheduled_class'),
    path('liveclass/schedule/delete/<int:session_id>/', live_class_views.live_class_schedule_delete, name='live_class_schedule_delete'),
    
    #add user
    path('users/add/', views.add_user, name='admin_add_user'),
    
# Test Series URLs - Proper naming
path('test-series-courses/', tviews.test_series_manage, name='test_series_manage'),
path('test-series-courses/create/', tviews.test_series_create, name='test_series_create'),
path('test-series-courses/<int:pk>/', tviews.test_series_detail, name='test_series_detail'),
path('test-series-courses/<int:pk>/edit/', tviews.test_series_edit, name='test_series_edit'),
path('test-series-courses/<int:pk>/delete/', tviews.test_series_delete, name='test_series_delete'),
path('test-series-courses/<int:series_pk>/schedule-test/', tviews.test_create, name='test_create'),
path('scheduled-tests/<int:pk>/edit/', tviews.test_edit, name='test_edit'),
path('scheduled-tests/<int:test_pk>/add-question/', tviews.question_create, name='question_create'),


  # Main bundle management
    path('bundle_manage/', views.bundle_manage, name='bundle_manage'),
    path('create/', views.bundle_create, name='bundle_create'),
    path('<int:pk>/', views.bundle_detail, name='bundle_detail'),
    path('<int:pk>/edit/', views.bundle_edit, name='bundle_edit'),
    path('<int:pk>/delete/', views.bundle_delete, name='bundle_delete'),
    
    # Status toggles
    path('<int:pk>/toggle-status/', views.bundle_toggle_status, name='bundle_toggle_status'),
    path('<int:pk>/toggle-featured/', views.bundle_toggle_featured, name='bundle_toggle_featured'),

    
    # AJAX endpoints
    path('calculate-price/', views.bundle_calculate_price, name='bundle_calculate_price'),

   # ========================================
    # DEVELOPER POPUP URLs - NEW
    # ========================================
    path('developer-popup/', views.developer_popup_manage, name='developer_popup_manage'),
    path('developer-popup/create/', views.developer_popup_create, name='developer_popup_create'),
    path('developer-popup/edit/<int:pk>/', views.developer_popup_edit, name='developer_popup_edit'),
    path('developer-popup/delete/<int:pk>/', views.developer_popup_delete, name='developer_popup_delete'),
    path('developer-popup/toggle/<int:pk>/', views.developer_popup_toggle_status, name='developer_popup_toggle_status'),
    

    path('adminnotifications/', views.notification_manage, name='adminnotifications'),
    path('notifications/create/', views.notification_create, name='notification_create'),
    path('notifications/delete/<int:pk>/', views.notification_delete, name='notification_delete'),
]
