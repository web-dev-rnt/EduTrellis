# ==================== DJANGO CORE IMPORTS ====================
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse, FileResponse, HttpResponse, Http404, HttpResponseBadRequest
from django.urls import reverse
from django.utils import timezone
from django.core.cache import cache
from django.core.mail import send_mail
from django.conf import settings
from django.db.models import Count, Sum, Prefetch, Q, Avg
from django.contrib.auth.hashers import make_password
import razorpay

# ==================== LOCAL APP IMPORTS ====================
from .forms import (
    EmailLoginForm, 
    SignupForm, 
    ProfileEditForm,
    PasswordChangeSimpleForm, 
    OTPVerificationForm
)
from .models import User, OTPVerification, UserCourseAccess, Payment
from .utils import has_smtp_configured, create_and_send_otp
from video_courses.models import VideoCourse, Category
from live_class.models import LiveClassCourse, LiveClassSession
from testseries.models import TestSeries, Test, TestAttempt, StudentAnswer
from elibrary.models import (
    ELibraryCourse, 
    ELibraryPDF, 
    ELibraryEnrollment, 
    ELibraryDownload
)
from adminpanel.models import (
    ProductBundle, 
    Coupon, 
    UserCoupon, 
    SMTPConfiguration, 
    Notification as AdminNotification
)

# ==================== OTHER IMPORTS ====================
import json
import os
import secrets
import string
from datetime import timedelta
import logging

from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_GET
from django.views.decorators.cache import cache_control
from django.conf import settings
from django.shortcuts import render
import os

@require_GET
@cache_control(max_age=0, no_cache=True, no_store=True, must_revalidate=True)
def service_worker(request):
    """Serve the service worker from root URL"""
    sw_path = os.path.join(settings.BASE_DIR, 'static', 'js', 'serviceworker.js')
    
    try:
        with open(sw_path, 'r', encoding='utf-8') as sw_file:
            sw_content = sw_file.read()
            response = HttpResponse(sw_content, content_type='application/javascript; charset=utf-8')
            response['Service-Worker-Allowed'] = '/'
            return response
    except FileNotFoundError:
        return HttpResponse('Service worker not found', status=404, content_type='text/plain')

@require_GET
@cache_control(max_age=3600)  # Cache for 1 hour
def manifest(request):
    """Generate and serve the manifest.json dynamically"""
    
    # Build absolute URLs for icons
    def build_icon_url(filename):
        return request.build_absolute_uri(settings.STATIC_URL + f'img/{filename}')
    
    manifest_data = {
        "name": "EduTrellis - Complete Learning Platform",
        "short_name": "EduTrellis",
        "description": "Access live classes, video courses, test series, and e-library. Learn anytime, anywhere with EduTrellis.",
        "start_url": "/",
        "scope": "/",
        "display": "standalone",
        "background_color": "#ffffff",
        "theme_color": "#c7212f",
        "orientation": "portrait-primary",
        "categories": ["education", "learning", "productivity"],
        "lang": "en-IN",
        "dir": "ltr",
        
        # Icons - required for PWA
        "icons": [
            {
                "src": build_icon_url("icon-72x72.png"),
                "sizes": "72x72",
                "type": "image/png",
                "purpose": "any"
            },
            {
                "src": build_icon_url("icon-96x96.png"),
                "sizes": "96x96",
                "type": "image/png",
                "purpose": "any"
            },
            {
                "src": build_icon_url("icon-128x128.png"),
                "sizes": "128x128",
                "type": "image/png",
                "purpose": "any"
            },
            {
                "src": build_icon_url("icon-144x144.png"),
                "sizes": "144x144",
                "type": "image/png",
                "purpose": "any"
            },
            {
                "src": build_icon_url("icon-152x152.png"),
                "sizes": "152x152",
                "type": "image/png",
                "purpose": "any"
            },
            {
                "src": build_icon_url("icon-192x192.png"),
                "sizes": "192x192",
                "type": "image/png",
                "purpose": "any maskable"
            },
            {
                "src": build_icon_url("icon-384x384.png"),
                "sizes": "384x384",
                "type": "image/png",
                "purpose": "any"
            },
            {
                "src": build_icon_url("icon-512x512.png"),
                "sizes": "512x512",
                "type": "image/png",
                "purpose": "any maskable"
            }
        ],
        
        # Shortcuts - quick actions from app icon (Android)
        "shortcuts": [
            {
                "name": "Video Courses",
                "short_name": "Courses",
                "description": "Browse all video courses",
                "url": "/#video-courses",
                "icons": [
                    {
                        "src": build_icon_url("icon-192x192.png"),
                        "sizes": "192x192",
                        "type": "image/png"
                    }
                ]
            },
            {
                "name": "Live Classes",
                "short_name": "Live",
                "description": "Join live classes",
                "url": "/#live-classes",
                "icons": [
                    {
                        "src": build_icon_url("icon-192x192.png"),
                        "sizes": "192x192",
                        "type": "image/png"
                    }
                ]
            },
            {
                "name": "Test Series",
                "short_name": "Tests",
                "description": "Take practice tests",
                "url": "/#test-series",
                "icons": [
                    {
                        "src": build_icon_url("icon-192x192.png"),
                        "sizes": "192x192",
                        "type": "image/png"
                    }
                ]
            },
            {
                "name": "E-Library",
                "short_name": "Library",
                "description": "Access digital books",
                "url": "/#e-library",
                "icons": [
                    {
                        "src": build_icon_url("icon-192x192.png"),
                        "sizes": "192x192",
                        "type": "image/png"
                    }
                ]
            }
        ],
        
        # Screenshots - helps with app store listing (optional but recommended)
        "screenshots": [
            {
                "src": build_icon_url("screenshot-1.png"),
                "sizes": "540x720",
                "type": "image/png",
                "form_factor": "narrow",
                "label": "Home page showing all courses"
            },
            {
                "src": build_icon_url("screenshot-2.png"),
                "sizes": "1280x720",
                "type": "image/png",
                "form_factor": "wide",
                "label": "Course detail page"
            }
        ],
        
        # Related applications - set to false to prefer PWA
        "prefer_related_applications": False,
        
        # Additional features
        "iarc_rating_id": "",  # Add if you have IARC rating
        "gcm_sender_id": "",   # Add if using push notifications later
    }
    
    return JsonResponse(manifest_data, json_dumps_params={'indent': 2})

@require_GET
def offline(request):
    """Offline fallback page"""
    return render(request, 'offline.html')


#notifications views 
@login_required
def notifications_list(request):
    """Get user notifications with filtering - includes both user-specific and admin broadcast notifications"""
    # Get filter parameters
    filter_type = request.GET.get('type', 'all')
    show_read = request.GET.get('show_read', 'false') == 'true'
    
    # === USER-SPECIFIC NOTIFICATIONS ===
    notifications_query = request.user.notifications.all()
    
    # Apply filters
    if not show_read:
        notifications_query = notifications_query.filter(is_read=False)
    
    if filter_type != 'all':
        notifications_query = notifications_query.filter(notification_type=filter_type)
    
    # Exclude expired notifications
    notifications_query = notifications_query.exclude(
        expires_at__lt=timezone.now()
    )
    
    # Get user notifications
    user_notifications = list(notifications_query[:20])
    
    # === ADMIN BROADCAST NOTIFICATIONS ===
    # Get active admin notifications that are scheduled to show
    admin_notifications = AdminNotification.objects.filter(
        is_active=True,
        scheduled_time__lte=timezone.now()
    ).order_by('-scheduled_time')[:10]
    
    # === CALCULATE UNREAD COUNT ===
    # Count user-specific unread notifications
    user_unread_count = request.user.notifications.filter(
        is_read=False
    ).exclude(
        expires_at__lt=timezone.now()
    ).count()
    
    # Count active admin notifications (always considered "unread")
    admin_unread_count = admin_notifications.count()
    
    # Total unread count (user notifications + admin notifications)
    total_unread_count = user_unread_count + admin_unread_count
    
    # Combine and format notifications
    notification_data = []
    
    # Add user-specific notifications
    for notification in user_notifications:
        notification_data.append({
            'id': notification.id,
            'title': notification.title,
            'message': notification.message,
            'link': notification.link,
            'is_read': notification.is_read,
            'created_at': notification.created_at.strftime('%b %d, %Y at %I:%M %p'),
            'type': notification.notification_type,
            'priority': notification.priority,
            'source': 'user',  # Mark as user-specific notification
            'is_admin': False
        })
    
    # Add admin broadcast notifications
    for notification in admin_notifications:
        notification_data.append({
            'id': f'admin_{notification.id}',
            'title': notification.title,
            'message': notification.body,
            'link': notification.link or '#',
            'is_read': False,  # Admin notifications are always shown as new
            'created_at': notification.scheduled_time.strftime('%b %d, %Y at %I:%M %p'),
            'type': 'announcement',  # Set type as announcement
            'priority': 'high',
            'source': 'admin',  # Mark as admin notification
            'is_admin': True
        })
    
    # Sort combined notifications by creation date (newest first)
    notification_data.sort(
        key=lambda x: timezone.datetime.strptime(x['created_at'], '%b %d, %Y at %I:%M %p'),
        reverse=True
    )
    
    # Limit to 20 total notifications
    notification_data = notification_data[:20]
    
    return JsonResponse({
        'notifications': notification_data,
        'unread_count': total_unread_count,  # This now includes both user and admin notifications
        'user_unread_count': user_unread_count,
        'admin_unread_count': admin_unread_count,
        'total_count': len(notification_data)
    })

@login_required
def mark_notification_read(request, notification_id):
    """Mark a user-specific notification as read"""
    if request.method == 'POST':
        try:
            # Check if it's an admin notification (can't mark as read)
            if str(notification_id).startswith('admin_'):
                return JsonResponse({
                    'status': 'info',
                    'message': 'Admin notifications cannot be marked as read'
                })
            
            notification = get_object_or_404(
                UserNotification, 
                id=notification_id, 
                user=request.user
            )
            notification.mark_as_read()
            
            # Recalculate total unread count
            user_unread = request.user.notifications.filter(
                is_read=False
            ).exclude(
                expires_at__lt=timezone.now()
            ).count()
            
            # Count active admin notifications
            admin_unread = AdminNotification.objects.filter(
                is_active=True,
                scheduled_time__lte=timezone.now()
            ).count()
            
            total_unread = user_unread + admin_unread
            
            return JsonResponse({
                'status': 'success',
                'unread_count': total_unread
            })
        except Exception as e:
            return JsonResponse({
                'status': 'error', 
                'message': str(e)
            }, status=400)
    
    return JsonResponse({
        'status': 'error', 
        'message': 'Invalid request'
    }, status=400)

@login_required
def mark_all_notifications_read(request):
    """Mark all user-specific notifications as read"""
    if request.method == 'POST':
        request.user.notifications.filter(is_read=False).update(is_read=True)
        
        # Count remaining admin notifications for badge
        admin_unread = AdminNotification.objects.filter(
            is_active=True,
            scheduled_time__lte=timezone.now()
        ).count()
        
        return JsonResponse({
            'status': 'success', 
            'unread_count': admin_unread  # Only admin notifications remain "unread"
        })
    
    return JsonResponse({
        'status': 'error', 
        'message': 'Invalid request'
    }, status=400)

