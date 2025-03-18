from django.contrib import admin
from .models import LiveNews
from django.utils.html import format_html
@admin.register(LiveNews)
class LiveNewsAdmin(admin.ModelAdmin):
    list_display = ('title', 'news_category', 'prediction', 'verification_status', 'publication_date')
    list_filter = ('prediction', 'verification_method', 'news_category')
    search_fields = ('title', 'content')
    readonly_fields = ('verification_details_preview',)
    
    def verification_status(self, obj):
        return obj.get_verification_method_display()
    
    def verification_details_preview(self, obj):
        if obj.verification_details:
            return format_html(
                "<strong>Confidence:</strong> {}<br>"
                "<strong>Key Reasons:</strong><ul>{}</ul>"
                "<strong>Suggested Checks:</strong><ul>{}</ul>",
                obj.verification_details.get('confidence', 'N/A'),
                "".join(f"<li>{reason}</li>" for reason in obj.verification_details.get('reasons', [])),
                "".join(f"<li>{check}</li>" for check in obj.verification_details.get('suggested_checks', []))
            )
        return "N/A"
    
    verification_details_preview.short_description = "Verification Analysis"