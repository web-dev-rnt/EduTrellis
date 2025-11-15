# live_class/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib import messages
from django.db import transaction
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.utils.dateparse import parse_datetime
from django.contrib.auth import authenticate, login
from django.conf import settings
import json
import hashlib
import secrets

from .models import LiveClassSession, LiveClassCourse
from .forms import LiveClassCourseForm


# Utility functions
def generate_room_name(session_id, class_name):
    """Generate a unique room name for the session"""
    unique_string = f"{session_id}_{class_name}_{secrets.token_hex(8)}"
    room_hash = hashlib.md5(unique_string.encode()).hexdigest()[:12]
    return f"LiveClass_{room_hash}"


def is_room_moderator(user):
    """Determine if user should be a moderator"""
    return user.is_staff or user.is_superuser


# Course Management Views
def live_class_course_manage(request):
    """Display and filter live class courses"""
    courses = LiveClassCourse.objects.select_related('category').all()
    
    # Search filter
    q = request.GET.get('q')
    if q:
        courses = courses.filter(name__icontains=q)
    
    # Course type filter (free/paid)
    course_type = request.GET.get('type')
    if course_type == 'free':
        courses = courses.filter(is_free=True)
    elif course_type == 'paid':
        courses = courses.filter(is_free=False)
    
    return render(request, "live_classes/live_class_course_manage.html", {
        "courses": courses,
        "selected_type": course_type,
    })


def live_class_course_create(request):
    """Create a new live class course"""
    if request.method == "POST":
        form = LiveClassCourseForm(request.POST, request.FILES)
        if form.is_valid():
            course = form.save()
            messages.success(request, "Live class course created successfully.")
            return redirect('liveclass')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = LiveClassCourseForm()
    return render(request, "live_classes/live_class_course_create.html", {
        "form": form,
    })


def live_class_course_edit(request, pk):
    """Edit an existing live class course"""
    course = get_object_or_404(LiveClassCourse, pk=pk)
    if request.method == "POST":
        form = LiveClassCourseForm(request.POST, request.FILES, instance=course)
        if form.is_valid():
            form.save()
            messages.success(request, "Live class course updated successfully.")
            return redirect('liveclass')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = LiveClassCourseForm(instance=course)
    return render(request, "live_classes/live_class_course_edit.html", {
        "form": form,
        "course": course,
    })


@require_POST
def live_class_course_delete(request, pk):
    """Delete a live class course"""
    course = get_object_or_404(LiveClassCourse, pk=pk)
    course.delete()
    messages.success(request, "Live class course deleted.")
    return redirect('liveclass')


@require_POST
def live_class_course_toggle_status(request, pk):
    """Toggle active status of a course"""
    course = get_object_or_404(LiveClassCourse, pk=pk)
    course.is_active = not course.is_active
    course.save()
    return JsonResponse({
        'success': True, 
        'status': course.is_active, 
        'message': 'Course status updated.'
    })


def live_class_course_classes(request, pk):
    """Get all classes for a specific course"""
    course = get_object_or_404(LiveClassCourse, pk=pk)
    classes = [{
        "id": s.id,
        "class_name": s.class_name,
        "scheduled_datetime": s.scheduled_datetime.strftime("%b %d, %Y, %I:%M %p"),
        "duration_minutes": s.duration_minutes,
        "max_participants": s.max_participants,
        "is_free": s.is_free,
        "enable_auto_recording": s.enable_auto_recording,
        "subject": s.subject or "-",
    } for s in course.sessions.all()]
    return JsonResponse({
        "course_name": course.name,
        "is_course_free": course.is_free,
        "classes": classes
    })


# Session Management Views
@csrf_exempt
def add_scheduled_class(request, course_id):
    """Add a new scheduled class to a course"""
    if request.method != "POST":
        return HttpResponseBadRequest()
    
    course = get_object_or_404(LiveClassCourse, pk=course_id)
    
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({
            "success": False, 
            "error": "Invalid JSON data."
        }, status=400)
    
    # Validate datetime
    scheduled_dt = parse_datetime(data.get("scheduled_datetime"))
    if not scheduled_dt:
        return JsonResponse({
            "success": False, 
            "error": "Invalid date/time format."
        }, status=400)
    
    # Check if datetime is within course duration
    if scheduled_dt.date() < course.start_date or scheduled_dt.date() > course.end_date:
        return JsonResponse({
            "success": False, 
            "error": "Class must be scheduled within course start and end dates."
        }, status=400)

    try:
        # Create session with transaction safety
        with transaction.atomic():
            session = LiveClassSession.objects.create(
                course=course,
                class_name=data.get("class_name", "").strip(),
                enable_auto_recording=bool(data.get("enable_auto_recording", False)),
                scheduled_datetime=scheduled_dt,
                duration_minutes=int(data.get("duration_minutes", 60)),
                max_participants=100,
                is_free=bool(data.get("is_free", False)),
                subject=data.get("subject", "").strip(),
            )
        return JsonResponse({
            "success": True, 
            "id": session.id, 
            "message": "Class scheduled successfully."
        })
    except Exception as e:
        return JsonResponse({
            "success": False, 
            "error": f"Failed to create session: {str(e)}"
        }, status=500)


@csrf_exempt
def live_class_schedule_delete(request, session_id):
    """Delete a scheduled class"""
    if request.method != "POST":
        return HttpResponseBadRequest("Only POST method allowed")
    
    session = get_object_or_404(LiveClassSession, id=session_id)
    
    try:
        session.delete()
        return JsonResponse({
            "success": True, 
            "message": "Class schedule deleted successfully."
        })
    except Exception as e:
        return JsonResponse({
            "success": False, 
            "error": f"Failed to delete session: {str(e)}"
        }, status=500)


# Live Session View
def live_class_join(request, session_id):
    """Join a live class session - works for both authenticated and guest users"""
    session = get_object_or_404(LiveClassSession, id=session_id)
    
    # Generate unique room name for this session
    room_name = generate_room_name(session_id, session.class_name)
    
    # Base context for all users
    context = {
        'session': session,
        'jitsi_domain': getattr(settings, 'JITSI_DOMAIN', 'meet.ffmuc.net'),
        'room_name': room_name,
    }
    
    # Add user-specific context based on authentication status
    if request.user.is_authenticated:
        # Authenticated user context
        context.update({
            'display_name': request.user.get_full_name() or request.user.email,
            'user_email': request.user.email,
            'is_moderator': is_room_moderator(request.user),
        })
    else:
        # Guest user context (will be populated by frontend)
        context.update({
            'display_name': '',
            'user_email': '',
            'is_moderator': False,
        })
    
    return render(request, 'live_classes/live_session.html', context)
