from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from ai_bible_quotation.models.bible_translations import BibleTranslation
# Create your views here.




class ListenSermonsAPIView(APIView):
    def get(self, request):
        quotation = BibleTranslation.objects.first()

        data = {
            'translation':quotation.translation,
            'book':quotation.book,
            'chapter':quotation.chapter,
            'verse':quotation.verse,
            'text':quotation.text
        }
        
        return Response({'data':data})