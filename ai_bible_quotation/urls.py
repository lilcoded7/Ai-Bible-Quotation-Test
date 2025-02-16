from django.urls import path
from ai_bible_quotation.views import LiveSermonQuotationView


urlpatterns = [
    path('', LiveSermonQuotationView.as_view(), name='listen_sermon')
]