@login_required
def delete_notification(request, notification_id):
    """Delete a specific user notification"""
    if request.method == 'POST':
        try:
            # Check if it's an admin notification (can't delete)
            if str(notification_id).startswith('admin_'):
                return JsonResponse({
                    'status': 'error',
                    'message': 'Admin notifications cannot be deleted'
                }, status=400)
            
            notification = get_object_or_404(
                UserNotification, 
                id=notification_id, 
                user=request.user
            )
            notification.delete()
            
            # Recalculate total unread count
            user_unread = request.user.notifications.filter(
                is_read=False
            ).exclude(
                expires_at__lt=timezone.now()
            ).count()
            
            # Count active admin notifications
            admin_unread = AdminNotification.objects.filter(
                is_active=True,
                scheduled_time__lte=timezone.now()
            ).count()
            
            total_unread = user_unread + admin_unread
            
            return JsonResponse({
                'status': 'success',
                'unread_count': total_unread
            })
        except Exception as e:
            return JsonResponse({
                'status': 'error', 
                'message': str(e)
            }, status=400)
    
    return JsonResponse({
        'status': 'error', 
        'message': 'Invalid request'
    }, status=400)

@login_required
def clear_all_notifications(request):
    """Clear all read user notifications"""
    if request.method == 'POST':
        request.user.notifications.filter(is_read=True).delete()
        
        # Recalculate total unread count
        user_unread = request.user.notifications.filter(
            is_read=False
        ).exclude(
            expires_at__lt=timezone.now()
        ).count()
        
        # Count active admin notifications
        admin_unread = AdminNotification.objects.filter(
            is_active=True,
            scheduled_time__lte=timezone.now()
        ).count()
        
        total_unread = user_unread + admin_unread
        
        return JsonResponse({
            'status': 'success',
            'unread_count': total_unread
        })
    
    return JsonResponse({
        'status': 'error', 
        'message': 'Invalid request'
    }, status=400)

@login_required
def my_purchases(request):
    """
    Display all purchased products for the authenticated user.
    """
    user = request.user
    
    # Get all active course access records for the user
    course_access_records = UserCourseAccess.objects.filter(
        user=user,
        is_active=True
    ).select_related('payment').order_by('-access_granted_at')
    
    # Organize purchases by type
    purchases = {
        'video_courses': [],
        'live_classes': [],
        'test_series': [],
        'elibrary_courses': [],
        'bundles': []
    }
    
    # Collect IDs by type
    video_course_ids = []
    live_class_ids = []
    test_series_ids = []
    elibrary_ids = []
    bundle_ids = []
    
    for access in course_access_records:
        if access.course_type == 'video_course':
            video_course_ids.append(access.course_id)
        elif access.course_type == 'live_class':
            live_class_ids.append(access.course_id)
        elif access.course_type == 'test_series':
            test_series_ids.append(access.course_id)
        elif access.course_type == 'elibrary':
            elibrary_ids.append(access.course_id)
        elif access.course_type == 'bundle':
            bundle_ids.append(access.course_id)
    
    # Fetch actual course objects
    if video_course_ids:
        from video_courses.models import VideoCourse
        video_courses = VideoCourse.objects.filter(id__in=video_course_ids)
        # Create a mapping for quick lookup
        video_courses_dict = {vc.id: vc for vc in video_courses}
        
        for access_record in course_access_records:
            if access_record.course_type == 'video_course':
                course = video_courses_dict.get(access_record.course_id)
                if course:  # Only add if course exists
                    purchases['video_courses'].append({
                        'course': course,
                        'access_granted': access_record.access_granted_at,
                        'payment': access_record.payment,
                        'expires_at': access_record.expires_at,
                    })
    
    if live_class_ids:
        from live_class.models import LiveClassCourse
        live_classes = LiveClassCourse.objects.filter(id__in=live_class_ids)
        live_classes_dict = {lc.id: lc for lc in live_classes}
        
        for access_record in course_access_records:
            if access_record.course_type == 'live_class':
                course = live_classes_dict.get(access_record.course_id)
                if course:
                    purchases['live_classes'].append({
                        'course': course,
                        'access_granted': access_record.access_granted_at,
                        'payment': access_record.payment,
                        'expires_at': access_record.expires_at,
                    })
    
    if test_series_ids:
        from exam.models import TestSeries
        test_series = TestSeries.objects.filter(id__in=test_series_ids)
        test_series_dict = {ts.id: ts for ts in test_series}
        
        for access_record in course_access_records:
            if access_record.course_type == 'test_series':
                course = test_series_dict.get(access_record.course_id)
                if course:
                    purchases['test_series'].append({
                        'course': course,
                        'access_granted': access_record.access_granted_at,
                        'payment': access_record.payment,
                        'expires_at': access_record.expires_at,
                    })
    
    if elibrary_ids:
        from elibrary.models import ELibraryCourse
        elibrary_courses = ELibraryCourse.objects.filter(id__in=elibrary_ids)
        elibrary_dict = {ec.id: ec for ec in elibrary_courses}
        
        for access_record in course_access_records:
            if access_record.course_type == 'elibrary':
                course = elibrary_dict.get(access_record.course_id)
                if course:
                    purchases['elibrary_courses'].append({
                        'course': course,
                        'access_granted': access_record.access_granted_at,
                        'payment': access_record.payment,
                        'expires_at': access_record.expires_at,
                    })
    
    if bundle_ids:
        from bundle.models import ProductBundle
        bundles = ProductBundle.objects.filter(id__in=bundle_ids)
        bundles_dict = {b.id: b for b in bundles}
        
        for access_record in course_access_records:
            if access_record.course_type == 'bundle':
                bundle = bundles_dict.get(access_record.course_id)
                if bundle:
                    purchases['bundles'].append({
                        'course': bundle,
                        'access_granted': access_record.access_granted_at,
                        'payment': access_record.payment,
                        'expires_at': access_record.expires_at,
                    })
    
    # Calculate total spent
    total_spent = sum(
        access.payment.amount / 100 if access.payment else 0 
        for access in course_access_records
    )
    
    # Count total purchases
    total_purchases = len(course_access_records)
    
    context = {
        'purchases': purchases,
        'total_spent': total_spent,
        'total_purchases': total_purchases,
    }
    
    return render(request, 'my_purchases.html', context)




def home(request):
    """
    Homepage view with AGGRESSIVE deduplication and purchase status.
    No prefetch_related or select_related on problematic models.
    """
    now = timezone.now()
    user = request.user

    # ===== Video Courses (ULTRA CLEAN - NO JOINS) ===== 
    video_course_ids = list(
        VideoCourse.objects
        .values_list('id', flat=True)
        .order_by('-created_at')[:10]
    )
    
    # Remove duplicates at Python level (preserves order)
    video_course_ids = list(dict.fromkeys(video_course_ids))
    
    video_courses = list(
        VideoCourse.objects
        .filter(id__in=video_course_ids)
        .order_by('-created_at')
    )
    
    # Get user's purchased video courses if authenticated
    purchased_video_course_ids = set()
    if user.is_authenticated:
        purchased_video_course_ids = set(
            UserCourseAccess.objects
            .filter(
                user=user,
                course_type='video_course',
                is_active=True
            )
            .values_list('course_id', flat=True)
        )
    
    # Additional Python-level deduplication
    seen_vc_ids = set()
    unique_video_courses = []
    for vc in video_courses:
        if vc.id not in seen_vc_ids:
            seen_vc_ids.add(vc.id)
            vc.original_price_display = f"{vc.original_price:.2f}"
            vc.selling_price_display = f"{vc.selling_price:.2f}"
            # Check if user has purchased this course
            vc.is_purchased = vc.id in purchased_video_course_ids
            unique_video_courses.append(vc)
    
    video_courses = unique_video_courses

    # ===== Live Classes (ULTRA CLEAN - NO PREFETCH) ===== 
    live_class_ids = list(
        LiveClassCourse.objects
        .filter(is_active=True)
        .values_list('id', flat=True)
        .order_by('-created_at')[:10]
    )
    
    # Remove duplicates at Python level
    live_class_ids = list(dict.fromkeys(live_class_ids))
    
    # Fetch WITHOUT any prefetch to avoid JOIN duplication
    live_classes = list(
        LiveClassCourse.objects
        .filter(id__in=live_class_ids)
        .order_by('-created_at')
    )
    
    # Get user's purchased live classes if authenticated
    purchased_live_class_ids = set()
    if user.is_authenticated:
        purchased_live_class_ids = set(
            UserCourseAccess.objects
            .filter(
                user=user,
                course_type='live_class',
                is_active=True
            )
            .values_list('course_id', flat=True)
        )
    
    # Additional Python-level deduplication + fetch sessions separately
    seen_lc_ids = set()
    unique_live_classes = []
    
    for course in live_classes:
        if course.id not in seen_lc_ids:
            seen_lc_ids.add(course.id)
            
            # Fetch sessions SEPARATELY to avoid JOIN duplication
            upcoming_sessions = list(
                LiveClassSession.objects
                .filter(
                    course_id=course.id,
                    scheduled_datetime__gte=now
                )
                .order_by('scheduled_datetime')[:2]
            )
            
            course.next_sessions = upcoming_sessions
            
            # Handle pricing display based on is_free field
            if course.is_free:
                course.original_price_display = "0.00"
                course.current_price_display = "FREE"
                course.price_display_text = "FREE"
                course.show_price_strike = False
            else:
                course.original_price_display = f"{course.original_price:.2f}"
                course.current_price_display = f"{course.current_price:.2f}"
                course.price_display_text = f"₹{course.current_price:.2f}"
                course.show_price_strike = course.original_price != course.current_price
            
            course.language_display = course.language
            # Check if user has purchased this course
            course.is_purchased = course.id in purchased_live_class_ids
            
            if course.about:
                course.about_short = (
                    course.about[:140] + '...' if len(course.about) > 140 else course.about
                )
            else:
                course.about_short = ""
            
            unique_live_classes.append(course)
    
    live_classes = unique_live_classes

    # ===== Test Series (Keep as is - working correctly) ===== 
    test_series_ids = list(
        TestSeries.objects
        .filter(is_active=True)
        .values_list('id', flat=True)
        .distinct()
        .order_by('-created_at')[:10]
    )
    
    test_series = list(
        TestSeries.objects
        .filter(id__in=test_series_ids)
        .prefetch_related(
            Prefetch(
                'tests',
                queryset=Test.objects
                .filter(is_active=True)
                .prefetch_related('questions')
                .annotate(
                    question_count=Count('questions', distinct=True),
                    total_marks_sum=Sum('questions__marks')
                ),
                to_attr='active_tests_list'
            )
        )
        .select_related('category')
        .order_by('-created_at')
    )
    
    # Get user's purchased test series if authenticated
    purchased_test_series_ids = set()
    if user.is_authenticated:
        purchased_test_series_ids = set(
            UserCourseAccess.objects
            .filter(
                user=user,
                course_type='test_series',
                is_active=True
            )
            .values_list('course_id', flat=True)
        )

    for series in test_series:
        series.total_tests = len(series.active_tests_list)
        series.total_questions = sum(
            test.question_count for test in series.active_tests_list
        )
        series.total_marks = sum(
            test.total_marks_sum or 0 for test in series.active_tests_list
        )
        series.free_tests = sum(
            1 for test in series.active_tests_list if series.is_free
        )
        series.user_count = 0
        series.price_display = "FREE" if series.is_free else f"₹{series.price:.2f}"
        # Check if user has purchased this test series
        series.is_purchased = series.id in purchased_test_series_ids

        
    # ===== E-Library Courses (ULTRA CLEAN) ===== 
    elibrary_ids = list(
        ELibraryCourse.objects
        .filter(is_active=True)
        .values_list('id', flat=True)
        .order_by('-created_at')[:10]
    )
    
    # Remove duplicates at Python level
    elibrary_ids = list(dict.fromkeys(elibrary_ids))
    
    elibrary_courses = list(
        ELibraryCourse.objects
        .filter(id__in=elibrary_ids)
        .order_by('-created_at')
    )
    
    # Get user's purchased elibrary courses if authenticated
    purchased_elibrary_ids = set()
    if user.is_authenticated:
        purchased_elibrary_ids = set(
            UserCourseAccess.objects
            .filter(
                user=user,
                course_type='elibrary',
                is_active=True
            )
            .values_list('course_id', flat=True)
        )
    
    # Additional Python-level deduplication
    seen_el_ids = set()
    unique_elibrary = []
    
    for course in elibrary_courses:
        if course.id not in seen_el_ids:
            seen_el_ids.add(course.id)
            course.price_display = f"₹{course.current_price:.2f}"
            # Check if user has purchased this course
            course.is_purchased = course.id in purchased_elibrary_ids
            
            if hasattr(course, 'short_description') and course.short_description:
                course.short_desc = (
                    course.short_description[:100] + '...' 
                    if len(course.short_description) > 100 
                    else course.short_description
                )
            else:
                course.short_desc = ""
            
            unique_elibrary.append(course)
    
    elibrary_courses = unique_elibrary
    
    # ===== Product Bundles (WITH PURCHASE STATUS) ===== 
    bundle_ids = list(
        ProductBundle.objects
        .filter(status='active')
        .values_list('id', flat=True)
        .distinct()
        .order_by('display_order', '-created_at')[:6]
    )
    
    product_bundles = list(
        ProductBundle.objects
        .filter(id__in=bundle_ids)
        .prefetch_related(
            Prefetch('video_courses', to_attr='video_courses_list'),
            Prefetch('live_classes', to_attr='live_classes_list'),
            Prefetch('test_series', to_attr='test_series_list'),
            Prefetch('elibrary_courses', to_attr='elibrary_courses_list')
        )
        .order_by('display_order', '-created_at')
    )
    
    # Get user's purchased bundles if authenticated
    purchased_bundle_ids = set()
    if user.is_authenticated:
        purchased_bundle_ids = set(
            UserCourseAccess.objects
            .filter(
                user=user,
                course_type='bundle',
                is_active=True
            )
            .values_list('course_id', flat=True)
        )
    
    for bundle in product_bundles:
        bundle.discount_percent = bundle.discount_percentage
        bundle.savings = bundle.original_price - bundle.bundle_price
        # Check if user has purchased this bundle
        bundle.is_purchased = bundle.id in purchased_bundle_ids
        
        if hasattr(bundle, 'features') and bundle.features:
            features_list = [f.strip() for f in bundle.features.split('\n') if f.strip()]
            bundle.features_list = features_list[:3]
        else:
            bundle.features_list = []
            
        bundle.price_display = f"{bundle.bundle_price:.2f}"
        bundle.original_price_display = f"{bundle.original_price:.2f}"
    
    # ===== Build Context =====
    context = {
        'live_classes': live_classes,
        'video_courses': video_courses,
        'test_series': test_series,
        'featured_courses': elibrary_courses,
        'product_bundles': product_bundles,
        'now': now,
    }
    
    return render(request, 'base.html', context)


