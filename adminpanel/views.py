# adminpanel/views.py
from datetime import timedelta
import csv
import json
import secrets
import string

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required 
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import Group
from django.core.paginator import Paginator
from django.db.models import Q, Sum, Count
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.text import slugify
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST , require_http_methods

from video_courses.models import Category

from .forms import *
from .models import*
User = get_user_model()


# bundles/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Q, Count, Sum
from django.http import JsonResponse
from django.core.paginator import Paginator

from .models import ProductBundle , DeveloperPopup 
from .forms import ProductBundleForm, BundleFilterForm , DeveloperPopupForm 
from video_courses.models import VideoCourse
from live_class.models import LiveClassCourse
from testseries.models import TestSeries
from elibrary.models import ELibraryCourse
from base.models import Payment , UserCourseAccess


def is_admin(user):
    return user.is_authenticated and user.is_staff
    

@login_required(login_url='login')
def notification_manage(request):
    """Manage all notifications"""
    if not request.user.is_staff:
        messages.error(request, 'Access denied. Admin privileges required.')
        return redirect('home')
    
    notifications = Notification.objects.all()
    
    context = {
        'notifications': notifications,
        'total_notifications': notifications.count(),
    }
    
    return render(request, 'notifications/notification_manage.html', context)


@login_required(login_url='login')
def notification_create(request):
    """Create new notification"""
    if not request.user.is_staff:
        messages.error(request, 'Access denied. Admin privileges required.')
        return redirect('home')
    
    if request.method == 'POST':
        form = NotificationForm(request.POST)
        if form.is_valid():
            notification = form.save(commit=False)
            # Automatically set scheduled_time to current time
            notification.scheduled_time = timezone.now()
            # Automatically set is_active to True
            notification.is_active = True
            notification.save()
            messages.success(request, f'Notification "{notification.title}" created successfully!')
            return redirect('adminnotifications')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = NotificationForm()
    
    context = {
        'form': form,
        'action': 'Create'
    }
    
    return render(request, 'notifications/notification_form.html', context)


@login_required(login_url='login')
@require_http_methods(["POST", "GET"])
def notification_delete(request, pk):
    """Delete notification"""
    if not request.user.is_staff:
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    notification = get_object_or_404(Notification, pk=pk)
    title = notification.title
    notification.delete()
    
    messages.success(request, f'Notification "{title}" deleted successfully!')
    return redirect('adminnotifications')

#Intro popup views
@login_required
def developer_popup_manage(request):
    """Manage developer popup settings"""
    popup = DeveloperPopup.objects.first()
    
    context = {
        'popup': popup,
    }
    return render(request, 'developer_popup_manage.html', context)

@login_required
def developer_popup_create(request):
    """Create new developer popup settings"""
    if request.method == 'POST':
        form = DeveloperPopupForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Developer popup created successfully!')
            return redirect('developer_popup_manage')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = DeveloperPopupForm()
    
    context = {
        'form': form,
    }
    return render(request, 'developer_popup_form.html', context)

@login_required
def developer_popup_edit(request, pk):
    """Edit existing developer popup settings"""
    popup = get_object_or_404(DeveloperPopup, pk=pk)
    
    if request.method == 'POST':
        form = DeveloperPopupForm(request.POST, request.FILES, instance=popup)
        if form.is_valid():
            form.save()
            messages.success(request, 'Developer popup updated successfully!')
            return redirect('developer_popup_manage')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = DeveloperPopupForm(instance=popup)
    
    context = {
        'form': form,
        'popup': popup,
    }
    return render(request, 'developer_popup_form.html', context)

@login_required
def developer_popup_delete(request, pk):
    """Delete developer popup settings"""
    popup = get_object_or_404(DeveloperPopup, pk=pk)
    popup.delete()
    messages.success(request, 'Developer popup deleted successfully!')
    return redirect('developer_popup_manage')

@login_required
def developer_popup_toggle_status(request, pk):
    """Toggle active status of developer popup"""
    popup = get_object_or_404(DeveloperPopup, pk=pk)
    popup.is_active = not popup.is_active
    popup.save()
    
    status = "activated" if popup.is_active else "deactivated"
    messages.success(request, f'Developer popup {status} successfully!')
    return redirect('developer_popup_manage')



# ======================== ADMIN DASHBOARD VIEWS ========================
@staff_member_required
def admin_dashboard(request):
    """Main admin dashboard with dynamic data"""
    
    # Date ranges
    now = timezone.now()
    this_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    # ===== USER STATISTICS =====
    total_users = User.objects.filter(is_superuser=False).count()
    this_month_signups = User.objects.filter(
        date_joined__gte=this_month, 
        is_superuser=False
    ).count()
    
    # ===== EARNINGS STATISTICS =====
    # Total earnings from all successful payments
    total_earnings = Payment.objects.filter(
        status='Success'
    ).aggregate(
        total=Sum('amount')
    )['total'] or 0
    total_earnings = total_earnings / 100  # Convert from paise to rupees
    
    # This month earnings
    this_month_earnings = Payment.objects.filter(
        status='Success',
        created_at__gte=this_month
    ).aggregate(
        total=Sum('amount')
    )['total'] or 0
    this_month_earnings = this_month_earnings / 100
    
    # ===== COURSE STATISTICS =====
    total_live_classes = LiveClassCourse.objects.filter(is_active=True).count()
    total_video_courses = VideoCourse.objects.count()
    total_test_series = TestSeries.objects.filter(is_active=True).count()
    total_elibrary = ELibraryCourse.objects.filter(is_active=True).count()
    total_bundles = ProductBundle.objects.filter(status='active').count()
    
    # ===== ENROLLMENT STATISTICS =====
    total_enrollments = UserCourseAccess.objects.filter(is_active=True).count()
    
    # Enrollments by course type
    enrollments_by_type = UserCourseAccess.objects.filter(
        is_active=True
    ).values('course_type').annotate(
        count=Count('id')
    )
    
    enrollment_stats = {item['course_type']: item['count'] for item in enrollments_by_type}
    
    # ===== LATEST TRANSACTIONS =====
    latest_transactions = Payment.objects.select_related('user').order_by('-created_at')[:10]
    
    # Format transactions for display
    transactions_data = []
    for payment in latest_transactions:
        transactions_data.append({
            'invoice': payment.razorpay_order_id[:15] + '...' if len(payment.razorpay_order_id) > 15 else payment.razorpay_order_id,
            'customer': payment.user.get_full_name() or payment.user.email.split('@')[0] if payment.user else 'Guest',
            'amount': f"₹{payment.amount / 100:.2f}",
            'status': payment.status,
            'date': payment.created_at.strftime('%Y-%m-%d'),
            'course_name': payment.course_name[:30] + '...' if len(payment.course_name) > 30 else payment.course_name,
            'course_type': payment.get_course_type_display(),
        })
    
    # ===== REVENUE BREAKDOWN =====
    # Revenue by course type
    revenue_by_type = Payment.objects.filter(
        status='Success'
    ).values('course_type').annotate(
        total=Sum('amount')
    ).order_by('-total')
    
    revenue_breakdown = []
    for item in revenue_by_type:
        revenue_breakdown.append({
            'type': item['course_type'].replace('_', ' ').title(),
            'amount': item['total'] / 100,
            'count': Payment.objects.filter(
                status='Success',
                course_type=item['course_type']
            ).count()
        })
    
    # ===== TOP SELLING COURSES =====
    top_courses = Payment.objects.filter(
        status='Success'
    ).values('course_name', 'course_type').annotate(
        sales_count=Count('id'),
        revenue=Sum('amount')
    ).order_by('-sales_count')[:5]
    
    top_courses_data = []
    for course in top_courses:
        top_courses_data.append({
            'name': course['course_name'],
            'type': course['course_type'].replace('_', ' ').title(),
            'sales': course['sales_count'],
            'revenue': course['revenue'] / 100
        })
    
    # ===== RECENT USER ACTIVITY =====
    recent_users = User.objects.filter(
        is_superuser=False
    ).order_by('-date_joined')[:5]
    
    recent_users_data = []
    for user in recent_users:
        # Get user's purchase count
        purchase_count = UserCourseAccess.objects.filter(
            user=user,
            is_active=True
        ).count()
        
        recent_users_data.append({
            'name': user.get_full_name() or user.email.split('@')[0],
            'email': user.email,
            'joined': user.date_joined.strftime('%Y-%m-%d'),
            'purchases': purchase_count,
            'verified': user.is_verified
        })
    
    context = {
        # User Stats
        'total_users': total_users,
        'this_month_signups': this_month_signups,
        
        # Earnings Stats
        'total_earnings': f"{total_earnings:.2f}",
        'this_month_earnings': f"{this_month_earnings:.2f}",
        
        # Course Stats
        'total_live_classes': total_live_classes,
        'total_video_courses': total_video_courses,
        'total_test_series': total_test_series,
        'total_elibrary': total_elibrary,
        'total_bundles': total_bundles,
        
        # Enrollment Stats
        'total_enrollments': total_enrollments,
        'enrollment_stats': enrollment_stats,
        
        # Transactions
        'latest_transactions': transactions_data,
        'total_transactions': Payment.objects.count(),
        
        # Revenue Breakdown
        'revenue_breakdown': revenue_breakdown,
        
        # Top Courses
        'top_courses': top_courses_data,
        
        # Recent Users
        'recent_users': recent_users_data,
    }
    
    return render(request, 'admin_dashboard.html', context)


