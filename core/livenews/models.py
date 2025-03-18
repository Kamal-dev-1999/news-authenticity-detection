from django.db import models
from django.utils import timezone
class LiveNews(models.Model):
    VERIFICATION_CHOICES = [
        ('gemini', 'Gemini AI'),
        ('basic', 'Basic Model'), 
        ('error', 'Error')
    ]

    # Core article information
    title = models.CharField(max_length=500)
    news_category = models.CharField(max_length=100)
    web_url = models.URLField(max_length=600, unique=True)
    img_url = models.URLField(max_length=600, blank=True)
    publication_date = models.DateTimeField(
        default=timezone.now,
        help_text="Original article publication date"
    )
    # Content and metadata
    content = models.TextField(blank=True)
    section_id = models.CharField(max_length=200, blank=True)
    section_name = models.CharField(max_length=200, blank=True)
    type = models.CharField(max_length=200, default='article')
    
    # Verification information
    prediction = models.BooleanField(
        default=True,
        help_text="True = Real News, False = Fake News"
    )
    expires_at = models.DateTimeField(
        default=timezone.now() + timezone.timedelta(hours=24),
        help_text="Article will be automatically removed after this time"
    )
    verification_method = models.CharField(
        max_length=20,
        choices=VERIFICATION_CHOICES,
        default='basic'
    )
    verification_details = models.JSONField(
        null=True,
        blank=True,
        help_text="Stores detailed verification analysis"
    )

    # Automatic timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Live News Article"
        verbose_name_plural = "Live News Articles"
        ordering = ['-publication_date']
        indexes = [
            models.Index(fields=['publication_date']),
            models.Index(fields=['news_category']),
            models.Index(fields=['verification_method']),
        ]