from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Q
import json

# Import models
from video_courses.models import Category
from testseries.models import TestSeries, Test, Question, Subject


@login_required
# @user_passes_test(is_admin)
def test_series_delete(request, pk):
    """Delete a test series"""
    series = get_object_or_404(TestSeries, pk=pk)
    if request.method == 'POST':
        title = series.title
        series.delete()
        messages.success(request, f'Test series "{title}" has been deleted successfully.')
        return redirect('test_series_manage')
    return redirect('test_series_manage')

    
# ---------------------------------------------
# Utility Functions
# ---------------------------------------------
def is_admin(user):
    return user.is_superuser or user.is_staff

# ---------------------------------------------
# Test Series Management Views
# ---------------------------------------------
@login_required
@user_passes_test(is_admin)
def test_series_manage(request):
    """Manage all test series courses"""
    search_query = request.GET.get('search', '')
    category_filter = request.GET.get('category', '')

    test_series = TestSeries.objects.select_related('category').prefetch_related('tests')

    # Apply filters
    if search_query:
        test_series = test_series.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query)
        )

    if category_filter:
        test_series = test_series.filter(category_id=category_filter)

    test_series = test_series.order_by('-created_at')

    # Add stats
    for series in test_series:
        series.total_tests = series.tests.count()
        series.total_questions = sum(test.questions.count() for test in series.tests.all())
        series.total_marks = sum(sum(q.marks for q in test.questions.all()) for test in series.tests.all())

    # Pagination
    paginator = Paginator(test_series, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    categories = Category.objects.all().order_by('name')

    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'category_filter': category_filter,
        'categories': categories,
    }
    return render(request, 'testseries/manage.html', context)

# ---------------------------------------------
# Create Test Series Course
# ---------------------------------------------
@login_required
@user_passes_test(is_admin)
def test_series_create(request):
    """Create new test series course"""
    if request.method == 'POST':
        title = request.POST.get('title')
        category_id = request.POST.get('category')
        description = request.POST.get('description')
        difficulty = request.POST.get('difficulty')
        estimated_duration = request.POST.get('estimated_duration')
        is_free = request.POST.get('is_free') == 'on'
        price = request.POST.get('price', 0)
        has_negative_marking = request.POST.get('has_negative_marking') == 'on'
        negative_marks = request.POST.get('negative_marks', 0.25)
        pass_percentage = request.POST.get('pass_percentage', 40)
        is_featured = request.POST.get('is_featured') == 'on'
        thumbnail = request.FILES.get('thumbnail')

        try:
            category = Category.objects.get(id=category_id)
            test_series = TestSeries.objects.create(
                title=title,
                category=category,
                description=description,
                difficulty=difficulty,
                estimated_duration=estimated_duration,
                is_free=is_free,
                price=price if not is_free else 0,
                has_negative_marking=has_negative_marking,
                negative_marks=negative_marks,
                pass_percentage=pass_percentage,
                is_featured=is_featured,
                thumbnail=thumbnail,
            )
            messages.success(request, f'✅ Test series course "{title}" created successfully! You can now schedule tests under it.')
            return redirect('test_series_detail', pk=test_series.pk)

        except Category.DoesNotExist:
            messages.error(request, '❌ Selected category does not exist. Please select a valid category.')
        except Exception as e:
            messages.error(request, f'❌ Error creating test series course: {str(e)}')

    categories = Category.objects.all().order_by('name')
    return render(request, 'testseries/create.html', {'categories': categories})

# ---------------------------------------------
# Test Series Detail - View All Scheduled Tests
# ---------------------------------------------
@login_required
@user_passes_test(is_admin)
def test_series_detail(request, pk):
    """View all scheduled tests in a series"""
    test_series = get_object_or_404(TestSeries, pk=pk)
    tests = test_series.tests.prefetch_related('questions').order_by('created_at')

    for test in tests:
        test.question_count = test.questions.count()
        test.total_marks = sum(q.marks for q in test.questions.all())
        test.difficulty_breakdown = {
            'easy': test.questions.filter(difficulty='easy').count(),
            'medium': test.questions.filter(difficulty='medium').count(),
            'hard': test.questions.filter(difficulty='hard').count(),
        }

    context = {
        'test_series': test_series,
        'tests': tests,
        'total_questions': sum(test.question_count for test in tests),
        'total_marks': sum(test.total_marks for test in tests),
    }
    return render(request, 'testseries/detail.html', context)