@staff_member_required
def signup_dashboard(request):
    """Signup analytics dashboard view - EXCLUDES superusers"""
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    user_type_filter = request.GET.get('user_type', '')
    date_range = request.GET.get('date_range', '')
    sort_by = request.GET.get('sort', 'date_joined')
    order = request.GET.get('order', 'desc')

    users = User.objects.filter(is_superuser=False)

    if search_query:
        search_filters = (
            Q(email__icontains=search_query)
            | Q(first_name__icontains=search_query)
            | Q(last_name__icontains=search_query)
        )
        if hasattr(User, 'contact_number'):
            search_filters |= Q(contact_number__icontains=search_query)
        users = users.filter(search_filters)

    if user_type_filter == 'staff':
        users = users.filter(is_staff=True, is_superuser=False)
    elif user_type_filter == 'regular':
        users = users.filter(is_staff=False, is_superuser=False)

    if status_filter == 'active':
        users = users.filter(is_active=True)
    elif status_filter == 'inactive':
        users = users.filter(is_active=False)

    if date_range:
        now = timezone.now()
        if date_range == 'today':
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
            users = users.filter(date_joined__gte=start_date)
        elif date_range == 'week':
            start_date = now - timedelta(days=7)
            users = users.filter(date_joined__gte=start_date)
        elif date_range == 'month':
            start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            users = users.filter(date_joined__gte=start_date)
        elif date_range == 'year':
            start_date = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            users = users.filter(date_joined__gte=start_date)

    if sort_by in ['id', 'email', 'date_joined', 'last_login']:
        if order == 'desc':
            sort_by = f'-{sort_by}'
        users = users.order_by(sort_by)
    elif sort_by == 'name':
        users = users.order_by('-first_name', '-last_name') if order == 'desc' else users.order_by('first_name', 'last_name')
    else:
        users = users.order_by('-date_joined')

    paginator = Paginator(users, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    total_users = User.objects.filter(is_superuser=False).count()
    active_users = User.objects.filter(is_active=True, is_superuser=False).count()
    inactive_users = User.objects.filter(is_active=False, is_superuser=False).count()
    staff_users = User.objects.filter(is_staff=True, is_superuser=False).count()
    regular_users = User.objects.filter(is_staff=False, is_superuser=False).count()

    current_month = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    this_month_signups = User.objects.filter(date_joined__gte=current_month, is_superuser=False).count()
    last_month = (current_month - timedelta(days=1)).replace(day=1)
    last_month_signups = User.objects.filter(
        date_joined__gte=last_month, date_joined__lt=current_month, is_superuser=False
    ).count()

    active_percentage = round((active_users / total_users * 100) if total_users > 0 else 0, 1)
    inactive_percentage = round((inactive_users / total_users * 100) if total_users > 0 else 0, 1)
    staff_percentage = round((staff_users / total_users * 100) if total_users > 0 else 0, 1)
    regular_percentage = round((regular_users / total_users * 100) if total_users > 0 else 0, 1)
    monthly_change = round(
        ((this_month_signups - last_month_signups) / last_month_signups * 100) if last_month_signups > 0 else 0, 1
    )

    context = {
        'users': page_obj,
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        'total_users': total_users,
        'this_month_signups': this_month_signups,
        'staff_users': staff_users,
        'regular_users': regular_users,
        'active_users': active_users,
        'inactive_users': inactive_users,
        'active_percentage': active_percentage,
        'inactive_percentage': inactive_percentage,
        'staff_percentage': staff_percentage,
        'regular_percentage': regular_percentage,
        'monthly_change': monthly_change,
        'total_growth': round((this_month_signups / total_users * 100) if total_users > 0 else 0, 1),
    }
    return render(request, 'analytics/signups.html', context)


@staff_member_required
def payment_dashboard(request):
    """Payment analytics dashboard view with dynamic data"""
    
    # Date ranges
    now = timezone.now()
    this_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    last_30_days = now - timedelta(days=30)
    
    # Get filter parameters
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    course_type_filter = request.GET.get('course_type', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    # Base queryset
    payments = Payment.objects.select_related('user').order_by('-created_at')
    
    # Apply filters
    if search_query:
        payments = payments.filter(
            Q(razorpay_order_id__icontains=search_query) |
            Q(razorpay_payment_id__icontains=search_query) |
            Q(user__email__icontains=search_query) |
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query) |
            Q(course_name__icontains=search_query)
        )
    
    if status_filter:
        payments = payments.filter(status=status_filter)
    
    if course_type_filter:
        payments = payments.filter(course_type=course_type_filter)
    
    if date_from:
        payments = payments.filter(created_at__date__gte=date_from)
    
    if date_to:
        payments = payments.filter(created_at__date__lte=date_to)
    
    # Pagination
    paginator = Paginator(payments, 20)  # 20 payments per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Format payments data
    payments_data = []
    for payment in page_obj:
        payments_data.append({
            'id': payment.id,
            'razorpay_order_id': payment.razorpay_order_id,
            'razorpay_payment_id': payment.razorpay_payment_id or 'N/A',
            'user_name': payment.user.get_full_name() if payment.user else 'Guest',
            'user_email': payment.user.email if payment.user else 'N/A',
            'course_name': payment.course_name,
            'course_type': payment.get_course_type_display(),
            'amount': payment.amount / 100,  # Convert from paise
            'currency': payment.currency,
            'status': payment.status,
            'created_at': payment.created_at,
            'updated_at': payment.updated_at,
        })
    
    # Statistics
    all_payments = Payment.objects.all()
    
    total_payments = all_payments.count()
    successful_payments = all_payments.filter(status='Success').count()
    failed_payments = all_payments.filter(status='Failed').count()
    pending_payments = all_payments.filter(status='Created').count()
    
    # Revenue calculations
    total_revenue = all_payments.filter(status='Success').aggregate(
        total=Sum('amount')
    )['total'] or 0
    total_revenue = total_revenue / 100
    
    this_month_revenue = all_payments.filter(
        status='Success',
        created_at__gte=this_month
    ).aggregate(total=Sum('amount'))['total'] or 0
    this_month_revenue = this_month_revenue / 100
    
    last_30_days_revenue = all_payments.filter(
        status='Success',
        created_at__gte=last_30_days
    ).aggregate(total=Sum('amount'))['total'] or 0
    last_30_days_revenue = last_30_days_revenue / 100
    
    # Today's stats
    today = now.date()
    today_payments = all_payments.filter(created_at__date=today).count()
    today_revenue = all_payments.filter(
        status='Success',
        created_at__date=today
    ).aggregate(total=Sum('amount'))['total'] or 0
    today_revenue = today_revenue / 100
    
    # Revenue by course type
    revenue_by_course_type = all_payments.filter(
        status='Success'
    ).values('course_type').annotate(
        total=Sum('amount'),
        count=Count('id')
    ).order_by('-total')
    
    course_type_stats = []
    for item in revenue_by_course_type:
        course_type_stats.append({
            'type': item['course_type'].replace('_', ' ').title(),
            'revenue': item['total'] / 100,
            'count': item['count']
        })
    
    # Recent successful payments
    recent_successful = all_payments.filter(
        status='Success'
    ).select_related('user').order_by('-created_at')[:5]
    
    recent_successful_data = []
    for payment in recent_successful:
        recent_successful_data.append({
            'order_id': payment.razorpay_order_id[:20] + '...' if len(payment.razorpay_order_id) > 20 else payment.razorpay_order_id,
            'user': payment.user.get_full_name() if payment.user else 'Guest',
            'amount': payment.amount / 100,
            'course': payment.course_name[:30] + '...' if len(payment.course_name) > 30 else payment.course_name,
            'date': payment.created_at.strftime('%d %b, %Y %I:%M %p')
        })
    
    # Get unique course types for filter
    course_types = Payment.objects.values_list('course_type', flat=True).distinct()
    
    context = {
        'payments': payments_data,
        'page_obj': page_obj,
        'total_payments': total_payments,
        'successful_payments': successful_payments,
        'failed_payments': failed_payments,
        'pending_payments': pending_payments,
        'total_revenue': f"{total_revenue:.2f}",
        'this_month_revenue': f"{this_month_revenue:.2f}",
        'last_30_days_revenue': f"{last_30_days_revenue:.2f}",
        'today_payments': today_payments,
        'today_revenue': f"{today_revenue:.2f}",
        'course_type_stats': course_type_stats,
        'recent_successful': recent_successful_data,
        'course_types': course_types,
        'search_query': search_query,
        'status_filter': status_filter,
        'course_type_filter': course_type_filter,
        'date_from': date_from,
        'date_to': date_to,
    }
    
    return render(request, 'analytics/payment.html', context)

# ======================== ADMIN CREATE USER ========================

def staff_required(view):
    return user_passes_test(lambda u: u.is_active and u.is_staff)(view)

@staff_required
def add_user(request):
    if request.method == 'POST':
        form = AdminCreateUserForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'User created successfully.')
            return redirect('signupdashboard')
        messages.error(request, 'Please correct the errors below.')
    else:
        form = AdminCreateUserForm()
    return render(request, 'users_add.html', {'form': form})