def product_bundle_detail(request, slug):
    """Display detailed view of a specific product bundle with purchase status"""
    try:
        bundle = get_object_or_404(
            ProductBundle.objects.prefetch_related(
                'video_courses',
                'live_classes',
                'test_series',
                'elibrary_courses',
                'category'
            ),
            slug=slug
            # Removed status='active' filter to debug
        )
        
        # DEBUG: Log bundle status
        logger.info(f"Bundle: {bundle.title}")
        logger.info(f"Status: {bundle.status}")
        logger.info(f"is_available: {bundle.is_available}")
        
        # DEBUG: Check why not available
        now = timezone.now().date()
        if bundle.start_date:
            logger.info(f"Start date: {bundle.start_date}, Today: {now}, Start in future: {now < bundle.start_date}")
        if bundle.end_date:
            logger.info(f"End date: {bundle.end_date}, Today: {now}, Ended: {now > bundle.end_date}")
        if bundle.max_enrollments:
            logger.info(f"Max enrollments: {bundle.max_enrollments}, Current: {bundle.current_enrollments}")
        
        # Increment view count
        bundle.total_views += 1
        bundle.save(update_fields=['total_views'])
        
        # Get all products in the bundle
        video_courses = bundle.video_courses.all()
        live_classes = bundle.live_classes.all()
        test_series_list = bundle.test_series.prefetch_related('tests__questions').all()
        elibrary_courses = bundle.elibrary_courses.all()
        
        # Calculate test series stats
        for series in test_series_list:
            active_tests = series.tests.filter(is_active=True)
            series.total_tests = active_tests.count()
            series.total_questions = sum(test.questions.count() for test in active_tests)
        
        # ===== DEFAULT CONTEXT =====
        context = {
            'bundle': bundle,
            'video_courses': video_courses,
            'live_classes': live_classes,
            'test_series_list': test_series_list,
            'elibrary_courses': elibrary_courses,
            'discount_percent': bundle.discount_percentage,
            'savings': bundle.savings_amount,
            'features_list': bundle.get_features_list(),
            'is_available': bundle.is_available,
            'price_display': f"₹{bundle.bundle_price:.2f}" if not bundle.is_free else "FREE",
            'original_price_display': f"₹{bundle.original_price:.2f}",
            # Purchase status
            'has_access': False,
            'is_purchased': False,
            'user_has_bundle': False,
            'access_expires_at': None,
        }
        
        # ===== CHECK USER PURCHASE STATUS =====
        if request.user.is_authenticated:
            try:
                # Check UserCourseAccess for bundle purchase
                access = UserCourseAccess.objects.get(
                    user=request.user,
                    course_id=bundle.id,
                    course_type='bundle'
                )
                
                # Check if access is still valid using the @property method
                if access.has_access:
                    context['has_access'] = True
                    context['is_purchased'] = True
                    context['user_has_bundle'] = True
                    context['access_expires_at'] = access.expires_at
                    
                    logger.info(f"User {request.user.id} has active access to bundle {bundle.id}")
                else:
                    # Access expired
                    context['has_access'] = False
                    context['is_purchased'] = False
                    context['user_has_bundle'] = False
                    
                    logger.info(f"User {request.user.id} access to bundle {bundle.id} has expired")
                    
            except UserCourseAccess.DoesNotExist:
                # User hasn't purchased this bundle
                context['has_access'] = False
                context['is_purchased'] = False
                context['user_has_bundle'] = False
                
                logger.info(f"User {request.user.id} has not purchased bundle {bundle.id}")
        
        return render(request, 'bundles/product_bundle_detail.html', context)
    
    except ProductBundle.DoesNotExist:
        raise Http404("Bundle not found")


def test_series_detail(request, pk):
    """
    View test series details and tests with purchase status check.
    Similar to live_class_detail view.
    """
    try:
        # Get test series with related tests
        test_series = get_object_or_404(TestSeries, pk=pk, is_active=True)
        tests = test_series.tests.filter(is_active=True).prefetch_related('questions')
        
        # Format price displays
        if test_series.is_free:
            test_series.original_price_display = "0.00"
            test_series.current_price_display = "FREE"
            test_series.show_price_strike = False
        else:
            test_series.original_price_display = f"{test_series.price:.2f}"
            test_series.current_price_display = f"{test_series.price:.2f}"
            test_series.show_price_strike = False  # Only show strike if you have original_price field
        
        # Add stats for each test
        for test in tests:
            test.question_count = test.questions.count()
            test.total_marks = sum(q.marks for q in test.questions.all())
            
            # Check if user has attempted this test
            if request.user.is_authenticated:
                test.user_attempts = TestAttempt.objects.filter(
                    user=request.user, 
                    test=test,
                    status='submitted'
                ).count()
                test.can_attempt = test.user_attempts < test.max_attempts
                
                # Get best score if available
                best_attempt = TestAttempt.objects.filter(
                    user=request.user,
                    test=test,
                    status='submitted'
                ).order_by('-marks_obtained').first()
                
                if best_attempt:
                    test.best_score = best_attempt.marks_obtained
                    test.best_percentage = best_attempt.percentage_score
                else:
                    test.best_score = None
                    test.best_percentage = None
            else:
                test.user_attempts = 0
                test.can_attempt = True
                test.best_score = None
                test.best_percentage = None
        
        # ===== DEFAULT CONTEXT =====
        context = {
            'test_series': test_series,
            'tests': tests,
            'is_purchased': False,  # Default: user hasn't purchased
        }
        
        # ===== CHECK PURCHASE STATUS FOR AUTHENTICATED USERS =====
        if request.user.is_authenticated:
            try:
                # Check if user has access to this test series
                access = UserCourseAccess.objects.get(
                    user=request.user,
                    course_id=pk,
                    course_type='test_series'
                )
                
                # Check if access is active
                if hasattr(access, 'is_active'):
                    if access.is_active:
                        context['is_purchased'] = True
                else:
                    # If no is_active field, just having the record means purchased
                    context['is_purchased'] = True
                    
            except UserCourseAccess.DoesNotExist:
                # User hasn't purchased this test series
                context['is_purchased'] = False
        
        return render(request, 'test_series_detail.html', context)
    
    except TestSeries.DoesNotExist:
        raise Http404("Test series not found")
    except Exception as e:
        raise Http404(f"Error loading test series: {str(e)}")

@login_required
def start_test(request, test_id):
    """Start a new test attempt"""
    test = get_object_or_404(Test, id=test_id, is_active=True)
    
    # Check if test is available
    if not test.is_available:
        messages.error(request, 'This test is not currently available.')
        return redirect('front_exam_series_detail', pk=test.test_series.pk)
    
    # Check if user can attempt this test
    user_attempts = TestAttempt.objects.filter(
        user=request.user, 
        test=test,
        status='submitted'
    ).count()
    
    if user_attempts >= test.max_attempts:
        messages.error(request, f'You have already used all {test.max_attempts} attempts for this test.')
        return redirect('front_exam_series_detail', pk=test.test_series.pk)
    
    # Check for incomplete attempts
    incomplete_attempt = TestAttempt.objects.filter(
        user=request.user,
        test=test,
        status__in=['started', 'in_progress']
    ).first()
    
    if incomplete_attempt:
        return redirect('front_exam_session', attempt_id=incomplete_attempt.id)
    
    # Get total marks for the test
    total_marks = test.questions.aggregate(Sum('marks'))['marks__sum'] or 0
    
    # Create new test attempt
    attempt = TestAttempt.objects.create(
        user=request.user,
        test=test,
        attempt_number=user_attempts + 1,
        total_questions=test.questions.count(),
        total_marks=total_marks,
        status='in_progress'
    )
    
    messages.success(request, f'Test started! You have {test.duration_minutes} minutes to complete.')
    return redirect('front_exam_session', attempt_id=attempt.id)


@login_required
def take_test(request, attempt_id):
    """Take test interface"""
    attempt = get_object_or_404(TestAttempt, id=attempt_id, user=request.user)
    
    if attempt.status == 'submitted':
        return redirect('front_exam_result', attempt_id=attempt.id)
    
    # Check if time expired
    elapsed_time = timezone.now() - attempt.started_at
    duration_seconds = attempt.test.duration_minutes * 60
    
    if elapsed_time.total_seconds() >= duration_seconds:
        # Auto-submit if time is up
        return redirect('front_exam_submit', attempt_id=attempt.id)
    
    questions = attempt.test.questions.all().order_by('order')
    
    # Shuffle questions if enabled
    if attempt.test.shuffle_questions:
        questions = list(questions)
        import random
        random.seed(attempt.id.int)  # Use attempt ID as seed for consistency
        random.shuffle(questions)
    
    # Calculate remaining time
    time_remaining = duration_seconds - int(elapsed_time.total_seconds())
    
    context = {
        'attempt': attempt,
        'test': attempt.test,
        'questions': questions,
        'time_remaining': max(0, time_remaining),
    }
    return render(request, 'take_test.html', context)


