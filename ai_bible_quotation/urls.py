from django.urls import path
from ai_bible_quotation.views import ListenSermonsAPIView


urlpatterns = [
    path('', ListenSermonsAPIView.as_view(), name='listen_sermon')
]