from django.shortcuts import render, redirect, get_object_or_404
from django.db import transaction
from django.urls import reverse
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.db import models
import json
from video_courses.models import VideoCourse
from .forms import VideoCourseForm, LearnFormSet, IncludeFormSet, VideoFormSet




def video_course_create(request):
    """Create a new video course with formsets"""
    course = None
    
    if request.method == "POST":
        form = VideoCourseForm(request.POST, request.FILES, instance=course)
        learn_fs = LearnFormSet(request.POST, instance=course, prefix="learn")
        include_fs = IncludeFormSet(request.POST, instance=course, prefix="incl")
        video_fs = VideoFormSet(request.POST, request.FILES, instance=course, prefix="vid")



        # Validate all forms
        if form.is_valid() and learn_fs.is_valid() and include_fs.is_valid() and video_fs.is_valid():
            try:
                with transaction.atomic():
                    # Save the main course
                    course = form.save()
                    
                    # Set the course instance for each formset
                    learn_fs.instance = course
                    include_fs.instance = course
                    video_fs.instance = course
                    
                    # Save all formsets
                    learn_fs.save()
                    include_fs.save()
                    video_fs.save()
                
                course_type = "free" if course.is_free else "paid"
                messages.success(request, f"Video course '{course.name}' created successfully as a {course_type} course!")
                return redirect(reverse("video_course_edit_by_pk", kwargs={"pk": course.pk}))
                
            except Exception as e:
                messages.error(request, f"Error creating course: {str(e)}")
                
        else:
            # Collect all form errors for better debugging
            all_errors = []
            
            # Form field errors
            if form.errors:
                for field, errors in form.errors.items():
                    for error in errors:
                        all_errors.append(f"Course {field}: {error}")
            
            # Form non-field errors
            if form.non_field_errors():
                all_errors.extend([f"Course: {error}" for error in form.non_field_errors()])
            
            # Learning formset errors
            if learn_fs.errors:
                for i, form_errors in enumerate(learn_fs.errors):
                    if form_errors:
                        for field, errors in form_errors.items():
                            for error in errors:
                                all_errors.append(f"Learning point {i+1} {field}: {error}")
            
            if learn_fs.non_form_errors():
                all_errors.extend([f"Learning points: {error}" for error in learn_fs.non_form_errors()])
            
            # Includes formset errors
            if include_fs.errors:
                for i, form_errors in enumerate(include_fs.errors):
                    if form_errors:
                        for field, errors in form_errors.items():
                            for error in errors:
                                all_errors.append(f"Include {i+1} {field}: {error}")
            
            if include_fs.non_form_errors():
                all_errors.extend([f"Includes: {error}" for error in include_fs.non_form_errors()])
            
            # Videos formset errors
            if video_fs.errors:
                for i, form_errors in enumerate(video_fs.errors):
                    if form_errors:
                        for field, errors in form_errors.items():
                            for error in errors:
                                all_errors.append(f"Video {i+1} {field}: {error}")
            
            if video_fs.non_form_errors():
                all_errors.extend([f"Videos: {error}" for error in video_fs.non_form_errors()])
            
            # Display errors
            if all_errors:
                for error in all_errors[:5]:  # Limit to first 5 errors
                    messages.error(request, error)
                if len(all_errors) > 5:
                    messages.error(request, f"... and {len(all_errors) - 5} more errors")
            else:
                messages.error(request, "Please correct the errors in the form fields.")
    else:
        # GET request - initialize empty forms
        form = VideoCourseForm()
        learn_fs = LearnFormSet(prefix="learn")
        include_fs = IncludeFormSet(prefix="incl")
        video_fs = VideoFormSet(prefix="vid")


    
    return render(request, "video_course_create.html", {
        "form": form,
        "learn_fs": learn_fs,
        "include_fs": include_fs,
        "video_fs": video_fs,
        "course": course,
        "mode": "create",
    })



