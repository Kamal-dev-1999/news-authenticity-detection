# In your core/urls.py (or wherever your API routes are defined)
from django.urls import path, include
from rest_framework import routers
from core.usercheckbytitle.viewsets import UserCheckViewSet
from core.livenews.viewsets import (
    LiveNewsPrediction, 
    LiveNewsByCategory, 
    NewsDashboardView,
    verify_news  # Make sure this is imported
)
from core.newsquiz.viewsets import NewsQuizViewSet

app_name = 'core'
router = routers.SimpleRouter()

# Existing API routes
router.register(r'usercheck/title', UserCheckViewSet, basename='game')
router.register(r'live', LiveNewsPrediction, basename='live')
router.register(r'quiz', NewsQuizViewSet, basename='quiz')
router.register(r'category/(?P<category>[^/.]+)', LiveNewsByCategory, basename='livenews-by-category')

# Add template-based routes
urlpatterns = [
    path('dashboard/', NewsDashboardView.as_view(), name='news-dashboard'),
    path('verify-news/', verify_news, name='verify-news'),
    path('api/', include(router.urls)),  # Move router URLs under /api/
]