# ======================== USER MANAGEMENT VIEWS ========================

@staff_member_required
def edit_user(request, user_id):
    """Edit user view - Maintains user status and removes permission editing"""
    user_obj = get_object_or_404(User, id=user_id)
    original_is_active = user_obj.is_active
    original_is_staff = user_obj.is_staff
    original_is_superuser = user_obj.is_superuser

    if request.method == 'POST':
        try:
            user_obj.email = request.POST.get('email', user_obj.email)
            user_obj.first_name = request.POST.get('first_name', '')
            user_obj.last_name = request.POST.get('last_name', '')

            if hasattr(user_obj, 'middle_name'):
                user_obj.middle_name = request.POST.get('middle_name', '')
            if hasattr(user_obj, 'contact_number'):
                user_obj.contact_number = request.POST.get('contact_number', '')
            if hasattr(user_obj, 'gender'):
                user_obj.gender = request.POST.get('gender', '')
            if hasattr(user_obj, 'age'):
                age = request.POST.get('age')
                if age:
                    try:
                        user_obj.age = int(age)
                    except ValueError:
                        pass

            password = request.POST.get('password')
            if password:
                user_obj.set_password(password)

            user_obj.is_active = original_is_active
            user_obj.is_staff = original_is_staff
            user_obj.is_superuser = original_is_superuser

            selected_groups = request.POST.getlist('groups')
            if selected_groups:
                user_obj.groups.clear()
                for group_id in selected_groups:
                    try:
                        group = Group.objects.get(id=group_id)
                        user_obj.groups.add(group)
                    except Group.DoesNotExist:
                        pass

            user_obj.save()

            extra_info = []
            if password:
                extra_info.append('Password updated')
            if user_obj.groups.exists():
                extra_info.append(f'Member of {user_obj.groups.count()} groups')

            extra = ' | '.join(extra_info) if extra_info else ''
            messages.success(request, f'User <strong>{user_obj.email}</strong> updated successfully! {extra}')
            return redirect('signupdashboard')
        except Exception as e:
            messages.error(request, f'Error updating user: {str(e)}')

    all_groups = Group.objects.all()
    user_groups = user_obj.groups.all()
    available_groups = all_groups.exclude(id__in=user_groups.values_list('id', flat=True))
    
    # Get gender display value
    gender_display = user_obj.get_gender_display() if user_obj.gender else 'Not specified'

    context = {
        'user_obj': user_obj,
        'all_groups': all_groups,
        'user_groups': user_groups,
        'available_groups': available_groups,
        'gender_choices': User.GENDER_CHOICES,
        'gender_display': gender_display,
    }
    return render(request, 'analytics/edit_user.html', context)


@staff_member_required
def delete_user(request, user_id):
    """Delete user - with superuser protection"""
    user_obj = get_object_or_404(User, id=user_id)

    if user_obj.is_superuser:
        messages.error(request, 'Cannot delete superuser accounts!')
        return redirect('signupdashboard')

    if request.method == 'POST':
        try:
            user_email = user_obj.email
            user_obj.delete()
            messages.success(request, f'User <strong>{user_email}</strong> deleted successfully!')
            return redirect('signupdashboard')
        except Exception as e:
            messages.error(request, f'Error deleting user: {str(e)}')

    context = {'user_obj': user_obj}
    return render(request, 'analytics/delete_user.html', context)


@staff_member_required
def toggle_user_status(request, user_id):
    """Toggle user active status - with superuser protection"""
    user_obj = get_object_or_404(User, id=user_id)

    if user_obj.is_superuser:
        messages.error(request, 'Cannot change status of superuser accounts!')
        return redirect('signupdashboard')

    if request.method == 'POST':
        try:
            user_obj.is_active = not user_obj.is_active
            user_obj.save()
            action = 'activated' if user_obj.is_active else 'deactivated'
            messages.success(request, f'User <strong>{user_obj.email}</strong> {action} successfully!')
            return redirect('signupdashboard')
        except Exception as e:
            messages.error(request, f'Error changing user status: {str(e)}')

    context = {'user_obj': user_obj}
    return render(request, 'analytics/toggle_status.html', context)


@staff_member_required
def reset_user_password(request, user_id):
    """Reset user password - with superuser protection"""
    user_obj = get_object_or_404(User, id=user_id)

    if user_obj.is_superuser and not request.user.is_superuser:
        messages.error(request, 'Only superusers can reset superuser passwords!')
        return redirect('signupdashboard')

    if request.method == 'POST':
        try:
            alphabet = string.ascii_letters + string.digits + "!@#$%"
            new_password = ''.join(secrets.choice(alphabet) for _ in range(12))
            user_obj.set_password(new_password)
            user_obj.save()

            messages.success(
                request,
                f'Password reset for <strong>{user_obj.email}</strong>! New temporary password: '
                f'<code style="background:#f3f4f6;padding:2px 6px;border-radius:4px;'
                f'font-family:monospace;color:#dc2626;">{new_password}</code>'
            )
            return redirect('signupdashboard')
        except Exception as e:
            messages.error(request, f'Error resetting password: {str(e)}')

    context = {'user_obj': user_obj}
    return render(request, 'analytics/reset_password.html', context)



# ======================== COUPON ADMIN VIEWS ========================

