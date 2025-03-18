# views.py
from rest_framework.response import Response
from rest_framework import viewsets, status
import requests
from .models import LiveNews
from .serializers import LiveNewsDetailedSerializer
import threading
import time
from rest_framework.views import APIView
from django.utils import timezone
from django.shortcuts import render
from django.views import View
import google.generativeai as genai
from django.conf import settings
import re
import json
from bs4 import BeautifulSoup
import datetime
from django.utils.dateparse import parse_datetime
from django.db.models import Q
from django.http import JsonResponse
import os
from core.model import get_models
# Configure Gemini API
genai.configure(api_key=settings.GEMINI_API_KEY)
safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]
model = genai.GenerativeModel('gemini-2.0-flash', safety_settings=safety_settings)
from django.views.decorators.cache import never_cache
from django.utils.decorators import method_decorator

@method_decorator(never_cache, name='dispatch')
class NewsDashboardView(View):
    template_name = 'news_dashboard.html'

    def get(self, request):
        now = timezone.now()
        query = request.GET.get('q', '')
        
        articles = LiveNews.objects.filter(
            expires_at__gt=now
        ).order_by('-publication_date')

        if query:
            articles = articles.filter(
                Q(title__icontains=query) |
                Q(news_category__icontains=query)
            )

        context = {
            'articles': articles[:50],
            'categories': LiveNews.objects.values_list('news_category', flat=True).distinct(),
            'current_time': now,
            'refresh_interval': 300,
            'search_query': query
        }
        return render(request, self.template_name, context)