def video_course_manage(request):
    """View to display all video courses in a table for management"""
    # Get search query and filter options
    search_query = request.GET.get('q', '').strip()
    course_type_filter = request.GET.get('type', '').strip()  # 'free', 'paid', or empty
    
    try:
        # Base queryset with optimizations
        courses = VideoCourse.objects.select_related("category").prefetch_related("videos").order_by("-updated_at")
        
        # Apply search filter if provided
        if search_query:
            courses = courses.filter(
                models.Q(name__icontains=search_query) |
                models.Q(category__name__icontains=search_query) |
                models.Q(instructor_name__icontains=search_query)
            )
        
        # Apply course type filter
        if course_type_filter == 'free':
            courses = courses.filter(is_free=True)
        elif course_type_filter == 'paid':
            courses = courses.filter(is_free=False)
        
        # Calculate stats
        total_courses = VideoCourse.objects.count()
        free_courses = VideoCourse.objects.filter(is_free=True).count()
        paid_courses = VideoCourse.objects.filter(is_free=False).count()
        
        # Check if model has is_active field
        if hasattr(VideoCourse, 'is_active'):
            active_courses = VideoCourse.objects.filter(is_active=True).count()
        else:
            active_courses = total_courses
        
        # Calculate additional stats
        total_videos = sum(course.videos.count() for course in courses)
        avg_rating = VideoCourse.objects.aggregate(models.Avg('rating'))['rating__avg'] or 0
        
    except Exception as e:
        courses = VideoCourse.objects.none()
        search_query = ""
        course_type_filter = ""
        total_courses = 0
        active_courses = 0
        free_courses = 0
        paid_courses = 0
        total_videos = 0
        avg_rating = 0
        messages.error(request, f"Error loading courses: {str(e)}")
    
    context = {
        "courses": courses,
        "search_query": search_query,
        "course_type_filter": course_type_filter,
        "total_courses": total_courses,
        "active_courses": active_courses,
        "free_courses": free_courses,
        "paid_courses": paid_courses,
        "total_videos": total_videos,
        "avg_rating": round(avg_rating, 1),
    }
    
    return render(request, "video_course_manage.html", context)




def video_course_edit(request, slug):
    """Edit course by slug - legacy function"""
    try:
        course = get_object_or_404(VideoCourse, slug=slug)
        print(f"Editing course: {course}")
        # Redirect to PK-based edit
        return redirect('video_course_edit_by_pk', pk=course.pk)
    except Exception as e:
        messages.error(request, f"Course not found: {str(e)}")
        return redirect('video_course_create')




def video_course_edit_by_pk(request, pk):
    """Edit an existing video course by primary key"""
    try:
        course = get_object_or_404(VideoCourse, pk=pk)
    except Exception as e:
        messages.error(request, f"Course not found: {str(e)}")
        return redirect('video_course_create')



    if request.method == "POST":
        form = VideoCourseForm(request.POST, request.FILES, instance=course)
        learn_fs = LearnFormSet(request.POST, instance=course, prefix="learn")
        include_fs = IncludeFormSet(request.POST, instance=course, prefix="incl")
        video_fs = VideoFormSet(request.POST, request.FILES, instance=course, prefix="vid")



        if form.is_valid() and learn_fs.is_valid() and include_fs.is_valid() and video_fs.is_valid():
            try:
                with transaction.atomic():
                    course = form.save()
                    learn_fs.save()
                    include_fs.save()
                    video_fs.save()
                
                course_type = "free" if course.is_free else "paid"
                messages.success(request, f"Video course '{course.name}' updated successfully as a {course_type} course!")
                return redirect(reverse("video_course_edit_by_pk", kwargs={"pk": course.pk}))
                
            except Exception as e:
                messages.error(request, f"Error updating course: {str(e)}")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        # GET request - initialize forms with existing data
        form = VideoCourseForm(instance=course)
        learn_fs = LearnFormSet(instance=course, prefix="learn")
        include_fs = IncludeFormSet(instance=course, prefix="incl")
        video_fs = VideoFormSet(instance=course, prefix="vid")



    # Fetch all existing courses for the table
    try:
        courses = VideoCourse.objects.select_related("category").prefetch_related("videos").order_by("-updated_at")
        total_courses = courses.count()
        free_courses = courses.filter(is_free=True).count()
        paid_courses = courses.filter(is_free=False).count()
        
        # Check if model has is_active field
        if hasattr(VideoCourse, 'is_active'):
            active_courses = courses.filter(is_active=True).count()
        else:
            active_courses = total_courses
            
    except Exception as e:
        courses = VideoCourse.objects.none()
        total_courses = 0
        active_courses = 0
        free_courses = 0
        paid_courses = 0
        messages.error(request, f"Error loading courses: {str(e)}")



    return render(request, "video_course_create.html", {
        "form": form,
        "learn_fs": learn_fs,
        "include_fs": include_fs,
        "video_fs": video_fs,
        "course": course,
        "courses": courses,
        "total_courses": total_courses,
        "active_courses": active_courses,
        "free_courses": free_courses,
        "paid_courses": paid_courses,
        "mode": "edit",
    })