@login_required
def submit_test(request, attempt_id):
    """Submit test and calculate results"""
    attempt = get_object_or_404(TestAttempt, id=attempt_id, user=request.user)
    
    if attempt.status == 'submitted':
        messages.info(request, 'This test has already been submitted.')
        return redirect('front_exam_result', attempt_id=attempt.id)
    
    if request.method == 'POST':
        # Calculate time spent
        time_spent = timezone.now() - attempt.started_at
        attempt.time_spent = time_spent
        attempt.submitted_at = timezone.now()
        
        # Initialize counters
        correct_answers = 0
        wrong_answers = 0
        attempted_questions = 0
        marks_obtained = 0.0
        subject_wise_score = {}
        
        # Get all questions for this test
        questions = attempt.test.questions.all()
        
        # Process each question
        for question in questions:
            answer_key = f'question_{question.id}'
            
            # Get student's answer from POST data
            if question.question_type == 'mcq_multiple':
                selected_answer = request.POST.getlist(answer_key)
            else:
                selected_answer = request.POST.get(answer_key, '')
            
            # Check if answered
            is_answered = bool(selected_answer) and not (isinstance(selected_answer, list) and len(selected_answer) == 0)
            
            # Skip if not answered - create empty record
            if not is_answered:
                StudentAnswer.objects.create(
                    attempt=attempt,
                    question=question,
                    selected_answer={},
                    is_correct=False,
                    marks_obtained=0,
                    is_attempted=False
                )
                continue
            
            attempted_questions += 1
            
            # Normalize answers for comparison
            if isinstance(selected_answer, list):
                student_answer = sorted([ans.lower().strip() for ans in selected_answer])
            else:
                student_answer = selected_answer.lower().strip()
            
            # Get correct answer
            correct_answer = question.correct_answer
            
            # Check if answer is correct
            is_correct = False
            question_marks = 0.0
            
            if question.question_type == 'mcq_multiple':
                # For multiple choice, compare as sorted lists
                if isinstance(correct_answer, dict) and 'answers' in correct_answer:
                    correct_list = sorted([ans.lower().strip() for ans in correct_answer['answers']])
                elif isinstance(correct_answer, list):
                    correct_list = sorted([ans.lower().strip() for ans in correct_answer])
                else:
                    correct_list = []
                
                is_correct = student_answer == correct_list
            
            elif question.question_type in ['mcq_single', 'true_false']:
                # For single choice
                if isinstance(correct_answer, dict) and 'answer' in correct_answer:
                    correct_value = correct_answer['answer'].lower().strip()
                elif isinstance(correct_answer, str):
                    correct_value = correct_answer.lower().strip()
                else:
                    correct_value = ''
                
                is_correct = student_answer == correct_value
            
            elif question.question_type in ['fill_blank', 'numerical']:
                # For text/numerical answers
                if isinstance(correct_answer, dict) and 'answer' in correct_answer:
                    correct_value = str(correct_answer['answer']).lower().strip()
                elif isinstance(correct_answer, str):
                    correct_value = correct_answer.lower().strip()
                else:
                    correct_value = ''
                
                is_correct = student_answer == correct_value
            
            # Calculate marks
            if is_correct:
                correct_answers += 1
                question_marks = float(question.marks)
            else:
                wrong_answers += 1
                # Apply negative marking if enabled
                if attempt.test.test_series.has_negative_marking:
                    question_marks = -float(question.negative_marks)
            
            marks_obtained += question_marks
            
            # Track subject-wise score
            if question.subject:
                subject_name = question.subject.name
                if subject_name not in subject_wise_score:
                    subject_wise_score[subject_name] = {
                        'correct': 0,
                        'wrong': 0,
                        'marks': 0.0
                    }
                
                if is_correct:
                    subject_wise_score[subject_name]['correct'] += 1
                else:
                    subject_wise_score[subject_name]['wrong'] += 1
                subject_wise_score[subject_name]['marks'] += question_marks
            
            # Save student answer with proper format
            StudentAnswer.objects.create(
                attempt=attempt,
                question=question,
                selected_answer={'answer': selected_answer} if not isinstance(selected_answer, list) else {'answers': selected_answer},
                is_correct=is_correct,
                marks_obtained=question_marks,
                is_attempted=True,  # Fixed: Set is_attempted flag
                answered_at=timezone.now()  # Fixed: Set answered timestamp
            )
            
            # Update question analytics
            question.total_attempts += 1
            if is_correct:
                question.correct_attempts += 1
            question.save(update_fields=['total_attempts', 'correct_attempts'])
        
        # Calculate percentage
        percentage_score = 0
        if attempt.total_marks > 0:
            percentage_score = (marks_obtained / float(attempt.total_marks)) * 100
        
        # Update attempt with results
        attempt.status = 'submitted'
        attempt.attempted_questions = attempted_questions
        attempt.correct_answers = correct_answers
        attempt.wrong_answers = wrong_answers
        attempt.marks_obtained = marks_obtained
        attempt.percentage_score = max(0, percentage_score)
        attempt.subject_wise_score = subject_wise_score
        attempt.save()
        
        # Update test series analytics
        test_series = attempt.test.test_series
        test_series.total_attempts += 1
        
        # Recalculate average score
        all_attempts = TestAttempt.objects.filter(
            test__test_series=test_series,
            status='submitted'
        )
        if all_attempts.exists():
            avg_score = all_attempts.aggregate(avg=Sum('marks_obtained'))['avg'] or 0
            test_series.average_score = avg_score / all_attempts.count() if all_attempts.count() > 0 else 0
        
        test_series.save()
        
        messages.success(request, 'Test submitted successfully!')
        return redirect('front_exam_result', attempt_id=attempt.id)
    
    # If GET request, just redirect to result
    return redirect('front_exam_result', attempt_id=attempt.id)



@login_required
def test_result(request, attempt_id):
    """Show test results"""
    attempt = get_object_or_404(TestAttempt, id=attempt_id, user=request.user)
    
    if attempt.status != 'submitted':
        messages.warning(request, 'Please submit the test first to see results.')
        return redirect('front_exam_session', attempt_id=attempt.id)
    
    # Calculate skipped questions
    skipped_questions = attempt.total_questions - attempt.attempted_questions
    
    # Get all answers for review (if allowed)
    student_answers = None
    if attempt.test.allow_review:
        student_answers = StudentAnswer.objects.filter(
            attempt=attempt
        ).select_related('question', 'question__subject')
    
    context = {
        'attempt': attempt,
        'test': attempt.test,
        'skipped_questions': skipped_questions,
        'student_answers': student_answers,
    }
    return render(request, 'test_result.html', context)

@login_required
def review_answers(request, attempt_id):
    """Review test answers with correct solutions"""
    attempt = get_object_or_404(TestAttempt, id=attempt_id, user=request.user)
    
    # Check if review is allowed
    if not attempt.test.allow_review:
        messages.error(request, 'Answer review is not available for this test.')
        return redirect('front_exam_result', attempt_id=attempt.id)
    
    if attempt.status != 'submitted':
        messages.warning(request, 'Please submit the test first to review answers.')
        return redirect('front_exam_session', attempt_id=attempt.id)
    
    # Get all student answers with related question data
    student_answers = StudentAnswer.objects.filter(
        attempt=attempt
    ).select_related(
        'question', 
        'question__subject'
    ).order_by('question__order')
    
    # Prepare answers with additional context
    answers_with_context = []
    for student_answer in student_answers:
        question = student_answer.question
        
        # Format correct answer display with full option text
        correct_answer_display = "No correct answer set"
        if question.correct_answer and isinstance(question.correct_answer, dict):
            if question.question_type in ['mcq_single', 'true_false']:
                if 'answer' in question.correct_answer and question.correct_answer['answer']:
                    answer_key = str(question.correct_answer['answer']).lower()
                    if question.options and answer_key in question.options:
                        # Show both key and option text
                        correct_answer_display = f"{answer_key.upper()}. {question.options[answer_key]}"
                    else:
                        correct_answer_display = f"{answer_key.upper()}. (Option text missing)"
            
            elif question.question_type == 'mcq_multiple':
                if 'answers' in question.correct_answer and question.correct_answer['answers']:
                    answer_keys = question.correct_answer['answers']
                    if question.options:
                        # Show all correct options with text
                        option_displays = []
                        for key in answer_keys:
                            key_lower = str(key).lower()
                            if key_lower in question.options:
                                option_displays.append(f"{key_lower.upper()}. {question.options[key_lower]}")
                            else:
                                option_displays.append(f"{key_lower.upper()}. (Option text missing)")
                        correct_answer_display = ', '.join(option_displays)
                    else:
                        correct_answer_display = ', '.join([str(key).upper() for key in answer_keys])
            
            elif question.question_type in ['fill_blank', 'numerical']:
                correct_answer_display = str(question.correct_answer.get('answer', 'N/A'))
        
        # Format student answer display with full option text - THIS IS THE KEY FIX
        student_answer_display = "Not Attempted"
        if student_answer.is_attempted and student_answer.selected_answer:
            if isinstance(student_answer.selected_answer, dict):
                # Single answer (MCQ single, True/False, Fill blank, Numerical)
                if 'answer' in student_answer.selected_answer and student_answer.selected_answer['answer']:
                    answer_value = student_answer.selected_answer['answer']
                    
                    if question.question_type in ['mcq_single', 'true_false']:
                        # For MCQ, show key + option text
                        answer_key = str(answer_value).lower()
                        
                        # Check if options exist and the key is in options
                        if question.options and isinstance(question.options, dict):
                            if answer_key in question.options:
                                student_answer_display = f"{answer_key.upper()}. {question.options[answer_key]}"
                            else:
                                student_answer_display = f"{answer_key.upper()}. (Option text not found)"
                        else:
                            student_answer_display = f"{answer_key.upper()}. (No options available)"
                    
                    elif question.question_type in ['fill_blank', 'numerical']:
                        # For text/numerical, just show the answer
                        student_answer_display = str(answer_value)
                
                # Multiple answers (MCQ multiple)
                elif 'answers' in student_answer.selected_answer and student_answer.selected_answer['answers']:
                    answer_keys = student_answer.selected_answer['answers']
                    
                    if question.options and isinstance(question.options, dict):
                        # Show all selected options with text
                        option_displays = []
                        for key in answer_keys:
                            key_lower = str(key).lower()
                            if key_lower in question.options:
                                option_displays.append(f"{key_lower.upper()}. {question.options[key_lower]}")
                            else:
                                option_displays.append(f"{key_lower.upper()}. (Option text not found)")
                        student_answer_display = ', '.join(option_displays)
                    else:
                        student_answer_display = ', '.join([str(key).upper() for key in answer_keys])
        
        answers_with_context.append({
            'student_answer': student_answer,
            'question': question,
            'correct_answer_display': correct_answer_display,
            'student_answer_display': student_answer_display,
        })
    
    # Calculate skipped questions
    skipped_questions = attempt.total_questions - attempt.attempted_questions
    
    # Subject-wise analysis
    subject_analysis = []
    if attempt.subject_wise_score:
        for subject_name, scores in attempt.subject_wise_score.items():
            subject_analysis.append({
                'name': subject_name,
                'correct': scores.get('correct', 0),
                'wrong': scores.get('wrong', 0),
                'marks': scores.get('marks', 0),
            })
    
    context = {
        'attempt': attempt,
        'test': attempt.test,
        'answers_with_context': answers_with_context,
        'skipped_questions': skipped_questions,
        'subject_analysis': subject_analysis,
    }
    
    # Mark as reviewed
    if not attempt.is_reviewed:
        attempt.is_reviewed = True
        attempt.save(update_fields=['is_reviewed'])
    
    return render(request, 'review_answers.html', context)







