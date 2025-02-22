from django.urls import path
from ai_bible_quotation.views import TranscribeAndQuoteView


urlpatterns = [
    path('', TranscribeAndQuoteView.as_view(), name='transcribe_and_quote')
]