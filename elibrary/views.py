import os
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse, HttpResponse, Http404
from django.db.models import Q, Count, Sum
from django.core.paginator import Paginator
from django.utils import timezone
from django.db import transaction
from video_courses.models import Category
from .models import ELibraryCourse, ELibraryPDF, ELibraryEnrollment, ELibraryDownload
from .forms import ELibraryCourseForm, ELibraryPDFForm, MultiplePDFUploadForm, ELibraryPDFFormSet


def is_admin(user):
    """Check if user is admin or staff member."""
    return user.is_staff or user.is_superuser


# ==================== Course Management Views ====================

@login_required
@user_passes_test(is_admin)
def elibrary_manage(request):
    """Main management view for E-Library courses with filters and stats."""
    search_query = request.GET.get('search', '')
    category_filter = request.GET.get('category', '')
    difficulty_filter = request.GET.get('difficulty', '')
    status_filter = request.GET.get('status', '')

    # Base queryset with optimizations
    courses = ELibraryCourse.objects.select_related(
        'category', 
        'created_by'
    ).prefetch_related('pdfs')

    # Apply search filter
    if search_query:
        courses = courses.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(instructor__icontains=search_query) |
            Q(tags__icontains=search_query)
        )

    # Apply category filter
    if category_filter:
        courses = courses.filter(category_id=category_filter)

    # Apply difficulty filter
    if difficulty_filter:
        courses = courses.filter(difficulty_level=difficulty_filter)

    # Apply status filter
    if status_filter == 'active':
        courses = courses.filter(is_active=True)
    elif status_filter == 'inactive':
        courses = courses.filter(is_active=False)

    # Pagination
    paginator = Paginator(courses, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Get categories for filter dropdown
    categories = Category.objects.all()
    
    # Calculate dashboard statistics
    stats = {
        'total_courses': ELibraryCourse.objects.count(),
        'active_courses': ELibraryCourse.objects.filter(is_active=True).count(),
        'total_pdfs': ELibraryPDF.objects.count(),
        'total_enrollments': ELibraryEnrollment.objects.count(),
        'total_revenue': ELibraryEnrollment.objects.filter(
            payment_status='completed'
        ).aggregate(total=Sum('amount_paid'))['total'] or 0,
    }

    context = {
        'page_obj': page_obj,
        'categories': categories,
        'stats': stats,
        'search_query': search_query,
        'category_filter': category_filter,
        'difficulty_filter': difficulty_filter,
        'status_filter': status_filter,
        'difficulty_choices': ELibraryCourse.DIFFICULTY_CHOICES,
    }

    return render(request, 'elibrary_manage.html', context)


@login_required
@user_passes_test(is_admin)
def elibrary_course_create(request):
    """Create a new E-Library course."""
    if request.method == 'POST':
        form = ELibraryCourseForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                course = form.save(commit=False)
                course.created_by = request.user
                course.save()
                messages.success(
                    request, 
                    f'✓ Course "{course.title}" has been created successfully! '
                    f'You can now add PDFs to this course.',
                    extra_tags='success'
                )
                return redirect('elibrary_course_detail', pk=course.pk)
            except Exception as e:
                messages.error(
                    request,
                    f'✗ Error creating course: {str(e)}',
                    extra_tags='danger'
                )
        else:
            messages.error(
                request,
                '✗ Please correct the errors below.',
                extra_tags='danger'
            )
    else:
        form = ELibraryCourseForm()

    return render(request, 'elibrary_create.html', {'form': form})


@login_required
@user_passes_test(is_admin)
def elibrary_course_edit(request, pk):
    """Edit an existing E-Library course."""
    course = get_object_or_404(ELibraryCourse, pk=pk)
    
    if request.method == 'POST':
        form = ELibraryCourseForm(request.POST, request.FILES, instance=course)
        if form.is_valid():
            try:
                updated_course = form.save()
                messages.success(
                    request, 
                    f'✓ Course "{updated_course.title}" has been updated successfully!',
                    extra_tags='success'
                )
                return redirect('elibrary_course_detail', pk=updated_course.pk)
            except Exception as e:
                messages.error(
                    request,
                    f'✗ Error updating course: {str(e)}',
                    extra_tags='danger'
                )
        else:
            messages.error(
                request,
                '✗ Please correct the errors in the form.',
                extra_tags='danger'
            )
    else:
        form = ELibraryCourseForm(instance=course)

    context = {
        'form': form,
        'item': course,
        'is_edit': True
    }

    return render(request, 'elibrary_edit.html', context)


@login_required
@user_passes_test(is_admin)
def elibrary_course_detail(request, pk):
    """Display detailed information about a course."""
    course = get_object_or_404(
        ELibraryCourse.objects.select_related('category', 'created_by')
        .prefetch_related('pdfs'), 
        pk=pk
    )
    
    # Organize PDFs by chapter
    pdfs_by_chapter = {}
    for pdf in course.pdfs.filter(is_active=True).order_by('chapter_number', 'order'):
        if pdf.chapter_number not in pdfs_by_chapter:
            pdfs_by_chapter[pdf.chapter_number] = []
        pdfs_by_chapter[pdf.chapter_number].append(pdf)

    # Calculate enrollment statistics
    enrollment_stats = {
        'total': ELibraryEnrollment.objects.filter(course=course).count(),
        'completed': ELibraryEnrollment.objects.filter(
            course=course, 
            payment_status='completed'
        ).count(),
        'pending': ELibraryEnrollment.objects.filter(
            course=course, 
            payment_status='pending'
        ).count(),
    }

    # Process tags into a list
    course_tags = []
    if course.tags:
        course_tags = [tag.strip() for tag in course.tags.split(',') if tag.strip()]

    context = {
        'course': course,
        'course_tags': course_tags,
        'pdfs_by_chapter': pdfs_by_chapter,
        'enrollment_stats': enrollment_stats,
    }

    return render(request, 'elibrary_course_detail.html', context)


@login_required
@user_passes_test(is_admin)
def elibrary_course_delete(request, pk):
    """Delete a course and its associated files."""
    course = get_object_or_404(ELibraryCourse, pk=pk)
    
    if request.method == 'POST':
        try:
            # Store course title before deletion
            course_title = course.title
            pdf_count = course.pdfs.count()
            
            # Delete associated PDF files
            deleted_files = 0
            for pdf in course.pdfs.all():
                if pdf.file:
                    try:
                        if os.path.exists(pdf.file.path):
                            os.remove(pdf.file.path)
                            deleted_files += 1
                    except OSError as e:
                        messages.warning(
                            request,
                            f'⚠ Could not delete file: {pdf.title}',
                            extra_tags='warning'
                        )
            
            # Delete cover image
            if course.cover_image:
                try:
                    if os.path.exists(course.cover_image.path):
                        os.remove(course.cover_image.path)
                except OSError:
                    pass
            
            # Delete preview PDF
            if course.preview_pdf:
                try:
                    if os.path.exists(course.preview_pdf.path):
                        os.remove(course.preview_pdf.path)
                except OSError:
                    pass
            
            # Delete the course
            course.delete()
            
            messages.success(
                request, 
                f'✓ Course "{course_title}" has been deleted successfully! '
                f'({deleted_files}/{pdf_count} PDF files removed)',
                extra_tags='success'
            )
            return redirect('elibrary_manage')
            
        except Exception as e:
            messages.error(
                request,
                f'✗ Error deleting course: {str(e)}',
                extra_tags='danger'
            )
    
    return redirect('elibrary_course_detail', pk=pk)


@login_required
@user_passes_test(is_admin)
def elibrary_toggle_course_status(request, pk):
    """Toggle course active/inactive status."""
    course = get_object_or_404(ELibraryCourse, pk=pk)
    
    try:
        course.is_active = not course.is_active
        course.save()
        
        status = "activated" if course.is_active else "deactivated"
        icon = "✓" if course.is_active else "⏸"
        
        messages.success(
            request, 
            f'{icon} Course "{course.title}" has been {status}.',
            extra_tags='success'
        )
    except Exception as e:
        messages.error(
            request,
            f'✗ Error changing course status: {str(e)}',
            extra_tags='danger'
        )
    
    return redirect('elibrary_manage')


# ==================== PDF Management Views ====================

@login_required
@user_passes_test(is_admin)
def elibrary_pdf_upload_multiple(request, course_pk):
    """Upload multiple PDF files to a course."""
    course = get_object_or_404(ELibraryCourse, pk=course_pk)
    
    if request.method == 'POST':
        form = MultiplePDFUploadForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                files = form.cleaned_data['pdfs']
                chapter_number = form.cleaned_data['chapter_number']
                auto_title = form.cleaned_data['auto_title']
                
                created_count = 0
                failed_count = 0
                
                with transaction.atomic():
                    for index, pdf_file in enumerate(files):
                        try:
                            # Generate title
                            if auto_title:
                                title = os.path.splitext(pdf_file.name)[0]
                            else:
                                title = f"PDF {index + 1}"
                            
                            # Create PDF object
                            pdf_obj = ELibraryPDF.objects.create(
                                course=course,
                                title=title,
                                file=pdf_file,
                                chapter_number=chapter_number,
                                order=index,
                                uploaded_by=request.user
                            )
                            created_count += 1
                            
                        except Exception as e:
                            failed_count += 1
                            messages.warning(
                                request,
                                f'⚠ Failed to upload {pdf_file.name}: {str(e)}',
                                extra_tags='warning'
                            )
                    
                    # Update course metadata
                    course.save()
                
                # Success notification
                if created_count > 0:
                    messages.success(
                        request, 
                        f'✓ {created_count} PDF(s) uploaded successfully to "{course.title}"!'
                        f'{f" ({failed_count} failed)" if failed_count > 0 else ""}',
                        extra_tags='success'
                    )
                    return redirect('elibrary_course_detail', pk=course.pk)
                else:
                    messages.error(
                        request,
                        f'✗ No PDFs were uploaded. All {failed_count} files failed.',
                        extra_tags='danger'
                    )
                    
            except Exception as e:
                messages.error(
                    request,
                    f'✗ Error during upload: {str(e)}',
                    extra_tags='danger'
                )
        else:
            messages.error(
                request,
                '✗ Please correct the errors in the form.',
                extra_tags='danger'
            )
    else:
        form = MultiplePDFUploadForm()

    context = {
        'form': form, 
        'course': course
    }

    return render(request, 'elibrary_pdf_upload_multiple.html', context)

@login_required
@user_passes_test(is_admin)
def elibrary_pdf_delete(request, pk):
    """Delete a single PDF from a course."""
    pdf = get_object_or_404(ELibraryPDF, pk=pk)
    course = pdf.course
    
    if request.method == 'POST':
        try:
            # Store PDF details before deletion
            pdf_title = pdf.title
            course_title = course.title
            
            # Delete the physical file
            if pdf.file:
                try:
                    if os.path.exists(pdf.file.path):
                        os.remove(pdf.file.path)
                except OSError as e:
                    messages.warning(
                        request,
                        f'⚠ Could not delete file from storage, but database entry was removed.',
                        extra_tags='warning'
                    )
            
            # Delete the PDF object
            pdf.delete()
            
            # Update course metadata
            course.save()
            
            messages.success(
                request, 
                f'✓ PDF "{pdf_title}" has been deleted successfully from "{course_title}".',
                extra_tags='success'
            )
            
        except Exception as e:
            messages.error(
                request,
                f'✗ Error deleting PDF: {str(e)}',
                extra_tags='danger'
            )
    
    return redirect('elibrary_course_detail', pk=course.pk)