def live_class_detail(request, pk):
    """
    Public view for displaying live class details with purchase status check.
    Shows "Already Enrolled" if user has purchased the course.
    """
    try:
        now = timezone.now()
        
        # Get the live class with related sessions
        course = LiveClassCourse.objects.prefetch_related('sessions').get(
            pk=pk, 
            is_active=True
        )
        
        # Format price displays
        if course.is_free:
            course.original_price_display = "0.00"
            course.current_price_display = "FREE"
        else:
            course.original_price_display = f"₹{course.original_price:.2f}"
            course.current_price_display = f"₹{course.current_price:.2f}"
        
        # Get next sessions
        next_sessions = [s for s in course.sessions.all() if s.scheduled_datetime >= now]
        course.next_sessions = sorted(next_sessions, key=lambda s: s.scheduled_datetime)[:10]
        
        # Get all sessions for schedule display
        all_sessions = course.sessions.all().order_by('scheduled_datetime')
        
        # Calculate total sessions and free sessions
        total_sessions = all_sessions.count()
        free_sessions = all_sessions.filter(is_free=True).count()
        
        # ===== DEFAULT CONTEXT =====
        context = {
            'course': course,
            'next_sessions': course.next_sessions,
            'all_sessions': all_sessions,
            'total_sessions': total_sessions,
            'free_sessions': free_sessions,
            'now': now,
            'is_purchased': False,  # Default: user hasn't purchased
        }
        
        # ===== CHECK PURCHASE STATUS FOR AUTHENTICATED USERS =====
        if request.user.is_authenticated:
            try:
                # Check if user has access to this course
                access = UserCourseAccess.objects.get(
                    user=request.user,
                    course_id=pk,
                    course_type='live_class'
                )
                
                # Check if access is active (if is_active field exists)
                if hasattr(access, 'is_active'):
                    if access.is_active:
                        context['is_purchased'] = True
                else:
                    # If no is_active field, just having the record means purchased
                    context['is_purchased'] = True
                    
            except UserCourseAccess.DoesNotExist:
                # User hasn't purchased this course
                context['is_purchased'] = False
        
        return render(request, 'live_class_detail.html', context)
    
    except LiveClassCourse.DoesNotExist:
        raise Http404("Live class not found")




def video_course_detail(request, pk):
    """
    Public view for displaying video course details with purchase status check
    """
    try:
        # Optimized query with prefetch_related
        course = VideoCourse.objects.prefetch_related(
            'videos', 
            'learn_points', 
            'includes'
        ).get(pk=pk)
        
        # Format price displays
        course.original_price_display = f"{course.original_price:.2f}"
        course.selling_price_display = f"{course.selling_price:.2f}"
        
        # Get related videos with duration formatting
        videos = course.videos.all()
        for video in videos:
            # Convert seconds to MM:SS format
            if video.duration_seconds and video.duration_seconds > 0:
                minutes = video.duration_seconds // 60
                seconds = video.duration_seconds % 60
                video.duration_display = f"{minutes}:{seconds:02d}"
            else:
                video.duration_display = "--:--"
        
        # Get learn points and includes
        learn_points = course.learn_points.all()
        includes = course.includes.all()
        
        # ===== DEFAULT CONTEXT =====
        context = {
            'course': course,
            'videos': videos,
            'learn_points': learn_points,
            'includes': includes,
            'has_access': False,
            'is_purchased': False,
            'access_expires_at': None,
        }
        
        # ===== CHECK USER PURCHASE STATUS =====
        if request.user.is_authenticated:
            try:
                # Get user's course access
                access = UserCourseAccess.objects.get(
                    user=request.user,
                    course_id=pk,
                    course_type='video_course'
                )
                
                # Check if access is still valid using the @property method
                if access.has_access:
                    context['has_access'] = True
                    context['is_purchased'] = True
                    context['access_expires_at'] = access.expires_at
                else:
                    # Access expired
                    context['has_access'] = False
                    context['is_purchased'] = False
                    
            except UserCourseAccess.DoesNotExist:
                # User hasn't purchased this course
                context['has_access'] = False
                context['is_purchased'] = False
        
        return render(request, 'video_course_detail.html', context)
    
    except VideoCourse.DoesNotExist:
        raise Http404("Course not found")


def loginuser(request):
    """Render the login page (static)."""
    return render(request, "login.html")


# base/views.py (add these imports and views)


def login_view(request):
    """Handle user login with 'remember me'"""
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()  # Normalize email
        password = request.POST.get('password', '')
        remember = request.POST.get('remember')
        
        
        if not email or not password:
            messages.error(request, 'Please enter both email and password.')
            return render(request, 'login.html')
        
        # Check if user exists first
        try:
            user_exists = User.objects.filter(email__iexact=email).exists()
        except Exception as e:
            print(f"Database error: {e}")
            messages.error(request, 'An error occurred. Please try again.')
            return render(request, 'login.html')
        
        if not user_exists:
            messages.error(request, 'No account found with this email.')
            return render(request, 'login.html')
        
        # Authenticate user
        user = authenticate(request, username=email, password=password)
        
        if user is not None:
            if user.is_active:
                login(request, user)
                
                # Remember Me functionality
                if remember:
                    request.session.set_expiry(2592000)  # 30 days
                else:
                    request.session.set_expiry(0)  # until browser closes
                
                messages.success(request, f'Welcome back, {user.get_full_name_or_email()}!')
                
                # Redirect to 'next' if present
                next_url = request.POST.get('next') or request.GET.get('next') or 'home'
                return redirect(next_url)
            else:
                messages.error(request, 'Your account is disabled.')
        else:
            messages.error(request, 'Incorrect password. Please try again.')
    
    return render(request, 'login.html')



@require_http_methods(["POST"])
def forgot_password_request(request):
    """Send OTP via email for password reset"""
    email = request.POST.get('email', '').strip()
    
    if not email:
        return JsonResponse({'success': False, 'message': 'Email is required'})
    
    # Check if user exists
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'No account found with this email address. Please check and try again.'
        })
    
    # Check if SMTP is configured and tested
    smtp_config = SMTPConfiguration.objects.filter(is_active=True).first()
    
    if not smtp_config:
        return JsonResponse({
            'success': False,
            'message': 'Email service is not configured. Please contact administrator to configure SMTP first.'
        })
    
    # Check if SMTP has been tested successfully
    if smtp_config.test_status != 'success':
        return JsonResponse({
            'success': False,
            'message': 'Email service has not been tested or configured properly. Please contact administrator.'
        })
    
    # Generate OTP
    def generate_otp(length=6):
        """Generate a random 6-digit OTP"""
        return ''.join(secrets.choice(string.digits) for _ in range(length))
    
    # Generate and save OTP
    otp_code = generate_otp()
    
    # Delete any existing unused OTPs for this user
    OTPVerification.objects.filter(
        user=user,
        verification_type='password_reset',
        is_used=False
    ).delete()
    
    # Create new OTP
    otp_instance = OTPVerification.objects.create(
        user=user,
        otp_code=otp_code,
        verification_type='password_reset',
        expires_at=timezone.now() + timezone.timedelta(minutes=10)
    )
    
    # Prepare email content
    email_subject = 'Password Reset OTP'
    email_message = f"""
Hello {user.first_name or user.username},

You have requested to reset your password.

Your OTP code is: {otp_code}

This OTP is valid for 10 minutes.

If you did not request this password reset, please ignore this email or contact support immediately.

Best regards,
Support Team
    """.strip()
    
    try:
        # Create SMTP connection
        connection = get_connection(
            backend=smtp_config.email_backend,
            host=smtp_config.email_host,
            port=smtp_config.email_port,
            username=smtp_config.email_host_user,
            password=smtp_config.email_host_password,
            use_tls=smtp_config.email_use_tls,
            use_ssl=smtp_config.email_use_ssl,
        )
        
        # Send email
        result = send_mail(
            subject=email_subject,
            message=email_message,
            from_email=smtp_config.default_from_email,
            recipient_list=[user.email],
            fail_silently=False,
            connection=connection
        )
        
        if result == 1:
            return JsonResponse({
                'success': True,
                'message': f'OTP has been sent to {email}. Please check your email.',
                'user_id': user.id
            })
        else:
            # Delete OTP if email fails
            otp_instance.delete()
            return JsonResponse({
                'success': False,
                'message': 'Failed to send email. Please try again later.'
            })
            
    except Exception as e:
        # Delete OTP if email fails
        otp_instance.delete()
        return JsonResponse({
            'success': False,
            'message': f'Failed to send email: {str(e)}'
        })


@require_http_methods(["POST"])
def verify_reset_otp(request):
    """Verify OTP for password reset"""
    user_id = request.POST.get('user_id')
    otp_code = request.POST.get('otp_code', '').strip()
    
    if not user_id or not otp_code:
        return JsonResponse({
            'success': False,
            'message': 'User ID and OTP code are required.'
        })
    
    try:
        user = User.objects.get(id=user_id)
        otp = OTPVerification.objects.filter(
            user=user,
            otp_code=otp_code,
            verification_type='password_reset',
            is_used=False
        ).first()
        
        if otp and otp.is_valid():
            # Mark OTP as used
            otp.is_used = True
            otp.save()
            
            # Store verification in session
            request.session['reset_user_id'] = user.id
            request.session['reset_verified'] = True
            request.session.set_expiry(600)  # Session expires in 10 minutes
            
            return JsonResponse({
                'success': True,
                'message': 'OTP verified successfully. Please create a new password.'
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Invalid or expired OTP. Please try again.'
            })
            
    except User.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'User not found.'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'An error occurred: {str(e)}'
        })


@require_http_methods(["POST"])
def reset_password(request):
    """Reset password after OTP verification"""
    # Check if OTP was verified
    if not request.session.get('reset_verified'):
        return JsonResponse({
            'success': False,
            'message': 'Please verify OTP first.'
        })
    
    user_id = request.session.get('reset_user_id')
    new_password = request.POST.get('new_password', '').strip()
    confirm_password = request.POST.get('confirm_password', '').strip()
    
    # Validate user_id exists in session
    if not user_id:
        return JsonResponse({
            'success': False,
            'message': 'Session expired. Please start the password reset process again.'
        })
    
    # Validate passwords
    if not new_password or not confirm_password:
        return JsonResponse({
            'success': False,
            'message': 'Please fill in all password fields.'
        })
    
    if new_password != confirm_password:
        return JsonResponse({
            'success': False,
            'message': 'Passwords do not match.'
        })
    
    if len(new_password) < 8:
        return JsonResponse({
            'success': False,
            'message': 'Password must be at least 8 characters long.'
        })
    
    try:
        # Get user from database
        user = User.objects.get(id=user_id)
        
        # Set new password (this hashes the password)
        user.set_password(new_password)
        
        # Save the user object to database
        user.save(update_fields=['password'])
        
        # Verify password was saved correctly by checking
        user.refresh_from_db()
        
        # Clear session data
        try:
            del request.session['reset_user_id']
            del request.session['reset_verified']
            request.session.modified = True
        except KeyError:
            pass
        
        return JsonResponse({
            'success': True,
            'message': 'Password reset successfully. You can now login with your new password.'
        })
        
    except User.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'User not found. Please start the password reset process again.'
        })
    except Exception as e:
        import traceback
        print(f"Error in reset_password: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({
            'success': False,
            'message': f'An error occurred while resetting password. Please try again.'
        })


def logout_view(request):
    """Handle user logout"""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('login')

# Signup / OTP Verification
def signup_view(request):
    """Handle user registration with optional OTP verification."""
    if request.method == 'POST':
        form = SignupForm(request.POST, request.FILES)  # Added request.FILES for image upload
        if form.is_valid():
            smtp_configured = has_smtp_configured()

            if smtp_configured:
                # Create inactive user for OTP verification
                user = form.save(commit=False)
                user.is_active = False
                user.is_verified = False
                user.save()

                otp, message = create_and_send_otp(user)
                if otp:
                    request.session['pending_user_id'] = user.id
                    messages.success(
                        request,
                        'Account created! Please check your email for verification code.'
                    )
                    return redirect('verify_otp')
                else:
                    user.delete()
                    messages.error(request, f'Failed to send verification email: {message}')
            else:
                # No SMTP → activate immediately
                user = form.save(commit=True)
                user.is_verified = True
                user.save()
                messages.success(request, 'Account created successfully. Please log in.')
                return redirect(reverse('login'))
    else:
        form = SignupForm()

    context = {
        'form': form,
        'smtp_configured': has_smtp_configured()
    }
    return render(request, 'signup.html', context)


