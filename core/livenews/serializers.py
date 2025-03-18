from rest_framework import serializers
from .models import LiveNews


class LiveNewsSerializer(serializers.ModelSerializer):
    """Serializes the required fields from the `LiveNews` model"""
    class Meta:
        model = LiveNews
        fields = (
                    'id', 'title', 'publication_date',
                    'news_category', 'prediction', 'img_url',
                 )

class LiveNewsDetailedSerializer(serializers.ModelSerializer):
    verification_status = serializers.SerializerMethodField()
    confidence_level = serializers.SerializerMethodField()
    
    def get_verification_status(self, obj):
        return obj.get_verification_method_display()
    
    def get_confidence_level(self, obj):
        if obj.verification_details:
            return obj.verification_details.get('confidence', 'N/A')
        return 'N/A'

    class Meta:
        model = LiveNews
        fields = [
            'id', 'title', 'publication_date', 'news_category',
            'prediction', 'verification_status', 'confidence_level',
            'verification_details', 'web_url', 'img_url', 'content'
        ]
# class LiveNewsDetailedSerializer(serializers.ModelSerializer):
#     """Serialized all fields from the `LiveNews` model"""
#     class Meta:
#         model = LiveNews
#         fields = (
#                     'id', 'title', 'publication_date',
#                     'news_category', 'prediction', 'section_id',
#                     'section_name', 'type', 'web_url', 'img_url'
#                  )