# views.py
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json
from django.views.decorators.http import require_POST
import google.generativeai as genai
genai.configure(api_key=settings.GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.0-flash')
@csrf_exempt
@require_POST
def verify_news(request):
    try:
        # Validate request
        if request.content_type != 'application/json':
            return JsonResponse({'error': 'Invalid content type'}, status=415)
        
        data = json.loads(request.body)
        user_input = data.get('input', '')
        
        if not user_input:
            return JsonResponse({'error': 'Empty input'}, status=400)

        # Try Gemini verification first
        try:
            response = model.generate_content(
                f"""Analyze this news for authenticity. Format response as JSON with:
                - verdict (Genuine/Fake/Unverified)
                - confidence (1-100)
                - reasons (array of strings)
                - sources (array of credible sources checked)
                News content: {user_input}"""
            )
            
            result = json.loads(response.text)
            return JsonResponse({
                'verdict': result.get('verdict', 'Unverified'),
                'confidence': result.get('confidence', 0),
                'details': result.get('reasons', []),
                'sources': result.get('sources', []),
                'method': 'gemini'
            })

        except Exception as e:
            # Fallback to local model if Gemini fails
            try:
                from core.model import get_models
                nb_model, vect_model = get_models()
                
                # Vectorize the input
                vectorized_input = vect_model.transform([user_input])
                
                # Make prediction
                prediction = nb_model.predict(vectorized_input)
                confidence = nb_model.predict_proba(vectorized_input)[0].max() * 100
                
                return JsonResponse({
                    'verdict': 'Genuine' if prediction[0] == 1 else 'Fake',
                    'confidence': round(float(confidence), 1),
                    'details': ['Local model prediction'],
                    'sources': ['Internal verification system'],
                    'method': 'local'
                })
                
            except Exception as model_error:
                return JsonResponse({
                    'error': f'Both verifications failed: {str(model_error)}'
                }, status=500)

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
        
        
# Date handling utilities
def safe_parse_date(value):
    """Safely parse dates from various formats"""
    if isinstance(value, str):
        try:
            # Try ISO format first
            return datetime.datetime.fromisoformat(value)
        except ValueError:
            try:
                # Try Django's parser
                return parse_datetime(value)
            except (ValueError, TypeError):
                pass
    return timezone.now()

# Content extraction
def get_article_content(url):
    """Extract main content from article URL"""
    try:
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Updated selectors for The Guardian's layout
        content_div = soup.select_one('div[data-gu-name="body"]') or soup.select_one('article')
        if not content_div:
            return "Content not available"
            
        paragraphs = content_div.find_all('p')
        return '\n'.join([p.get_text().strip() for p in paragraphs[:15]])
    except Exception as e:
        print(f"Content extraction failed: {str(e)}")
        return ""

# Verification system
def analyze_with_gemini(title, content):
    """Analyze news using Gemini API"""
    try:
        prompt = f"""Analyze this news article for authenticity. Return JSON with:
        - "verdict": "true" or "false"
        - "confidence": "high/medium/low"
        - "reasons": list of strings
        - "checks": list of strings

        Title: {title}
        Content: {content[:3000]}"""

        response = model.generate_content(prompt)
        json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
        
        if not json_match:
            return None
            
        analysis = json.loads(json_match.group())
        return {
            'prediction': analysis.get('verdict') == 'true',
            'details': analysis,
            'method': 'gemini'
        }
    except Exception as e:
        print(f"Gemini analysis failed: {str(e)}")
        return None

def basic_verification(title):
    """Fallback verification using ML model"""
    try:
        from core.model import load_models, nb_model
        vectorized = load_models.transform([title])
        return nb_model.predict(vectorized)[0] == 1
    except Exception as e:
        print(f"Basic verification failed: {str(e)}")
        return False

def verify_article(article):
    """Hybrid verification workflow"""
    content = get_article_content(article.get('webUrl', ''))
    title = article.get('webTitle', '')
    
    gemini_result = analyze_with_gemini(title, content)
    if gemini_result:
        return gemini_result
    
    return {
        'prediction': basic_verification(title),
        'method': 'basic',
        'details': None
    }

# News updater
def get_new_news_from_api_and_update():
    """Main news update process"""
    LiveNews.objects.filter(expires_at__lte=timezone.now()).delete()
    try:
        params = {
            "api-key": "e705adff-ca49-414e-89e2-7edede919e2e",
            "order-by": "newest",
            "show-fields": "thumbnail,body",
            "page-size": 50
        }
        print("Fetching from Guardian API...")
        response = requests.get("https://content.guardianapis.com/search", params=params)
        print(f"API Status: {response.status_code}")
        
        articles = response.json().get("response", {}).get("results", [])
        print(f"Received {len(articles)} articles")

        for article in articles:
            web_url = article.get('webUrl')
            print(f"\nProcessing: {web_url}")
            
            if not web_url:
                print("Skipping - No URL")
                continue
                
            if LiveNews.objects.filter(web_url=web_url).exists():
                print("Skipping - Already exists")
                continue
        response = requests.get("https://content.guardianapis.com/search", params=params)
        articles = response.json().get("response", {}).get("results", [])

        for article in articles:
            web_url = article.get('webUrl')
            if not web_url or LiveNews.objects.filter(web_url=web_url).exists():
                continue

            verification = verify_article(article)
            pub_date = safe_parse_date(article.get('webPublicationDate'))
            
            LiveNews.objects.update_or_create(
                web_url=web_url,
                defaults={
                    'title': article.get('webTitle', ''),
                    'publication_date': pub_date,
                    'news_category': article.get('pillarName', 'General'),
                    'img_url': article.get('fields', {}).get('thumbnail', ''),
                    'content': verification.get('content', ''),
                    'prediction': verification['prediction'],
                    'verification_method': verification['method'],
                    'verification_details': verification['details'],
                    'section_id': article.get('sectionId', ''),
                    'section_name': article.get('sectionName', ''),
                    'type': article.get('type', 'article')
                }
            )

    except Exception as e:
        print(f"News update error: {str(e)}")

# Background updater
def auto_refresh_news():
    while True:
        try:
            # Remove 10% oldest articles each cycle
            cutoff = timezone.now() - timezone.timedelta(hours=2)
            LiveNews.objects.filter(
                publication_date__lt=cutoff
            ).delete()
            
            get_new_news_from_api_and_update()
            time.sleep(300)
            
        except Exception as e:
            print(f"Updater crashed: {str(e)}")
            time.sleep(60)  # Wait before restarting

# Initialize background thread
update_thread = threading.Thread(target=auto_refresh_news, daemon=True)
update_thread.start()

# # Views
# class NewsDashboardView(View):
#     template_name = 'news_dashboard.html'

#     def get(self, request):
#         context = {
#             'articles': LiveNews.objects.order_by('-publication_date')[:50],
#             'categories': LiveNews.objects.values_list('news_category', flat=True).distinct()
#         }
#         return render(request, self.template_name, context)

class LiveNewsPrediction(viewsets.ViewSet):
    http_method_names = ('get',)

    def list(self, request):
        queryset = LiveNews.objects.order_by('-publication_date')[:50]
        serializer = LiveNewsDetailedSerializer(queryset, many=True)
        return Response({
            'count': len(queryset),
            'results': serializer.data,
            'gemini_verified': LiveNews.objects.filter(verification_method='gemini').count()
        })

class LiveNewsByCategory(viewsets.ViewSet):
    def list(self, request, category=None):
        if not category:
            return Response({"error": "Category required"}, status=status.HTTP_400_BAD_REQUEST)
            
        queryset = LiveNews.objects.filter(
            news_category__iexact=category
        ).order_by('-publication_date')[:50]
        serializer = LiveNewsDetailedSerializer(queryset, many=True)
        return Response(serializer.data)

class DebugNewsView(APIView):
    def get(self, request):
        latest_db = LiveNews.objects.order_by('-publication_date').first()
        return Response({
            'database_latest': {
                'title': latest_db.title if latest_db else None,
                'date': latest_db.publication_date if latest_db else None
            },
            'server_time': timezone.now()
        })