def verify_otp_view(request):
    """Handle OTP verification for new users."""
    user_id = request.session.get('pending_user_id')
    if not user_id:
        messages.error(request, 'No pending verification found.')
        return redirect('signup')

    user = get_object_or_404(User, id=user_id, is_active=False)

    if request.method == 'POST':
        form = OTPVerificationForm(user=user, data=request.POST)
        if form.is_valid():
            otp_code = form.cleaned_data['otp_code']
            try:
                otp = OTPVerification.objects.get(
                    user=user,
                    otp_code=otp_code,
                    verification_type='email',
                    is_used=False
                )
                if otp.is_valid():
                    otp.is_used = True
                    otp.save()

                    user.is_active = True
                    user.is_verified = True
                    user.save()

                    login(request, user)
                    del request.session['pending_user_id']

                    messages.success(request, 'Email verified successfully! Welcome.')
                    return redirect('home')
                else:
                    messages.error(request, 'OTP has expired. Please request a new one.')
            except OTPVerification.DoesNotExist:
                messages.error(request, 'Invalid OTP code.')
    else:
        form = OTPVerificationForm(user=user)

    context = {'form': form, 'user': user, 'can_resend': True}
    return render(request, 'verify_otp.html', context)


def verify_otp_view(request):
    """Handle OTP verification for new users."""
    user_id = request.session.get('pending_user_id')
    if not user_id:
        messages.error(request, 'No pending verification found.')
        return redirect('signup')

    user = get_object_or_404(User, id=user_id, is_active=False)

    if request.method == 'POST':
        form = OTPVerificationForm(user=user, data=request.POST)
        if form.is_valid():
            otp_code = form.cleaned_data['otp_code']
            try:
                otp = OTPVerification.objects.get(
                    user=user,
                    otp_code=otp_code,
                    verification_type='email',
                    is_used=False
                )
                if otp.is_valid():
                    otp.is_used = True
                    otp.save()

                    user.is_active = True
                    user.is_verified = True
                    user.save()

                    login(request, user)
                    del request.session['pending_user_id']

                    messages.success(request, 'Email verified successfully! Welcome.')
                    return redirect('home')
                else:
                    messages.error(request, 'OTP has expired. Please request a new one.')
            except OTPVerification.DoesNotExist:
                messages.error(request, 'Invalid OTP code.')
    else:
        form = OTPVerificationForm(user=user)

    context = {'form': form, 'user': user, 'can_resend': True}
    return render(request, 'verify_otp.html', context)


@require_http_methods(["POST"])
def resend_otp_view(request):
    """Resend OTP via AJAX."""
    user_id = request.session.get('pending_user_id')
    if not user_id:
        return JsonResponse({'success': False, 'message': 'No pending verification found.'})

    try:
        user = User.objects.get(id=user_id, is_active=False)

        last_otp = OTPVerification.objects.filter(
            user=user,
            verification_type='email'
        ).order_by('-created_at').first()

        if last_otp and (timezone.now() - last_otp.created_at).seconds < 60:
            return JsonResponse({
                'success': False,
                'message': 'Please wait at least 1 minute before requesting a new OTP.'
            })

        otp, message = create_and_send_otp(user)
        if otp:
            return JsonResponse({'success': True, 'message': 'New OTP sent to your email!'})
        else:
            return JsonResponse({'success': False, 'message': f'Failed to send OTP: {message}'})
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Invalid user.'})
    except Exception:
        return JsonResponse({'success': False, 'message': 'An error occurred.'})


# Profile Management
@login_required
def profile_edit(request):
    """Edit user profile (details + picture)."""
    if request.method == 'POST':
        form = ProfileEditForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('profile_edit')
    else:
        form = ProfileEditForm(instance=request.user)

    return render(request, 'profile_edit.html', {'form': form})


@login_required
@require_http_methods(["POST"])
def change_password(request):
    """Change user password (AJAX)."""
    form = PasswordChangeSimpleForm(request.POST)
    if not form.is_valid():
        return JsonResponse({'success': False, 'errors': form.errors}, status=400)

    old_pw = form.cleaned_data['old_password']
    new_pw = form.cleaned_data['new_password1']
    user = request.user

    if not user.check_password(old_pw):
        return JsonResponse({'success': False, 'message': 'Current password is incorrect.'}, status=400)

    user.set_password(new_pw)
    user.save()
    update_session_auth_hash(request, user)
    return JsonResponse({'success': True, 'message': 'Password updated successfully.'})

# Coupons
@csrf_exempt
@login_required
def apply_coupon(request):
    """Apply and save a coupon for the authenticated user."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid request method'})

    try:
        data = json.loads(request.body)
        coupon_code = data.get('coupon_code', '').strip().upper()
        if not coupon_code:
            return JsonResponse({'success': False, 'message': 'Please enter a coupon code'})

        try:
            coupon = Coupon.objects.get(code=coupon_code)
        except Coupon.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Invalid coupon code'})

        if not coupon.is_valid():
            return JsonResponse({
                'success': False,
                'message': 'This coupon has expired or is no longer valid'
            })

        user_coupon, created = UserCoupon.objects.get_or_create(
            user=request.user,
            coupon=coupon,
            defaults={'assigned_at': timezone.now()}
        )

        if not created:
            return JsonResponse({
                'success': False,
                'message': 'You have already saved this coupon'
            })

        return JsonResponse({
            'success': True,
            'message': f'Coupon {coupon_code} saved successfully! You can now use it for discounts.'
        })
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Invalid data format'})
    except Exception:
        return JsonResponse({'success': False, 'message': 'An error occurred. Please try again.'})


@login_required
def my_coupons(request):
    """Retrieve and return user's saved coupons."""
    try:
        user_coupons = UserCoupon.objects.filter(
            user=request.user, is_used=False
        ).select_related('coupon')

        coupons_data = []
        current_time = timezone.now()

        for user_coupon in user_coupons:
            coupon = user_coupon.coupon
            is_expired = (
                current_time > coupon.valid_to or
                coupon.used_count >= coupon.usage_limit
            )
            coupons_data.append({
                'code': coupon.code,
                'description': coupon.description or '',
                'discount_display': coupon.get_discount_display(),
                'valid_to': coupon.valid_to.strftime('%d %b %Y'),
                'minimum_amount': float(coupon.minimum_amount),
                'usage_limit': coupon.usage_limit,
                'used_count': coupon.used_count,
                'is_expired': is_expired
            })

        return JsonResponse({'success': True, 'coupons': coupons_data})
    except Exception:
        return JsonResponse({'success': False, 'message': 'Error loading coupons'})

# Categories
def category_detail(request, slug):
    """Show a category detail page."""
    category = get_object_or_404(Category, slug=slug)
    return render(request, 'category_detail.html', {'category': category})



# base/views.py or create search/views.py
def search_suggestions(request):
    """
    AJAX endpoint for live search suggestions
    Returns matching courses from all types including categories and bundles
    """
    query = request.GET.get('q', '').strip()
    
    if len(query) < 2:
        return JsonResponse({'suggestions': []})
    
    suggestions = []
    
    # Search Categories
    categories = Category.objects.filter(
        Q(name__icontains=query) | Q(description__icontains=query)
    )[:3]
    
    for category in categories:
        suggestions.append({
            'type': 'Category',
            'name': category.name,
            'url': f'/category/{category.slug}/',
            'price': '',
            'thumbnail': None,
            'category': 'Exam Category',
            'description': category.description[:100] if category.description else ''
        })
    
    # Search Video Courses
    video_courses = VideoCourse.objects.filter(
        Q(name__icontains=query) | Q(description__icontains=query)
    )[:3]
    
    for course in video_courses:
        suggestions.append({
            'type': 'Video Course',
            'name': course.name,
            'url': f'/course/{course.pk}/',
            'price': f'₹{course.selling_price}',
            'thumbnail': course.thumbnail.url if course.thumbnail else None,
            'category': course.category.name if course.category else 'General'
        })
    
    # Search Live Class Courses
    live_courses = LiveClassCourse.objects.filter(
        Q(name__icontains=query) | Q(about__icontains=query),
        is_active=True
    )[:3]
    
    for course in live_courses:
        suggestions.append({
            'type': 'Live Class',
            'name': course.name,
            'url': f'/live-class/{course.pk}/',
            'price': f'₹{course.current_price}',
            'thumbnail': course.banner_image_desktop.url if course.banner_image_desktop else None,
            'category': course.category_name
        })
    
    # Search Test Series
    test_series = TestSeries.objects.filter(
        Q(title__icontains=query) | Q(description__icontains=query),
        is_active=True
    )[:3]
    
    for series in test_series:
        suggestions.append({
            'type': 'Test Series',
            'name': series.title,
            'url': f'/exam-series/{series.pk}/',
            'price': f'₹{series.price}' if not series.is_free else 'Free',
            'thumbnail': series.thumbnail.url if series.thumbnail else None,
            'category': series.category.name if series.category else 'General'
        })
    
    # Search E-Library Courses
    elibrary_courses = ELibraryCourse.objects.filter(
        Q(title__icontains=query) | Q(description__icontains=query),
        is_active=True
    )[:3]

    for course in elibrary_courses:
        suggestions.append({
            'type': 'E-Library',
            'name': course.title,
            'url': f'/ebook/{course.pk}/',  # Changed from /elibrary/course/{course.pk}/
            'price': f'₹{course.current_price}',
            'thumbnail': course.cover_image.url if course.cover_image else None,
            'category': course.category.name if course.category else 'General'
        })
        
    # Search Product Bundles
    bundles = ProductBundle.objects.filter(
        Q(title__icontains=query) | 
        Q(description__icontains=query) |
        Q(short_description__icontains=query),
        status='active'
    )[:3]
    
    for bundle in bundles:
        # Calculate total courses in bundle
        total_courses = (
            bundle.video_courses.count() +
            bundle.live_classes.count() +
            bundle.test_series.count() +
            bundle.elibrary_courses.count()
        )
        
        # Calculate discount percentage
        discount_percent = 0
        if bundle.original_price > 0:
            discount_percent = ((bundle.original_price - bundle.bundle_price) / bundle.original_price) * 100
        
        suggestions.append({
            'type': 'Bundle',
            'name': bundle.title,
            'url': f'/bundle/{bundle.slug}/',
            'price': f'₹{bundle.bundle_price}',
            'thumbnail': bundle.thumbnail.url if bundle.thumbnail else None,
            'category': f'{total_courses} Courses • {discount_percent:.0f}% OFF',
            'original_price': f'₹{bundle.original_price}'
        })
    
    return JsonResponse({'suggestions': suggestions[:15]})


