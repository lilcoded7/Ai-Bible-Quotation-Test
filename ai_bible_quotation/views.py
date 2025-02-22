from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import LivesermonsSerializer
from ai_bible_quotation.models.bible_translations import BibleTranslation
import openai
import google.generativeai as genai
from django.conf import settings
import os


openai.api_key = 'your-openai-api-key'
genai.configure(api_key=settings.GOOGLE_API_KEY)

class TranscribeAndQuoteView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = LivesermonsSerializer(data=request.data)
        if serializer.is_valid():
            audio_file = serializer.validated_data['audio_file']
            
           
            transcription = self.transcribe_audio(audio_file)
            
            quote_address = self.extract_quote_address(transcription)
            
            if quote_address:
                quote = self.get_bible_quote(quote_address)
                return Response({'quote': quote}, status=status.HTTP_200_OK)
            else:
                return Response({'error': 'No Bible quote detected.'}, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def transcribe_audio(self, audio_file):
        
        with open('temp_audio.mp3', 'wb+') as destination:
            for chunk in audio_file.chunks():
                destination.write(chunk)
        
        with open('temp_audio.mp3', 'rb') as audio:
            transcription = openai.Audio.transcribe("whisper-1", audio)
        os.remove('temp_audio.mp3')
        return transcription['text']

    def extract_quote_address(self, text):
        
        model = genai.GenerativeModel('gemini-flash')
        response = model.generate_content(f"Extract Bible quote address from: {text}")
        return response.text

    def get_bible_quote(self, address):
    
        parts = address.split()
        book = parts[0]
        chapter_verse = parts[1].split(':')
        chapter = int(chapter_verse[0])
        verse = int(chapter_verse[1])
        
        try:
            quote = BibleTranslation.objects.get(book=book, chapter=chapter, verse=verse)
            return quote.text
        except BibleTranslation.DoesNotExist:
            return None