@login_required
@user_passes_test(is_admin)
def coupon_list(request):
    """Admin page to list all coupons"""
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')

    coupons = Coupon.objects.all()
    if search_query:
        coupons = coupons.filter(Q(code__icontains=search_query) | Q(description__icontains=search_query))
    if status_filter:
        coupons = coupons.filter(status=status_filter)

    for coupon in coupons:
        coupon.remaining_uses = coupon.usage_limit - coupon.used_count
        coupon.is_expired = coupon.valid_to < timezone.now()

    paginator = Paginator(coupons, 20)
    page_number = request.GET.get('page')
    coupons = paginator.get_page(page_number)

    context = {
        'coupons': coupons,
        'search_query': search_query,
        'status_filter': status_filter,
        'status_choices': Coupon.STATUS_CHOICES,
    }
    return render(request, 'coupons/list.html', context)


@login_required
@user_passes_test(is_admin)
def coupon_create(request):
    """Create new coupon"""
    if request.method == 'POST':
        form = CouponForm(request.POST)
        if form.is_valid():
            coupon = form.save(commit=False)
            coupon.created_by = request.user
            coupon.save()
            messages.success(request, f'Coupon "{coupon.code}" created successfully!')
            return redirect('coupon_list')
        messages.error(request, 'Please correct the errors below.')
    else:
        form = CouponForm()
        form.fields['code'].initial = Coupon.generate_coupon_code()

    return render(request, 'coupons/create.html', {'form': form})


@login_required
@user_passes_test(is_admin)
def coupon_edit(request, pk):
    """Edit existing coupon"""
    coupon = get_object_or_404(Coupon, pk=pk)

    if request.method == 'POST':
        form = CouponForm(request.POST, instance=coupon)
        if form.is_valid():
            form.save()
            messages.success(request, f'Coupon "{coupon.code}" updated successfully!')
            return redirect('coupon_list')
        messages.error(request, 'Please correct the errors below.')
    else:
        form = CouponForm(instance=coupon)

    usage_stats = CouponUsage.objects.filter(coupon=coupon).aggregate(
        total_usage=Count('id'), total_discount=Sum('discount_amount')
    )

    context = {'form': form, 'coupon': coupon, 'usage_stats': usage_stats}
    return render(request, 'coupons/edit.html', context)


@login_required
@user_passes_test(is_admin)
@require_POST
def coupon_delete(request, pk):
    """Delete coupon"""
    coupon = get_object_or_404(Coupon, pk=pk)
    code = coupon.code
    coupon.delete()
    messages.success(request, f'Coupon "{code}" deleted successfully!')
    return redirect('coupon_list')


@login_required
@user_passes_test(is_admin)
def coupon_analytics(request):
    """Coupon analytics dashboard"""
    total_coupons = Coupon.objects.count()
    active_coupons = Coupon.objects.filter(status='active').count()
    expired_coupons = Coupon.objects.filter(valid_to__lt=timezone.now()).count()

    usage_stats = CouponUsage.objects.aggregate(total_usage=Count('id'), total_discount=Sum('discount_amount'))

    top_coupons = (
        Coupon.objects.annotate(
            usage_count=Count('usage_history'), total_discount=Sum('usage_history__discount_amount')
        )
        .order_by('-usage_count')[:10]
    )

    context = {
        'total_coupons': total_coupons,
        'active_coupons': active_coupons,
        'expired_coupons': expired_coupons,
        'usage_stats': usage_stats,
        'top_coupons': top_coupons,
    }
    return render(request, 'coupons/analytics.html', context)


# ======================== PUBLIC COUPON APIs ========================

@csrf_exempt
@login_required
def apply_coupon(request):
    """Apply coupon code (AJAX endpoint) - WITH USAGE TRACKING"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid request method'})
    try:
        data = json.loads(request.body)
        coupon_code = data.get('coupon_code', '').strip().upper()
        if not coupon_code:
            return JsonResponse({'success': False, 'message': 'Please enter a coupon code'})

        coupon = Coupon.objects.filter(code=coupon_code).first()
        if not coupon:
            return JsonResponse({'success': False, 'message': 'Invalid coupon code'})

        if not coupon.is_valid():
            return JsonResponse({'success': False, 'message': 'This coupon has expired or is no longer valid'})

        _, created = UserCoupon.objects.get_or_create(
            user=request.user, coupon=coupon, defaults={'assigned_at': timezone.now()}
        )
        if not created:
            return JsonResponse({'success': False, 'message': 'You have already saved this coupon'})

        return JsonResponse(
            {'success': True, 'message': f'Coupon {coupon_code} saved successfully! You can now use it for discounts.'}
        )
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Invalid data format'})
    except Exception:
        return JsonResponse({'success': False, 'message': 'An error occurred. Please try again.'})


@login_required
def my_coupons(request):
    """Return user's available coupons"""
    try:
        user_coupons = UserCoupon.objects.filter(user=request.user, is_used=False).select_related('coupon')
        coupons_data = []
        current_time = timezone.now()
        for user_coupon in user_coupons:
            coupon = user_coupon.coupon
            is_expired = current_time > coupon.valid_to or coupon.used_count >= coupon.usage_limit
            coupons_data.append({
                'code': coupon.code,
                'description': coupon.description or '',
                'discount_display': coupon.get_discount_display(),
                'valid_to': coupon.valid_to.strftime('%d %b %Y'),
                'minimum_amount': float(coupon.minimum_amount),
                'usage_limit': coupon.usage_limit,
                'used_count': coupon.used_count,
                'is_expired': is_expired,
            })
        return JsonResponse({'success': True, 'coupons': coupons_data})
    except Exception:
        return JsonResponse({'success': False, 'message': 'Error loading coupons'})