def search_results(request):
    """
    Full search results page
    """
    query = request.GET.get('q', '').strip()
    
    context = {
        'query': query,
        'categories': [],
        'video_courses': [],
        'live_courses': [],
        'test_series': [],
        'elibrary_courses': [],
        'product_bundles': [],
        'total_results': 0
    }
    
    if query:
        # Categories
        categories = Category.objects.filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        ).distinct()
        
        # Video Courses
        video_courses = VideoCourse.objects.filter(
            Q(name__icontains=query) | 
            Q(description__icontains=query) |
            Q(category__name__icontains=query)
        ).select_related('category').distinct()
        
        # Live Classes
        live_courses = LiveClassCourse.objects.filter(
            Q(name__icontains=query) | 
            Q(about__icontains=query) |
            Q(category__name__icontains=query),
            is_active=True
        ).select_related('category').distinct()
        
        # Test Series
        test_series = TestSeries.objects.filter(
            Q(title__icontains=query) | 
            Q(description__icontains=query) |
            Q(category__name__icontains=query),
            is_active=True
        ).select_related('category').distinct()
        
        # E-Library
        elibrary_courses = ELibraryCourse.objects.filter(
            Q(title__icontains=query) | 
            Q(description__icontains=query) |
            Q(short_description__icontains=query) |
            Q(category__name__icontains=query),
            is_active=True
        ).select_related('category').distinct()
        
        # Product Bundles
        product_bundles = ProductBundle.objects.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(short_description__icontains=query) |
            Q(category__name__icontains=query) |
            Q(video_courses__name__icontains=query) |
            Q(live_classes__name__icontains=query) |
            Q(test_series__title__icontains=query) |
            Q(elibrary_courses__title__icontains=query),
            status='active'
        ).select_related('category').prefetch_related(
            'video_courses',
            'live_classes', 
            'test_series',
            'elibrary_courses'
        ).distinct()
        
        # Add calculated fields to bundles
        bundle_list = []
        for bundle in product_bundles:
            total_courses = (
                bundle.video_courses.count() +
                bundle.live_classes.count() +
                bundle.test_series.count() +
                bundle.elibrary_courses.count()
            )
            
            discount_percent = 0
            if bundle.original_price > 0:
                discount_percent = ((bundle.original_price - bundle.bundle_price) / bundle.original_price) * 100
            
            bundle.total_courses = total_courses
            bundle.discount_percent = discount_percent
            bundle_list.append(bundle)
        
        context['categories'] = categories
        context['video_courses'] = video_courses
        context['live_courses'] = live_courses
        context['test_series'] = test_series
        context['elibrary_courses'] = elibrary_courses
        context['product_bundles'] = bundle_list
        context['total_results'] = (
            categories.count() +
            video_courses.count() + 
            live_courses.count() + 
            test_series.count() + 
            elibrary_courses.count() +
            len(bundle_list)
        )
    
    return render(request, 'search_results.html', context)



#category display
def category_detail(request, slug):
    """
    Display all courses (Video, Live Class, Test Series, E-Library) 
    under a specific category
    """
    category = get_object_or_404(Category, slug=slug)
    
    # Get all courses under this category
    video_courses = VideoCourse.objects.filter(
        category=category
    ).order_by('-created_at')
    
    live_courses = LiveClassCourse.objects.filter(
        category=category,
        is_active=True
    ).order_by('-created_at')
    
    test_series = TestSeries.objects.filter(
        category=category,
        is_active=True
    ).order_by('-created_at')
    
    elibrary_courses = ELibraryCourse.objects.filter(
        category=category,
        is_active=True
    ).order_by('-created_at')
    
    # Count total courses
    total_courses = (
        video_courses.count() + 
        live_courses.count() + 
        test_series.count() + 
        elibrary_courses.count()
    )
    
    context = {
        'category': category,
        'video_courses': video_courses,
        'live_courses': live_courses,
        'test_series': test_series,
        'elibrary_courses': elibrary_courses,
        'total_courses': total_courses,
    }
    
    return render(request, 'category_detail.html', context)    

#Elibrary
def elibrary_home(request):
    """Display all e-library courses with filtering"""
    
    # Get featured and popular courses
    featured_courses = ELibraryCourse.objects.filter(
        is_active=True, 
        is_featured=True
    ).order_by('-created_at')[:8]
    
    # Get bestsellers
    bestseller_courses = ELibraryCourse.objects.filter(
        is_active=True,
        is_bestseller=True
    ).order_by('-enrollment_count')[:8]
    
    # Get all active courses
    all_courses = ELibraryCourse.objects.filter(
        is_active=True
    ).order_by('-created_at')
    
    context = {
        'featured_courses': featured_courses,
        'bestseller_courses': bestseller_courses,
        'all_courses': all_courses,
    }
    return render(request, 'elibrary/library.html', context)


def elibrary_course_detail(request, pk):
    """Display detailed information about a specific e-library course"""
    
    course = get_object_or_404(ELibraryCourse, pk=pk, is_active=True)
    
    # Check if user has purchased/has access to the course
    is_purchased = False
    access_expires_at = None
    
    if request.user.is_authenticated:
        # Check UserCourseAccess
        access = UserCourseAccess.objects.filter(
            user=request.user,
            course_id=course.id,
            course_type='elibrary',
            is_active=True
        ).first()
        
        if access and access.has_access:
            is_purchased = True
            access_expires_at = access.expires_at
    
    # Get PDFs organized by chapter
    pdfs = course.pdfs.filter(is_active=True).order_by('chapter_number', 'order')
    
    # Get preview PDFs (free access)
    preview_pdfs = pdfs.filter(is_preview=True)
    
    # Organize PDFs by chapter
    chapters = {}
    for pdf in pdfs:
        if pdf.chapter_number not in chapters:
            chapters[pdf.chapter_number] = []
        chapters[pdf.chapter_number].append(pdf)
    
    context = {
        'course': course,
        'is_purchased': is_purchased,
        'access_expires_at': access_expires_at,
        'pdfs': pdfs,
        'preview_pdfs': preview_pdfs,
        'chapters': chapters,
        'total_chapters': len(chapters),
    }
    return render(request, 'elibrary/course_detail.html', context)



@login_required
def elibrary_view_pdf(request, pdf_id):
    """View a PDF file (no access restrictions)."""
    
    pdf = get_object_or_404(ELibraryPDF, pk=pdf_id, is_active=True)
    
    # Log download
    ELibraryDownload.objects.create(
        user=request.user,
        pdf=pdf,
        ip_address=request.META.get('REMOTE_ADDR')
    )
    
    # Update download count
    pdf.download_count += 1
    pdf.save()
    
    # Serve PDF
    try:
        return FileResponse(
            open(pdf.file.path, 'rb'),
            content_type='application/pdf',
            as_attachment=False,
            filename=f"{pdf.title}.pdf"
        )
    except FileNotFoundError:
        raise Http404("PDF file not found")


@login_required
def elibrary_download_pdf(request, pdf_id):
    """Force download a PDF file (no access restrictions)."""
    
    pdf = get_object_or_404(ELibraryPDF, pk=pdf_id, is_active=True)
    
    # Log download
    ELibraryDownload.objects.create(
        user=request.user,
        pdf=pdf,
        ip_address=request.META.get('REMOTE_ADDR')
    )
    
    # Update download count
    pdf.download_count += 1
    pdf.save()
    
    # Force download
    try:
        return FileResponse(
            open(pdf.file.path, 'rb'),
            content_type='application/pdf',
            as_attachment=True,
            filename=f"{pdf.title}.pdf"
        )
    except FileNotFoundError:
        raise Http404("PDF file not found")


@login_required
def my_elibrary(request):
    """Display user's enrolled e-library courses"""
    
    enrollments = ELibraryEnrollment.objects.filter(
        user=request.user,
        payment_status='completed'
    ).select_related('course').order_by('-enrolled_at')
    
    context = {
        'enrollments': enrollments,
    }
    return render(request, 'elibrary/my_library.html', context)


def elibrary_category(request, category_slug):
    """Filter courses by category"""
    
    from video_courses.models import Category
    category = get_object_or_404(Category, slug=category_slug)
    
    courses = ELibraryCourse.objects.filter(
        category=category,
        is_active=True
    ).order_by('-created_at')
    
    context = {
        'category': category,
        'courses': courses,
    }
    return render(request, 'elibrary/category.html', context)




#Payment views

logger = logging.getLogger(__name__)

# Initialize Razorpay client
razorpay_client = razorpay.Client(
    auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
)

# ===== COURSE MODEL MAPPING =====
COURSE_MODELS = {
    'video_course': VideoCourse,
    'live_class': LiveClassCourse,
    'test_series': TestSeries,
    'elibrary': ELibraryCourse,
    'bundle': ProductBundle,
}


def get_course_model(course_type):
    """Get the model class for a course type"""
    return COURSE_MODELS.get(course_type)


def get_course_name(course, course_type):
    """
    Extract name from course based on type.
    Different models use different field names for the course name.
    """
    if course_type == 'video_course':
        return course.name if hasattr(course, 'name') else course.title
    elif course_type == 'live_class':
        return course.name
    elif course_type == 'test_series':
        return course.title
    elif course_type == 'elibrary':
        return course.title
    elif course_type == 'bundle':
        return course.title
    
    return str(course)


def get_course_price(course, course_type):
    """
    Extract price from course based on type.
    Returns tuple: (price, is_free)
    """
    # Check if course has is_free attribute
    is_free = getattr(course, 'is_free', False)
    
    if is_free:
        return 0, True
    
    # Different models use different price field names
    if course_type == 'video_course':
        return course.selling_price, False
    elif course_type == 'live_class':
        return course.current_price, False
    elif course_type == 'test_series':
        return course.price, False
    elif course_type == 'elibrary':
        return course.current_price, False
    elif course_type == 'bundle':
        return course.bundle_price, False
    
    return 0, False


def get_validity_days(course, course_type):
    """Get validity days for different course types"""
    if course_type == 'bundle':
        return course.validity_days
    # Add validity for other course types if needed
    return 365  # Default 1 year


def calculate_expiry_date(validity_days):
    """Calculate expiry date from validity days"""
    return timezone.now() + timedelta(days=validity_days)


# ===== PAYMENT ORDER CREATION =====

