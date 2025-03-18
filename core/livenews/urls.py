from django.urls import path
from .viewsets import NewsDashboardView, verify_news

urlpatterns = [
    path('dashboard/', NewsDashboardView.as_view(), name='news-dashboard'),
    path('api/verify-news/', verify_news, name='verify-news'),
    
    # Keep your existing API URLs
]