# ---------------------------------------------
# Edit Test Series Course
# ---------------------------------------------
@login_required
@user_passes_test(is_admin)
def test_series_edit(request, pk):
    """Edit test series course"""
    test_series = get_object_or_404(TestSeries, pk=pk)

    if request.method == 'POST':
        old_title = test_series.title
        test_series.title = request.POST.get('title')
        test_series.category = Category.objects.get(id=request.POST.get('category'))
        test_series.description = request.POST.get('description')
        test_series.difficulty = request.POST.get('difficulty')
        test_series.estimated_duration = request.POST.get('estimated_duration')
        test_series.is_free = request.POST.get('is_free') == 'on'
        test_series.price = request.POST.get('price', 0) if not test_series.is_free else 0
        test_series.has_negative_marking = request.POST.get('has_negative_marking') == 'on'
        test_series.negative_marks = request.POST.get('negative_marks', 0.25)
        test_series.pass_percentage = request.POST.get('pass_percentage', 40)
        test_series.is_featured = request.POST.get('is_featured') == 'on'
        test_series.is_active = request.POST.get('is_active') == 'on'

        if request.FILES.get('thumbnail'):
            test_series.thumbnail = request.FILES.get('thumbnail')

        try:
            test_series.save()
            messages.success(request, f'✅ Test series course "{old_title}" updated successfully!')
            return redirect('test_series_detail', pk=test_series.pk)
        except Exception as e:
            messages.error(request, f'❌ Error updating test series course: {str(e)}')

    categories = Category.objects.all().order_by('name')
    return render(request, 'testseries/edit.html', {'test_series': test_series, 'categories': categories})

# ---------------------------------------------
# Create Scheduled Test
# ---------------------------------------------
@login_required
@user_passes_test(is_admin)
def test_create(request, series_pk):
    """Schedule a new test for a series"""
    test_series = get_object_or_404(TestSeries, pk=series_pk)

    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        duration_minutes = request.POST.get('duration_minutes')
        max_attempts = request.POST.get('max_attempts', 1)
        shuffle_questions = request.POST.get('shuffle_questions') == 'on'
        show_result_immediately = request.POST.get('show_result_immediately') == 'on'
        allow_review = request.POST.get('allow_review') == 'on'
        start_time = request.POST.get('start_time')
        end_time = request.POST.get('end_time')

        try:
            test = Test.objects.create(
                test_series=test_series,
                title=title,
                description=description,
                duration_minutes=duration_minutes,
                max_attempts=max_attempts,
                shuffle_questions=shuffle_questions,
                show_result_immediately=show_result_immediately,
                allow_review=allow_review,
                start_time=start_time if start_time else None,
                end_time=end_time if end_time else None,
            )
            messages.success(
                request,
                f'✅ Scheduled test "{title}" created successfully under "{test_series.title}"! Now add questions to complete the test.'
            )
            return redirect('test_edit', pk=test.pk)

        except Exception as e:
            messages.error(request, f'❌ Error creating scheduled test: {str(e)}')

    return render(request, 'testseries/test_create.html', {'test_series': test_series})