@csrf_exempt
@login_required
def use_coupon(request):
    """Actually use a coupon and track usage - for checkout process"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid request method'})
    try:
        data = json.loads(request.body)
        coupon_code = data.get('coupon_code', '').strip().upper()
        order_amount = float(data.get('order_amount', 0))
        order_id = data.get('order_id')

        if not coupon_code:
            return JsonResponse({'success': False, 'message': 'Please enter a coupon code'})

        coupon = Coupon.objects.filter(code=coupon_code).first()
        if not coupon:
            return JsonResponse({'success': False, 'message': 'Invalid coupon code'})

        if not coupon.can_be_used(order_amount):
            if coupon.status != 'active':
                error = 'This coupon is no longer active.'
            elif not coupon.is_valid():
                error = 'This coupon has expired or reached usage limit.'
            elif order_amount < coupon.minimum_amount:
                error = f'Minimum order amount of ₹{coupon.minimum_amount} required.'
            else:
                error = 'This coupon cannot be applied to your order.'
            return JsonResponse({'success': False, 'message': error})

        if CouponUsage.objects.filter(coupon=coupon, user=request.user).exists():
            return JsonResponse({'success': False, 'message': 'You have already used this coupon'})

        discount_amount = coupon.calculate_discount(order_amount)
        final_amount = order_amount - discount_amount

        CouponUsage.objects.create(
            coupon=coupon,
            user=request.user,
            order_id=order_id,
            discount_amount=discount_amount,
            ip_address=request.META.get('REMOTE_ADDR'),
        )

        coupon.use_coupon()

        UserCoupon.objects.filter(user=request.user, coupon=coupon).update(is_used=True, used_at=timezone.now())

        request.session['applied_coupon'] = {
            'code': coupon.code,
            'discount_amount': float(discount_amount),
            'coupon_id': coupon.id,
        }

        return JsonResponse({
            'success': True,
            'message': f'Coupon applied successfully! You saved ₹{discount_amount}',
            'discount_amount': discount_amount,
            'final_amount': final_amount,
            'coupon_code': coupon.code,
            'discount_display': coupon.get_discount_display(),
        })
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Invalid data format'})
    except Exception:
        return JsonResponse({'success': False, 'message': 'An error occurred. Please try again.'})


def remove_coupon(request):
    """Remove applied coupon"""
    if 'applied_coupon' in request.session:
        del request.session['applied_coupon']
        request.session.modified = True
        return JsonResponse({'success': True, 'message': 'Coupon removed successfully.'})
    return JsonResponse({'success': False, 'message': 'No coupon to remove.'})


def validate_coupon(request):
    """Validate coupon without applying (for real-time validation)"""
    code = request.GET.get('code', '').upper().strip()
    order_amount = float(request.GET.get('order_amount', 0))

    if not code:
        return JsonResponse({'valid': False, 'message': 'Please enter a coupon code.'})

    try:
        coupon = Coupon.objects.get(code=code)
        if coupon.can_be_used(order_amount):
            discount_amount = coupon.calculate_discount(order_amount)
            return JsonResponse({
                'valid': True,
                'message': f'Valid coupon! You will save ₹{discount_amount}',
                'discount_amount': discount_amount,
                'discount_display': coupon.get_discount_display(),
            })
        return JsonResponse({'valid': False, 'message': 'This coupon cannot be applied to your current order.'})
    except Coupon.DoesNotExist:
        return JsonResponse({'valid': False, 'message': 'Invalid coupon code.'})


# ======================== BANNER VIEWS ========================

@login_required
def banner_edit(request):
    """Main banner management page"""
    banners = Banner.objects.all()
    context = {'banners': banners}
    return render(request, 'banner_edit.html', context)


@login_required
def banner_create(request):
    """Create new banner"""
    if request.method == 'POST':
        form = BannerForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Banner created successfully!')
            return redirect('banneredit')
    else:
        form = BannerForm()
    context = {'form': form, 'action': 'Create'}
    return render(request, 'banner_form.html', context)


@login_required
def banner_edit_single(request, pk):
    """Edit existing banner"""
    banner = get_object_or_404(Banner, pk=pk)
    if request.method == 'POST':
        form = BannerForm(request.POST, request.FILES, instance=banner)
        if form.is_valid():
            form.save()
            messages.success(request, 'Banner updated successfully!')
            return redirect('banneredit')
    else:
        form = BannerForm(instance=banner)
    context = {'form': form, 'action': 'Edit', 'banner': banner}
    return render(request, 'banner_form.html', context)


@login_required
def banner_delete(request, pk):
    """Delete banner"""
    banner = get_object_or_404(Banner, pk=pk)
    banner.delete()
    messages.success(request, 'Banner deleted successfully!')
    return redirect('banneredit')


@login_required
def banner_toggle_status(request, pk):
    """Toggle banner active status"""
    banner = get_object_or_404(Banner, pk=pk)
    banner.is_active = not banner.is_active
    banner.save()
    status = 'activated' if banner.is_active else 'deactivated'
    messages.success(request, f'Banner {status} successfully!')
    return redirect('banneredit')


# ======================== OTHER DETAILS (STAT + CTA) ========================

@login_required
def other_details_edit(request):
    """Main other details management page"""
    stat_cards = StatCard.objects.all().order_by('order')
    cta_sections = CTASection.objects.all().order_by('-created_at')
    context = {'stat_cards': stat_cards, 'cta_sections': cta_sections}
    return render(request, 'other_details_edit.html', context)

@login_required
def stat_card_create(request):
    if request.method == 'POST':
        form = StatCardForm(request.POST, request.FILES)
        if form.is_valid():
            stat_card = form.save()
            messages.success(
                request, 
                f'✅ Stat card "{stat_card.label}" has been created successfully!',
                extra_tags='stat_card_created'
            )
            return redirect('other_details_edit')
        else:
            messages.error(
                request,
                '❌ There were errors in your form. Please correct them and try again.',
                extra_tags='form_error'
            )
    else:
        form = StatCardForm()
    context = {'form': form, 'action': 'Create', 'type': 'stat_card'}
    return render(request, 'other_details_form.html', context)

@login_required
def stat_card_edit(request, pk):
    stat_card = get_object_or_404(StatCard, pk=pk)
    if request.method == 'POST':
        form = StatCardForm(request.POST, request.FILES, instance=stat_card)
        if form.is_valid():
            updated_card = form.save()
            messages.success(
                request, 
                f'✏️ Stat card "{updated_card.label}" has been updated successfully!',
                extra_tags='stat_card_updated'
            )
            return redirect('other_details_edit')
        else:
            messages.error(
                request,
                '❌ There were errors in your form. Please correct them and try again.',
                extra_tags='form_error'
            )
    else:
        form = StatCardForm(instance=stat_card)
    context = {'form': form, 'action': 'Edit', 'stat_card': stat_card, 'type': 'stat_card','form_type': 'cta'}
    return render(request, 'other_details_form.html', context)

@login_required
def stat_card_delete(request, pk):
    stat_card = get_object_or_404(StatCard, pk=pk)
    stat_label = stat_card.label  # Store label before deletion
    stat_card.delete()
    messages.success(
        request, 
        f'🗑️ Stat card "{stat_label}" has been deleted successfully!',
        extra_tags='stat_card_deleted'
    )
    return redirect('other_details_edit')

@login_required
def stat_card_toggle_status(request, pk):
    stat_card = get_object_or_404(StatCard, pk=pk)
    stat_card.is_active = not stat_card.is_active
    stat_card.save()
    
    if stat_card.is_active:
        messages.success(
            request, 
            f'👁️ Stat card "{stat_card.label}" has been activated successfully!',
            extra_tags='stat_card_activated'
        )
    else:
        messages.info(
            request, 
            f'👁️‍🗨️ Stat card "{stat_card.label}" has been deactivated successfully!',
            extra_tags='stat_card_deactivated'
        )
    return redirect('other_details_edit')

@login_required
@user_passes_test(is_admin)
def cta_section_create(request):
    """Create a new CTA section."""
    if request.method == 'POST':
        form = CTASectionForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                cta_section = form.save()
                messages.success(
                    request, 
                    f'✓ CTA section "{cta_section.title}" has been created successfully!',
                    extra_tags='success'
                )
                return redirect('other_details_edit')
            except Exception as e:
                messages.error(
                    request,
                    f'✗ Error creating CTA section: {str(e)}',
                    extra_tags='danger'
                )
        else:
            messages.error(
                request,
                '✗ Please correct the errors in the form.',
                extra_tags='danger'
            )
    else:
        form = CTASectionForm()
    
    context = {
        'form': form,
    }
    
    return render(request, 'cta_section_create.html', context)


@login_required
@user_passes_test(is_admin)
def cta_section_edit(request, pk):
    """Edit an existing CTA section."""
    cta_section = get_object_or_404(CTASection, pk=pk)
    
    if request.method == 'POST':
        form = CTASectionForm(request.POST, request.FILES, instance=cta_section)
        if form.is_valid():
            try:
                updated_cta = form.save()
                messages.success(
                    request,
                    f'✓ CTA Section "{updated_cta.title}" has been updated successfully!',
                    extra_tags='success'
                )
                return redirect('other_details_edit')
            except Exception as e:
                messages.error(
                    request,
                    f'✗ Error updating CTA section: {str(e)}',
                    extra_tags='danger'
                )
        else:
            messages.error(
                request,
                '✗ Please correct the errors in the form.',
                extra_tags='danger'
            )
    else:
        form = CTASectionForm(instance=cta_section)
    
    context = {
        'form': form,
        'cta_section': cta_section,
    }
    
    return render(request, 'cta_section_edit.html', context)



@login_required
@user_passes_test(is_admin)
def cta_section_edit(request, pk):
    """Edit an existing CTA section."""
    cta_section = get_object_or_404(CTASection, pk=pk)
    
    if request.method == 'POST':
        form = CTASectionForm(request.POST, request.FILES, instance=cta_section)
        if form.is_valid():
            try:
                form.save()
                messages.success(
                    request,
                    '✓ CTA Section has been updated successfully!',
                    extra_tags='success'
                )
                return redirect('other_details_edit')
            except Exception as e:
                messages.error(
                    request,
                    f'✗ Error updating CTA section: {str(e)}',
                    extra_tags='danger'
                )
        else:
            messages.error(
                request,
                '✗ Please correct the errors in the form.',
                extra_tags='danger'
            )
    else:
        form = CTASectionForm(instance=cta_section)
    
    context = {
        'form': form,
        'cta_section': cta_section,
    }
    
    return render(request, 'cta_section_edit.html', context)


@login_required
def cta_section_delete(request, pk):
    cta_section = get_object_or_404(CTASection, pk=pk)
    cta_title = cta_section.title  # Store title before deletion
    cta_section.delete()
    messages.success(
        request, 
        f'🗑️ CTA section "{cta_title}" has been deleted successfully!',
        extra_tags='cta_section_deleted'
    )
    return redirect('other_details_edit')

@login_required
def cta_section_toggle_status(request, pk):
    cta_section = get_object_or_404(CTASection, pk=pk)
    cta_section.is_active = not cta_section.is_active
    cta_section.save()
    
    if cta_section.is_active:
        messages.success(
            request, 
            f'👁️ CTA section "{cta_section.title}" has been activated successfully!',
            extra_tags='cta_section_activated'
        )
    else:
        messages.info(
            request, 
            f'👁️‍🗨️ CTA section "{cta_section.title}" has been deactivated successfully!',
            extra_tags='cta_section_deactivated'
        )
    return redirect('other_details_edit')

# ======================== ABOUT US ========================

@login_required
def about_us_edit(request):
    """About Us management page"""
    about_us = AboutUsSection.objects.first()
    why_choose_items = WhyChooseUsItem.objects.all()
    service_items = ServiceItem.objects.all()
    context = {
        'about_us': about_us,
        'why_choose_items': why_choose_items,
        'service_items': service_items,
    }
    return render(request, 'about_us_edit.html', context)


@login_required
def about_us_section_edit(request):
    """Edit About Us main section"""
    about_us, _ = AboutUsSection.objects.get_or_create(
        defaults={
            'company_name': 'EduGorilla Community Pvt. Ltd.',
            'heading': 'About EduGorilla',
            'description': (
                "India's fastest-growing one-stop exam prep platform (Trusted by over 4 crore users!).\n"
                'We empower exam aspirants with affordable online live classes, mock tests, e-books, and personalized '
                'learning journeys across 1,600+ national and state exams. Maximize your success with best-in-class '
                'technology, analytics, and top educators!'
            ),
        }
    )

    if request.method == 'POST':
        form = AboutUsSectionForm(request.POST, request.FILES, instance=about_us)
        if form.is_valid():
            form.save()
            messages.success(request, 'About Us section updated successfully!')
            return redirect('about_us_edit')
    else:
        form = AboutUsSectionForm(instance=about_us)

    context = {'form': form, 'action': 'Edit', 'about_us': about_us}
    return render(request, 'about_us_section_form.html', context)


@login_required
def why_choose_create(request):
    if request.method == 'POST':
        form = WhyChooseUsItemForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Why Choose Us item created successfully!')
            return redirect('about_us_edit')
    else:
        form = WhyChooseUsItemForm()
    context = {'form': form, 'action': 'Create', 'type': 'why_choose'}
    return render(request, 'about_us_item_form.html', context)


@login_required
def why_choose_edit(request, pk):
    item = get_object_or_404(WhyChooseUsItem, pk=pk)
    if request.method == 'POST':
        form = WhyChooseUsItemForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, 'Why Choose Us item updated successfully!')
            return redirect('about_us_edit')
    else:
        form = WhyChooseUsItemForm(instance=item)
    context = {'form': form, 'action': 'Edit', 'item': item, 'type': 'why_choose'}
    return render(request, 'about_us_item_form.html', context)


@login_required
def why_choose_delete(request, pk):
    item = get_object_or_404(WhyChooseUsItem, pk=pk)
    item.delete()
    messages.success(request, 'Why Choose Us item deleted successfully!')
    return redirect('about_us_edit')


@login_required
def why_choose_toggle_status(request, pk):
    item = get_object_or_404(WhyChooseUsItem, pk=pk)
    item.is_active = not item.is_active
    item.save()
    status = 'activated' if item.is_active else 'deactivated'
    messages.success(request, f'Why Choose Us item {status} successfully!')
    return redirect('about_us_edit')


@login_required
def service_create(request):
    if request.method == 'POST':
        form = ServiceItemForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Service item created successfully!')
            return redirect('about_us_edit')
    else:
        form = ServiceItemForm()
    context = {'form': form, 'action': 'Create', 'type': 'service'}
    return render(request, 'about_us_item_form.html', context)


@login_required
def service_edit(request, pk):
    item = get_object_or_404(ServiceItem, pk=pk)
    if request.method == 'POST':
        form = ServiceItemForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, 'Service item updated successfully!')
            return redirect('about_us_edit')
    else:
        form = ServiceItemForm(instance=item)
    context = {'form': form, 'action': 'Edit', 'item': item, 'type': 'service'}
    return render(request, 'about_us_item_form.html', context)


@login_required
def service_delete(request, pk):
    item = get_object_or_404(ServiceItem, pk=pk)
    item.delete()
    messages.success(request, 'Service item deleted successfully!')
    return redirect('about_us_edit')


@login_required
def service_toggle_status(request, pk):
    item = get_object_or_404(ServiceItem, pk=pk)
    item.is_active = not item.is_active
    item.save()
    status = 'activated' if item.is_active else 'deactivated'
    messages.success(request, f'Service item {status} successfully!')
    return redirect('about_us_edit')


# ======================== NAVBAR SETTINGS ========================

@login_required
def navbar_settings_edit(request):
    navbar_settings, _ = NavbarSettings.objects.get_or_create(
        defaults={'contact_number': '7905817391', 'contact_hours': '(10 AM to 7 PM)', 'search_placeholder': 'Search courses'}
    )
    if request.method == 'POST':
        form = NavbarSettingsForm(request.POST, request.FILES, instance=navbar_settings)
        if form.is_valid():
            form.save()
            messages.success(request, 'Navbar settings updated successfully!')
            return redirect('navbar_settings_edit')
    else:
        form = NavbarSettingsForm(instance=navbar_settings)
    context = {'form': form, 'navbar_settings': navbar_settings}
    return render(request, 'navbar_settings_form.html', context)


# ======================== FOOTER ========================

@login_required
def footer_edit(request):
    footer_settings = FooterSettings.objects.first()
    footer_links = FooterLink.objects.all()
    footer_legal_links = FooterLegalLink.objects.all()
    context = {
        'footer_settings': footer_settings,
        'footer_links': footer_links,
        'footer_legal_links': footer_legal_links,
    }
    return render(request, 'footer_edit.html', context)


@login_required
def footer_settings_edit(request):
    footer_settings, _ = FooterSettings.objects.get_or_create(
        defaults={'email': 'testseries@edugorilla.com', 'copyright_text': 'Copyright © 2025'}
    )
    if request.method == 'POST':
        form = FooterSettingsForm(request.POST, request.FILES, instance=footer_settings)
        if form.is_valid():
            form.save()
            messages.success(request, 'Footer settings updated successfully!')
            return redirect('footer_edit')
    else:
        form = FooterSettingsForm(instance=footer_settings)
    context = {'form': form, 'footer_settings': footer_settings}
    return render(request, 'footer_settings_form.html', context)


@login_required
def footer_link_create(request):
    if request.method == 'POST':
        form = FooterLinkForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Footer link created successfully!')
            return redirect('footer_edit')
    else:
        form = FooterLinkForm()
    context = {'form': form, 'action': 'Create', 'type': 'footer_link'}
    return render(request, 'footer_link_form.html', context)


@login_required
def footer_link_edit(request, pk):
    footer_link = get_object_or_404(FooterLink, pk=pk)
    if request.method == 'POST':
        form = FooterLinkForm(request.POST, instance=footer_link)
        if form.is_valid():
            form.save()
            messages.success(request, 'Footer link updated successfully!')
            return redirect('footer_edit')
    else:
        form = FooterLinkForm(instance=footer_link)
    context = {'form': form, 'action': 'Edit', 'footer_link': footer_link, 'type': 'footer_link'}
    return render(request, 'footer_link_form.html', context)


@login_required
def footer_link_delete(request, pk):
    footer_link = get_object_or_404(FooterLink, pk=pk)
    footer_link.delete()
    messages.success(request, 'Footer link deleted successfully!')
    return redirect('footer_edit')


@login_required
def footer_link_toggle_status(request, pk):
    footer_link = get_object_or_404(FooterLink, pk=pk)
    footer_link.is_active = not footer_link.is_active
    footer_link.save()
    status = 'activated' if footer_link.is_active else 'deactivated'
    messages.success(request, f'Footer link {status} successfully!')
    return redirect('footer_edit')


@login_required
def footer_legal_create(request):
    if request.method == 'POST':
        form = FooterLegalLinkForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Footer legal link created successfully!')
            return redirect('footer_edit')
    else:
        form = FooterLegalLinkForm()
    context = {'form': form, 'action': 'Create', 'type': 'footer_legal'}
    return render(request, 'footer_link_form.html', context)


@login_required
def footer_legal_edit(request, pk):
    footer_legal = get_object_or_404(FooterLegalLink, pk=pk)
    if request.method == 'POST':
        form = FooterLegalLinkForm(request.POST, instance=footer_legal)
        if form.is_valid():
            form.save()
            messages.success(request, 'Footer legal link updated successfully!')
            return redirect('footer_edit')
    else:
        form = FooterLegalLinkForm(instance=footer_legal)
    context = {'form': form, 'action': 'Edit', 'footer_legal': footer_legal, 'type': 'footer_legal'}
    return render(request, 'footer_link_form.html', context)


@login_required
def footer_legal_delete(request, pk):
    footer_legal = get_object_or_404(FooterLegalLink, pk=pk)
    footer_legal.delete()
    messages.success(request, 'Footer legal link deleted successfully!')
    return redirect('footer_edit')


@login_required
def footer_legal_toggle_status(request, pk):
    footer_legal = get_object_or_404(FooterLegalLink, pk=pk)
    footer_legal.is_active = not footer_legal.is_active
    footer_legal.save()
    status = 'activated' if footer_legal.is_active else 'deactivated'
    messages.success(request, f'Footer legal link {status} successfully!')
    return redirect('footer_edit')


# ======================== CATEGORIES ========================

@login_required
def manage_categories(request):
    categories = Category.objects.all().order_by('-created_at')
    paginator = Paginator(categories, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {'categories': page_obj, 'total_categories': categories.count()}
    return render(request, 'adminpanel/manage_categories.html', context)


@login_required
def create_category(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        if name:
            if Category.objects.filter(name__iexact=name).exists():
                messages.error(request, 'Category with this name already exists.')
            else:
                category = Category.objects.create(name=name, description=description, slug=slugify(name)[:140])
                messages.success(request, f'Category "{category.name}" created successfully.')
                return redirect('manage_categories')
        else:
            messages.error(request, 'Category name is required.')
    return render(request, 'adminpanel/create_category.html')


@login_required
def edit_category(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        if name:
            if Category.objects.filter(name__iexact=name).exclude(id=category.id).exists():
                messages.error(request, 'Another category with this name already exists.')
            else:
                category.name = name
                category.description = description
                category.slug = slugify(name)[:140]
                category.save()
                messages.success(request, f'Category "{category.name}" updated successfully.')
                return redirect('manage_categories')
        else:
            messages.error(request, 'Category name is required.')
    context = {'category': category}
    return render(request, 'adminpanel/edit_category.html', context)


@login_required
def delete_category(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    if request.method == 'POST':
        category_name = category.name
        category.delete()
        messages.success(request, f'Category "{category_name}" deleted successfully.')
        return redirect('manage_categories')
    context = {'category': category}
    return render(request, 'adminpanel/delete_category.html', context)


# ======================== SMTP CONFIG ========================

@login_required
def smtp_configuration(request):
    configurations = SMTPConfiguration.objects.all()
    active_config = configurations.filter(is_active=True).first()
    context = {
        'configurations': configurations,
        'active_config': active_config,
        'total_configs': configurations.count(),
        'tested_configs': configurations.filter(test_status='success').count(),
    }
    return render(request, 'adminpanel/smtp_configuration.html', context)


@login_required
def smtp_create(request):
    if request.method == 'POST':
        try:
            is_active = request.POST.get('is_active') == 'on'
            if is_active:
                SMTPConfiguration.objects.filter(is_active=True).update(is_active=False)

            config = SMTPConfiguration.objects.create(
                name=request.POST.get('name'),
                email_backend=request.POST.get('email_backend'),
                email_host=request.POST.get('email_host'),
                email_port=int(request.POST.get('email_port')),
                email_use_tls=request.POST.get('email_use_tls') == 'on',
                email_use_ssl=request.POST.get('email_use_ssl') == 'on',
                email_host_user=request.POST.get('email_host_user'),
                email_host_password=request.POST.get('email_host_password'),
                default_from_email=request.POST.get('default_from_email'),
                is_active=is_active,
            )
            messages.success(request, f'SMTP configuration "{config.name}" created successfully.')
            return redirect('smtp_configuration')
        except Exception as e:
            messages.error(request, f'Error creating SMTP configuration: {str(e)}')
    return render(request, 'adminpanel/smtp_create.html')


@login_required
def smtp_edit(request, config_id):
    config = get_object_or_404(SMTPConfiguration, id=config_id)
    if request.method == 'POST':
        try:
            is_active = request.POST.get('is_active') == 'on'
            if is_active and not config.is_active:
                SMTPConfiguration.objects.filter(is_active=True).update(is_active=False)

            config.name = request.POST.get('name')
            config.email_backend = request.POST.get('email_backend')
            config.email_host = request.POST.get('email_host')
            config.email_port = int(request.POST.get('email_port'))
            config.email_use_tls = request.POST.get('email_use_tls') == 'on'
            config.email_use_ssl = request.POST.get('email_use_ssl') == 'on'
            config.email_host_user = request.POST.get('email_host_user')
            config.email_host_password = request.POST.get('email_host_password')
            config.default_from_email = request.POST.get('default_from_email')
            config.is_active = is_active
            config.save()

            messages.success(request, f'SMTP configuration "{config.name}" updated successfully.')
            return redirect('smtp_configuration')
        except Exception as e:
            messages.error(request, f'Error updating SMTP configuration: {str(e)}')
    context = {'config': config}
    return render(request, 'adminpanel/smtp_edit.html', context)


@login_required
@require_POST
def smtp_test(request, config_id):
    """Test SMTP configuration via AJAX"""
    config = get_object_or_404(SMTPConfiguration, id=config_id)
    config.test_status = 'pending'
    config.save(update_fields=['test_status'])
    try:
        success, message = config.test_connection()
    except Exception as e:
        success = False
        message = f'Unexpected error during test: {str(e)}'
        config.test_status = 'failed'
        config.save(update_fields=['test_status'])

    last_tested = config.last_tested.strftime('%m/%d/%Y %H:%M:%S') if config.last_tested else None
    return JsonResponse(
        {'success': success, 'message': message, 'last_tested': last_tested, 'test_status': config.test_status}
    )


@login_required
def smtp_delete(request, config_id):
    config = get_object_or_404(SMTPConfiguration, id=config_id)
    if request.method == 'POST':
        config_name = config.name
        config.delete()
        messages.success(request, f'SMTP configuration "{config_name}" deleted successfully.')
        return redirect('smtp_configuration')
    context = {'config': config}
    return render(request, 'adminpanel/smtp_delete.html', context)


#bundles views
def is_admin(user):
    """Check if user is admin"""
    return user.is_authenticated and (user.is_staff or user.is_superuser)


@login_required
@user_passes_test(is_admin)
def bundle_manage(request):
    """List and manage all bundles"""
    bundles = ProductBundle.objects.all().select_related('category').prefetch_related(
        'video_courses', 'live_classes', 'test_series', 'elibrary_courses'
    )
    
    # Apply filters
    filter_form = BundleFilterForm(request.GET)
    if filter_form.is_valid():
        search = filter_form.cleaned_data.get('search')
        category = filter_form.cleaned_data.get('category')
        bundle_type = filter_form.cleaned_data.get('bundle_type')
        status = filter_form.cleaned_data.get('status')
        is_featured = filter_form.cleaned_data.get('is_featured')
        is_free = filter_form.cleaned_data.get('is_free')
        
        if search:
            bundles = bundles.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search)
            )
        
        if category:
            bundles = bundles.filter(category=category)
        
        if bundle_type:
            bundles = bundles.filter(bundle_type=bundle_type)
        
        if status:
            bundles = bundles.filter(status=status)
        
        if is_featured is not None:
            bundles = bundles.filter(is_featured=is_featured)
        
        if is_free is not None:
            bundles = bundles.filter(is_free=is_free)
    
    # Pagination
    paginator = Paginator(bundles, 15)
    page = request.GET.get('page')
    bundles = paginator.get_page(page)
    
    context = {
        'bundles': bundles,
        'filter_form': filter_form,
        'total_bundles': ProductBundle.objects.count(),
        'active_bundles': ProductBundle.objects.filter(status='active').count(),
        'featured_bundles': ProductBundle.objects.filter(is_featured=True).count(),
        'free_bundles': ProductBundle.objects.filter(is_free=True).count(),
    }
    
    return render(request, 'bundles/bundle_manage.html', context)


def is_admin(user):
    """Check if user is admin"""
    return user.is_staff or user.is_superuser


@login_required
@user_passes_test(is_admin)
def bundle_create(request):
    """Create a new bundle"""
    if request.method == 'POST':
        form = ProductBundleForm(request.POST, request.FILES)
        if form.is_valid():
            bundle = form.save(commit=False)
            bundle.created_by = request.user
            bundle.save()
            form.save_m2m()  # Save many-to-many relationships
            messages.success(request, f'Bundle "{bundle.title}" created successfully!')
            return redirect('bundle_manage')
        else:
            # Show detailed error messages
            if form.errors:
                for field, errors in form.errors.items():
                    for error in errors:
                        if field == '__all__':
                            messages.error(request, f'{error}')
                        else:
                            messages.error(request, f'{field}: {error}')
            else:
                messages.error(request, 'Please correct the errors below.')
    else:
        form = ProductBundleForm()
    
    context = {
        'form': form,
        'mode': 'create',
        'video_courses': VideoCourse.objects.all(),
        'live_classes': LiveClassCourse.objects.filter(is_active=True),
        'test_series': TestSeries.objects.filter(is_active=True),
        'elibrary_courses': ELibraryCourse.objects.filter(is_active=True),
    }
    
    return render(request, 'bundles/bundle_form.html', context)


@login_required
@user_passes_test(is_admin)
def bundle_edit(request, pk):
    """Edit an existing bundle"""
    bundle = get_object_or_404(ProductBundle, id=pk)
    
    if request.method == 'POST':
        form = ProductBundleForm(request.POST, request.FILES, instance=bundle)
        if form.is_valid():
            bundle = form.save()
            messages.success(request, f'Bundle "{bundle.title}" updated successfully!')
            return redirect('bundle_manage')
        else:
            # Show detailed error messages
            if form.errors:
                for field, errors in form.errors.items():
                    for error in errors:
                        if field == '__all__':
                            messages.error(request, f'{error}')
                        else:
                            messages.error(request, f'{field}: {error}')
            else:
                messages.error(request, 'Please correct the errors below.')
    else:
        form = ProductBundleForm(instance=bundle)
    
    context = {
        'form': form,
        'mode': 'edit',
        'bundle': bundle,
        'video_courses': VideoCourse.objects.all(),
        'live_classes': LiveClassCourse.objects.filter(is_active=True),
        'test_series': TestSeries.objects.filter(is_active=True),
        'elibrary_courses': ELibraryCourse.objects.filter(is_active=True),
    }
    
    return render(request, 'bundles/bundle_form.html', context)

@login_required
@user_passes_test(is_admin)
def bundle_detail(request, pk):
    """View bundle details"""
    bundle = get_object_or_404(
        ProductBundle.objects.prefetch_related(
            'video_courses', 'live_classes', 'test_series', 'elibrary_courses',
            'enrollments', 'reviews'
        ),
        pk=pk
    )
    
    # Get statistics
    total_enrollments = bundle.enrollments.filter(payment_status='completed').count()
    total_revenue = bundle.enrollments.filter(
        payment_status='completed'
    ).aggregate(Sum('amount_paid'))['amount_paid__sum'] or 0
    
    avg_rating = bundle.reviews.aggregate(models.Avg('rating'))['rating__avg'] or 0
    
    # Recent enrollments
    recent_enrollments = bundle.enrollments.select_related('user').order_by('-created_at')[:10]
    
    # Reviews
    reviews = bundle.reviews.filter(is_approved=True).select_related('user').order_by('-created_at')[:5]
    
    context = {
        'bundle': bundle,
        'total_enrollments': total_enrollments,
        'total_revenue': total_revenue,
        'avg_rating': round(avg_rating, 2),
        'recent_enrollments': recent_enrollments,
        'reviews': reviews,
    }
    
    return render(request, 'bundles/bundle_detail.html', context)


@login_required
@user_passes_test(is_admin)
def bundle_delete(request, pk):
    """Delete a bundle"""
    bundle = get_object_or_404(ProductBundle, pk=pk)
    title = bundle.title
    bundle.delete()
    messages.success(request, f'Bundle "{title}" deleted successfully!')
    return redirect('bundle_manage')


@login_required
@user_passes_test(is_admin)
def bundle_toggle_status(request, pk):
    """Toggle bundle status (active/inactive)"""
    bundle = get_object_or_404(ProductBundle, pk=pk)
    
    if bundle.status == 'active':
        bundle.status = 'inactive'
        message = 'deactivated'
    else:
        bundle.status = 'active'
        message = 'activated'
    
    bundle.save()
    messages.success(request, f'Bundle "{bundle.title}" {message} successfully!')
    
    return redirect('bundle_manage')


@login_required
@user_passes_test(is_admin)
def bundle_toggle_featured(request, pk):
    """Toggle featured status"""
    bundle = get_object_or_404(ProductBundle, pk=pk)
    bundle.is_featured = not bundle.is_featured
    bundle.save()
    
    status = 'featured' if bundle.is_featured else 'unfeatured'
    messages.success(request, f'Bundle "{bundle.title}" {status} successfully!')
    
    return redirect('bundle_manage')


@login_required
@user_passes_test(is_admin)
def bundle_calculate_price(request):
    """AJAX endpoint to calculate original price from selected products"""
    if request.method == 'POST':
        video_course_ids = request.POST.getlist('video_courses[]')
        live_class_ids = request.POST.getlist('live_classes[]')
        test_series_ids = request.POST.getlist('test_series[]')
        elibrary_ids = request.POST.getlist('elibrary_courses[]')
        
        total = 0
        
        # Calculate from video courses
        if video_course_ids:
            video_total = VideoCourse.objects.filter(
                id__in=video_course_ids
            ).aggregate(Sum('selling_price'))['selling_price__sum'] or 0
            total += float(video_total)
        
        # Calculate from live classes
        if live_class_ids:
            live_total = LiveClassCourse.objects.filter(
                id__in=live_class_ids
            ).aggregate(Sum('current_price'))['current_price__sum'] or 0
            total += float(live_total)
        
        # Calculate from test series
        if test_series_ids:
            test_total = TestSeries.objects.filter(
                id__in=test_series_ids,
                is_free=False
            ).aggregate(Sum('price'))['price__sum'] or 0
            total += float(test_total)
        
        # Calculate from e-library courses
        if elibrary_ids:
            elibrary_total = ELibraryCourse.objects.filter(
                id__in=elibrary_ids
            ).aggregate(
                total=Sum('discount_price')
            )['total'] or 0
            
            # If discount price is null, use regular price
            if elibrary_total == 0:
                elibrary_total = ELibraryCourse.objects.filter(
                    id__in=elibrary_ids
                ).aggregate(Sum('price'))['price__sum'] or 0
            
            total += float(elibrary_total)
        
        return JsonResponse({
            'success': True,
            'total_price': round(total, 2)
        })
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})