@csrf_exempt
def video_course_delete(request, pk):
    """Delete a video course - supports both AJAX and regular POST"""
    if request.method != "POST":
        return JsonResponse({"success": False, "error": "Only POST method allowed"}, status=405)
    
    try:
        # Get the course
        course = get_object_or_404(VideoCourse, pk=pk)
        course_name = course.name
        
        # Count related objects before deletion for logging
        video_count = 0
        try:
            if hasattr(course, 'videos'):
                video_count = course.videos.count()
        except Exception:
            pass  # Ignore if videos relation doesn't exist
        
        # Delete the course
        with transaction.atomic():
            course.delete()
        
        success_message = f"Course '{course_name}' deleted successfully!"
        if video_count > 0:
            success_message += f" ({video_count} videos also removed)"
        
        # Handle AJAX request
        if (request.headers.get('X-Requested-With') == 'XMLHttpRequest' or 
            request.content_type == 'application/json' or
            'application/json' in request.META.get('HTTP_ACCEPT', '')):
            
            return JsonResponse({
                "success": True,
                "message": success_message
            })
        
        # Handle regular form POST (fallback)
        messages.success(request, success_message)
        return redirect(reverse("video_course_create"))
        
    except VideoCourse.DoesNotExist:
        error_message = "Course not found or already deleted"
        
        if (request.headers.get('X-Requested-With') == 'XMLHttpRequest' or 
            request.content_type == 'application/json' or
            'application/json' in request.META.get('HTTP_ACCEPT', '')):
            
            return JsonResponse({"success": False, "error": error_message}, status=404)
        
        messages.error(request, error_message)
        return redirect(reverse("video_course_create"))
        
    except Exception as e:
        error_message = f"Failed to delete course: {str(e)}"
        
        if (request.headers.get('X-Requested-With') == 'XMLHttpRequest' or 
            request.content_type == 'application/json' or
            'application/json' in request.META.get('HTTP_ACCEPT', '')):
            
            return JsonResponse({"success": False, "error": error_message}, status=500)
        
        messages.error(request, error_message)
        return redirect(reverse("video_course_create"))




@csrf_exempt 
def video_course_toggle_status(request, pk):
    """Toggle course active status - AJAX only"""
    if request.method != "POST":
        return JsonResponse({"success": False, "error": "Only POST method allowed"}, status=405)
    
    try:
        course = get_object_or_404(VideoCourse, pk=pk)
        
        # Check if the model has is_active field
        if not hasattr(course, 'is_active'):
            return JsonResponse({
                "success": False,
                "error": "Course status toggle is not supported for this model"
            }, status=400)
        
        # Toggle status
        course.is_active = not course.is_active
        course.save(update_fields=['is_active'])
        
        status_text = "activated" if course.is_active else "deactivated"
        
        return JsonResponse({
            "success": True,
            "message": f"Course '{course.name}' {status_text} successfully!",
            "is_active": course.is_active
        })
        
    except VideoCourse.DoesNotExist:
        return JsonResponse({"success": False, "error": "Course not found"}, status=404)
        
    except Exception as e:
        return JsonResponse({
            "success": False,
            "error": f"Failed to update course status: {str(e)}"
        }, status=500)