# ---------------------------------------------
# Edit Scheduled Test
# ---------------------------------------------
@login_required
@user_passes_test(is_admin)
def test_edit(request, pk):
    """Edit scheduled test and manage questions"""
    test = get_object_or_404(Test, pk=pk)

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'update_test':
            old_title = test.title
            test.title = request.POST.get('title')
            test.description = request.POST.get('description')
            test.duration_minutes = request.POST.get('duration_minutes')
            test.max_attempts = request.POST.get('max_attempts')
            test.shuffle_questions = request.POST.get('shuffle_questions') == 'on'
            test.show_result_immediately = request.POST.get('show_result_immediately') == 'on'
            test.allow_review = request.POST.get('allow_review') == 'on'
            test.is_active = request.POST.get('is_active') == 'on'

            start_time = request.POST.get('start_time')
            end_time = request.POST.get('end_time')
            test.start_time = start_time if start_time else None
            test.end_time = end_time if end_time else None

            try:
                test.save()
                messages.success(request, f'✅ Scheduled test "{old_title}" updated successfully!')
            except Exception as e:
                messages.error(request, f'❌ Error updating scheduled test: {str(e)}')

    questions = test.questions.select_related('subject').order_by('order')
    subjects = Subject.objects.filter(is_active=True)

    # Test statistics
    test.question_count = questions.count()
    test.total_marks = sum(q.marks for q in questions)
    test.difficulty_stats = {
        'easy': questions.filter(difficulty='easy').count(),
        'medium': questions.filter(difficulty='medium').count(),
        'hard': questions.filter(difficulty='hard').count(),
    }

    # Subject-wise breakdown
    test.subject_stats = {}
    for question in questions:
        subject = question.subject.name if question.subject else 'General'
        test.subject_stats[subject] = test.subject_stats.get(subject, 0) + 1

    context = {
        'test': test,
        'questions': questions,
        'subjects': subjects,
    }
    return render(request, 'testseries/test_edit.html', context)

# ---------------------------------------------
# Create Question
# ---------------------------------------------
@login_required
@user_passes_test(is_admin)
def question_create(request, test_pk):
    """Create new question for a scheduled test"""
    test = get_object_or_404(Test, pk=test_pk)

    if request.method == 'POST':
        question_text = request.POST.get('question_text')
        question_type = request.POST.get('question_type')
        difficulty = request.POST.get('difficulty')
        marks = request.POST.get('marks', 1)
        negative_marks = request.POST.get('negative_marks', 0.25)
        subject_id = request.POST.get('subject')
        explanation = request.POST.get('explanation', '')
        question_image = request.FILES.get('question_image')
        solution_image = request.FILES.get('solution_image')

        # Determine order
        last_question = test.questions.order_by('-order').first()
        order = (last_question.order + 1) if last_question else 1

        # Prepare options and answers
        options = {}
        correct_answer = {}

        if question_type in ['mcq_single', 'mcq_multiple']:
            for i in range(1, 5):  # 4 options (a–d)
                option_text = request.POST.get(f'option_{i}')
                if option_text:
                    options[chr(96 + i)] = option_text  # a, b, c, d

            if question_type == 'mcq_single':
                correct_answer = request.POST.get('correct_answer')
            else:
                correct_answer = request.POST.getlist('correct_answers')

        elif question_type == 'true_false':
            options = {'a': 'True', 'b': 'False'}
            correct_answer = request.POST.get('correct_answer')

        elif question_type in ['fill_blank', 'numerical']:
            correct_answer = request.POST.get('correct_answer')

        try:
            subject = Subject.objects.get(id=subject_id) if subject_id else None
            Question.objects.create(
                test=test,
                subject=subject,
                question_type=question_type,
                difficulty=difficulty,
                question_text=question_text,
                question_image=question_image,
                marks=marks,
                negative_marks=negative_marks,
                options=options,
                correct_answer=correct_answer,
                explanation=explanation,
                solution_image=solution_image,
                order=order,
            )
            messages.success(
                request,
                f'✅ Question #{order} added successfully to "{test.title}"! Test now has {test.questions.count()} questions.'
            )
            return redirect('test_edit', pk=test.pk)

        except Exception as e:
            messages.error(request, f'❌ Error creating question: {str(e)}')

    subjects = Subject.objects.filter(is_active=True)
    return render(request, 'testseries/question_create.html', {'test': test, 'subjects': subjects})
