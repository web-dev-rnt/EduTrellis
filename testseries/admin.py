from django.contrib import admin
from django.urls import path, reverse
from django.utils.html import format_html
from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse
from video_courses.models import Category
from .models import TestSeries, Test, Question, Subject, TestAttempt, StudentAnswer

class QuestionInline(admin.TabularInline):
    model = Question
    extra = 1
    fields = ('order', 'question_text', 'question_type', 'difficulty', 'marks')
    ordering = ('order',)

class TestAdmin(admin.ModelAdmin):
    list_display = ('title', 'test_series', 'render_test_button', 'duration_minutes', 'total_questions', 'max_attempts', 'is_active')
    list_filter = ('test_series', 'is_active')
    search_fields = ('title',)
    inlines = [QuestionInline]
    prepopulated_fields = {'slug': ('title',)}

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                '<path:object_id>/render-test/',
                self.admin_site.admin_view(self.render_test_view),
                name='test-series-test-render',
            ),
        ]
        return custom_urls + urls

    def render_test_view(self, request, object_id, *args, **kwargs):
        test = get_object_or_404(Test, pk=object_id)
        questions = test.questions.all().order_by('order')
        
        context = dict(
            self.admin_site.each_context(request),
            test=test,
            questions=questions,
            total_questions=questions.count(),
            total_marks=sum(q.marks for q in questions),
        )
        return TemplateResponse(request, "admin/render_test.html", context)

    def render_test_button(self, obj):
        if obj.pk:
            url = reverse('admin:test-series-test-render', args=[obj.pk])
            return format_html('<a class="button" href="{}" target="_blank" style="background: #417690; color: white; padding: 4px 8px; text-decoration: none; border-radius: 4px;">🔍 Preview Test</a>', url)
        return "-"
    render_test_button.short_description = 'Preview'
    render_test_button.allow_tags = True

class TestSeriesAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'difficulty', 'total_tests', 'is_active', 'created_at')
    list_filter = ('category', 'difficulty', 'is_active')
    search_fields = ('title', 'description')
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ('total_tests', 'total_attempts', 'average_score')

class TestAttemptAdmin(admin.ModelAdmin):
    list_display = ('user', 'test', 'attempt_number', 'status', 'percentage_score', 'marks_obtained', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('user__username', 'test__title')

class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'code')

# Register models
admin.site.register(TestSeries, TestSeriesAdmin)
admin.site.register(Test, TestAdmin)
admin.site.register(Question)
admin.site.register(Subject, SubjectAdmin)
admin.site.register(TestAttempt, TestAttemptAdmin)
admin.site.register(StudentAnswer)