@login_required
def create_payment_order(request, course_type, course_id):
    """
    Create Razorpay order for course purchase.
    Works with video_course, live_class, test_series, elibrary, and bundle.
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)
    
    try:
        # Validate course type
        course_model = get_course_model(course_type)
        if not course_model:
            return JsonResponse({
                'success': False, 
                'error': f'Invalid course type: {course_type}'
            }, status=400)
        
        # Get course details
        course = get_object_or_404(course_model, id=course_id)
        
        # Get course name
        course_name = get_course_name(course, course_type)
        
        # Get price and free status
        price, is_free = get_course_price(course, course_type)
        
        # Handle free courses/bundles - create access directly without payment
        if is_free:
            logger.info(f"Free enrollment: {course_type} - {course.id} by user {request.user.id}")
            
            # Get validity days and calculate expiry
            validity_days = get_validity_days(course, course_type)
            expires_at = calculate_expiry_date(validity_days)
            
            # Grant access immediately for free courses
            access, created = UserCourseAccess.objects.get_or_create(
                user=request.user,
                course_id=course.id,
                course_type=course_type,
                defaults={
                    'access_granted_at': timezone.now(),
                    'expires_at': expires_at,
                    'is_active': True
                }
            )
            
            if not created and not access.is_active:
                access.is_active = True
                access.access_granted_at = timezone.now()
                access.expires_at = expires_at
                access.save()
            
            # Handle specific course type enrollments for free items
            if course_type == 'elibrary':
                enrollment, _ = ELibraryEnrollment.objects.get_or_create(
                    user=request.user,
                    course=course,
                    defaults={
                        'payment_status': 'completed',
                        'amount_paid': 0
                    }
                )
                if not created:
                    enrollment.payment_status = 'completed'
                    enrollment.save()
            
            # Update bundle stats for free bundles
            elif course_type == 'bundle':
                course.current_enrollments += 1
                course.total_purchases += 1
                course.save(update_fields=['current_enrollments', 'total_purchases'])
            
            return JsonResponse({
                'success': True,
                'is_free': True,
                'message': f'Free {course_type.replace("_", " ")} access granted!',
                'course_name': course_name,
                'course_type': course_type,
                'course_id': course.id
            })
        
        # Calculate amount in paise (multiply by 100)
        amount_paise = int(float(price) * 100)
        
        if amount_paise <= 0:
            return JsonResponse({'success': False, 'error': 'Invalid amount'}, status=400)
        
        # Create Razorpay order
        try:
            order_data = {
                'amount': amount_paise,
                'currency': 'INR',
                'payment_capture': '1',  # Auto-capture
                'receipt': f'order_{course_type}_{course_id}_{request.user.id}_{int(timezone.now().timestamp())}'
            }
            
            razorpay_order = razorpay_client.order.create(order_data)
            razorpay_order_id = razorpay_order['id']
            
            logger.info(f"Razorpay order created: {razorpay_order_id} for {course_type} - {course_id}")
            
        except Exception as e:
            logger.error(f"Razorpay order creation failed: {str(e)}")
            return JsonResponse({
                'success': False, 
                'error': f'Order creation failed: {str(e)}'
            }, status=400)
        
        # Save payment record in DB
        try:
            payment = Payment.objects.create(
                user=request.user,
                razorpay_order_id=razorpay_order_id,
                course_type=course_type,
                course_id=course_id,
                course_name=course_name,
                amount=amount_paise,
                currency='INR',
                status='Pending'
            )
            logger.info(f"Payment record created: {payment.id} for order {razorpay_order_id}")
            
        except Exception as e:
            logger.error(f"Payment record creation failed: {str(e)}")
            return JsonResponse({
                'success': False, 
                'error': f'Database error: {str(e)}'
            }, status=400)
        
        # Get user phone if available
        user_phone = ''
        if hasattr(request.user, 'profile') and hasattr(request.user.profile, 'phone'):
            user_phone = request.user.profile.phone
        
        # Return checkout data
        return JsonResponse({
            'success': True,
            'is_free': False,
            'razorpay_order_id': razorpay_order_id,
            'razorpay_merchant_key': settings.RAZORPAY_KEY_ID,
            'amount': amount_paise,
            'currency': 'INR',
            'course_name': course_name,
            'course_type': course_type,
            'course_id': course.id,
            'user_name': request.user.get_full_name() or request.user.username,
            'user_email': request.user.email,
            'user_phone': user_phone
        })
        
    except Exception as e:
        logger.error(f"Unexpected error in create_payment_order: {str(e)}", exc_info=True)
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


# ===== PAYMENT VERIFICATION =====

@csrf_exempt
def payment_handler(request):
    """
    Handle Razorpay payment callback for all course types including bundles.
    Verifies payment signature and grants course access.
    Returns JSON response.
    """
    if request.method != "POST":
        return JsonResponse({
            'success': False, 
            'error': 'Invalid request',
            'type': 'error'
        }, status=400)
    
    try:
        payment_id = request.POST.get('razorpay_payment_id', '')
        order_id = request.POST.get('razorpay_order_id', '')
        signature = request.POST.get('razorpay_signature', '')
        
        if not all([payment_id, order_id, signature]):
            return JsonResponse({
                'success': False,
                'error': 'Missing payment information',
                'type': 'error'
            }, status=400)
        
        # Fetch payment record
        try:
            payment = Payment.objects.get(razorpay_order_id=order_id)
        except Payment.DoesNotExist:
            logger.error(f"Payment record not found for order: {order_id}")
            return JsonResponse({
                'success': False,
                'error': 'Payment record not found',
                'type': 'error'
            }, status=404)
        
        # Verify signature
        try:
            params_dict = {
                'razorpay_order_id': order_id,
                'razorpay_payment_id': payment_id,
                'razorpay_signature': signature
            }
            
            razorpay_client.utility.verify_payment_signature(params_dict)
            logger.info(f"Payment signature verified: {payment_id}")
            
        except razorpay.errors.SignatureVerificationError as e:
            logger.error(f"Payment signature verification failed: {str(e)}")
            payment.status = 'Failed'
            payment.save()
            
            return JsonResponse({
                'success': False,
                'error': 'Payment verification failed',
                'type': 'error'
            }, status=400)
        
        # Update payment status
        payment.razorpay_payment_id = payment_id
        payment.razorpay_signature = signature
        payment.status = 'Success'
        payment.save()
        
        logger.info(f"Payment status updated to Success: {payment_id}")
        
        # Get course to determine validity days and calculate expiry
        course_model = get_course_model(payment.course_type)
        if course_model:
            try:
                course = course_model.objects.get(id=payment.course_id)
                validity_days = get_validity_days(course, payment.course_type)
                expires_at = calculate_expiry_date(validity_days)
            except:
                validity_days = 365  # Default
                expires_at = calculate_expiry_date(validity_days)
        else:
            validity_days = 365  # Default
            expires_at = calculate_expiry_date(validity_days)
        
        # Grant course access - FIXED: Removed validity_days, use expires_at
        access, created = UserCourseAccess.objects.get_or_create(
            user=payment.user,
            course_id=payment.course_id,
            course_type=payment.course_type,
            defaults={
                'access_granted_at': timezone.now(),
                'expires_at': expires_at,
                'is_active': True
            }
        )
        
        if created:
            logger.info(f"Course access created for user {payment.user.id}: {payment.course_type} - {payment.course_id}")
        else:
            # If access already exists, make sure it's active
            if not access.is_active:
                access.is_active = True
                access.access_granted_at = timezone.now()
                access.expires_at = expires_at
                access.save()
                logger.info(f"Course access reactivated for user {payment.user.id}: {payment.course_type} - {payment.course_id}")
        
        # Handle specific course type enrollments after payment
        if payment.course_type == 'elibrary':
            try:
                course = ELibraryCourse.objects.get(id=payment.course_id)
                enrollment, enroll_created = ELibraryEnrollment.objects.get_or_create(
                    user=payment.user,
                    course=course,
                    defaults={
                        'payment_status': 'completed',
                        'amount_paid': payment.amount / 100,
                        'payment_id': payment_id
                    }
                )
                
                if not enroll_created:
                    enrollment.payment_status = 'completed'
                    enrollment.amount_paid = payment.amount / 100
                    enrollment.payment_id = payment_id
                    enrollment.save()
                
                # Update enrollment count
                course.enrollment_count += 1
                course.save()
                
                logger.info(f"eLibrary enrollment created for user {payment.user.id}: {course.title}")
            except Exception as e:
                logger.error(f"Failed to create eLibrary enrollment: {str(e)}")
        
        # Handle bundle purchase - update stats
        elif payment.course_type == 'bundle':
            try:
                bundle = ProductBundle.objects.get(id=payment.course_id)
                
                # Update bundle stats
                bundle.current_enrollments += 1
                bundle.total_purchases += 1
                bundle.save(update_fields=['current_enrollments', 'total_purchases'])
                
                logger.info(f"Bundle purchase recorded for user {payment.user.id}: {bundle.title}")
            except Exception as e:
                logger.error(f"Failed to update Bundle stats: {str(e)}")
        
        # Return JSON response
        return JsonResponse({
            'success': True,
            'type': 'success',
            'message': f'Payment successful! Access granted to {payment.course_name}',
            'payment_id': payment_id,
            'order_id': order_id,
            'course_name': payment.course_name,
            'course_type': payment.course_type,
            'course_id': payment.course_id,
            'amount': float(payment.amount / 100),
            'user': payment.user.get_full_name() or payment.user.username
        })
        
    except Exception as e:
        logger.error(f"Payment handler error: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': str(e),
            'type': 'error'
        }, status=500)


# ===== MY PURCHASES VIEW =====
@login_required
def my_purchases(request):
    """
    Display all purchased products for the authenticated user.
    """
    user = request.user
    
    # Get all active course access records for the user
    course_access_records = UserCourseAccess.objects.filter(
        user=user,
        is_active=True
    ).select_related('payment').order_by('-access_granted_at')
    
    # Organize purchases by type
    purchases = {
        'video_courses': [],
        'live_classes': [],
        'test_series': [],
        'elibrary_courses': [],
        'bundles': []
    }
    
    # Process each access record
    for access_record in course_access_records:
        payment = access_record.payment  # Use the ForeignKey relationship
        
        try:
            if access_record.course_type == 'video_course':
                try:
                    from video_courses.models import VideoCourse
                    course = VideoCourse.objects.get(id=access_record.course_id)
                    purchases['video_courses'].append({
                        'course': course,
                        'access_granted': access_record.access_granted_at,
                        'payment': payment,
                        'expires_at': access_record.expires_at,
                    })
                except VideoCourse.DoesNotExist:
                    print(f"Video course {access_record.course_id} not found")
                except ImportError:
                    print("Could not import VideoCourse")
            
            elif access_record.course_type == 'live_class':
                try:
                    from live_class.models import LiveClassCourse
                    course = LiveClassCourse.objects.get(id=access_record.course_id)
                    purchases['live_classes'].append({
                        'course': course,
                        'access_granted': access_record.access_granted_at,
                        'payment': payment,
                        'expires_at': access_record.expires_at,
                    })
                except LiveClassCourse.DoesNotExist:
                    print(f"Live class {access_record.course_id} not found")
                except ImportError:
                    print("Could not import LiveClassCourse")
            
            elif access_record.course_type == 'test_series':
                try:
                    from testseries.models import TestSeries
                    course = TestSeries.objects.get(id=access_record.course_id)
                    purchases['test_series'].append({
                        'course': course,
                        'access_granted': access_record.access_granted_at,
                        'payment': payment,
                        'expires_at': access_record.expires_at,
                    })
                except TestSeries.DoesNotExist:
                    print(f"Test series {access_record.course_id} not found")
                except ImportError:
                    print("Could not import TestSeries")
            
            elif access_record.course_type == 'elibrary':
                try:
                    from elibrary.models import ELibraryCourse
                    course = ELibraryCourse.objects.get(id=access_record.course_id)
                    purchases['elibrary_courses'].append({
                        'course': course,
                        'access_granted': access_record.access_granted_at,
                        'payment': payment,
                        'expires_at': access_record.expires_at,
                    })
                except ELibraryCourse.DoesNotExist:
                    print(f"Elibrary course {access_record.course_id} not found")
                except ImportError:
                    print("Could not import ELibraryCourse")
            
            elif access_record.course_type == 'bundle':
                try:
                    from adminpanel.models import ProductBundle  # ← Check if this is correct
                    bundle = ProductBundle.objects.get(id=access_record.course_id)
                    purchases['bundles'].append({
                        'course': bundle,
                        'access_granted': access_record.access_granted_at,
                        'payment': payment,
                        'expires_at': access_record.expires_at,
                    })
                    print(f"✓ Bundle added: {bundle.title}")  # Debug
                except ProductBundle.DoesNotExist:
                    print(f"✗ Bundle {access_record.course_id} not found in database")
                except ImportError as e:
                    print(f"✗ Could not import ProductBundle: {e}")
                    # Try alternative import if ProductBundle might be in base.models
                    try:
                        from base.models import ProductBundle
                        bundle = ProductBundle.objects.get(id=access_record.course_id)
                        purchases['bundles'].append({
                            'course': bundle,
                            'access_granted': access_record.access_granted_at,
                            'payment': payment,
                            'expires_at': access_record.expires_at,
                        })
                        print(f"✓ Bundle added from base.models: {bundle.title}")
                    except:
                        print(f"✗ Could not import ProductBundle from base.models either")
        
        except Exception as e:
            print(f"Error processing {access_record.course_type} (ID: {access_record.course_id}): {str(e)}")
            import traceback
            traceback.print_exc()
            continue
    
    
    # Calculate total spent
    total_spent = 0
    for access in course_access_records:
        if access.payment:
            total_spent += access.payment.amount / 100
    
    # Count total purchases
    total_purchases = course_access_records.count()
    
    context = {
        'purchases': purchases,
        'total_spent': total_spent,
        'total_purchases': total_purchases,
    }
    
    return render(request, 'my_purchases.html', context)