from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from ai_bible_quotation.models.bible_translations import BibleTranslation
from ai_bible_quotation.serializers import BibleTranslationSerializer
import google.generativeai as genai 
from rest_framework import status
from django.conf import settings
import logging
logger = logging.getLogger(__name__)
import whisper
import tempfile
import openai 
import os 
# Create your views here.


from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from faster_whisper import WhisperModel
import tempfile
import os
import google.generativeai as genai
from concurrent.futures import ThreadPoolExecutor
from django.db.models import Q
import logging

from .serializers import LivesermonsSerializer, BibleTranslationSerializer
from .models import BibleTranslation

logger = logging.getLogger(__name__)

class LiveSermonQuotationView(APIView):
    """
    API endpoint that processes live sermon audio and returns relevant Bible quotations.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            # Initialize Faster Whisper model (tiny for speed)
            self.whisper_model = WhisperModel("tiny", device="cpu", compute_type="int8")
            
            # Initialize Google Gemini
            genai.configure(api_key=settings.GOOGLE_API_KEY)
            self.gemini_model = genai.GenerativeModel('gemini-pro')
        except Exception as e:
            logger.error(f"Failed to initialize models: {str(e)}")
            self.whisper_model = None
            self.gemini_model = None

    def extract_bible_reference(self, text):
        """
        Use Gemini to extract Bible references from text.
        """
        if not self.gemini_model:
            raise ValueError("Gemini model not properly initialized")

        prompt = f"""
        Extract any Bible verse references from the following text. 
        Return only the book, chapter, and verse numbers in the format: book|chapter|verse
        If multiple verses are referenced, return each on a new line.
        If no clear reference is found, return 'None'.
        
        Text: {text}
        """
        
        try:
            response = self.gemini_model.generate_content(prompt)
            references = []
            
            for line in response.text.split('\n'):
                if line and line != 'None':
                    try:
                        book, chapter, verse = line.strip().split('|')
                        references.append({
                            'book': book.strip(),
                            'chapter': int(chapter),
                            'verse': int(verse)
                        })
                    except ValueError:
                        continue
                        
            return references
        except Exception as e:
            logger.error(f"Error extracting Bible reference: {str(e)}")
            return []

    def get_bible_verses(self, references, translation='KJV'):
        """
        Retrieve Bible verses from the database.
        """
        verses = []
        for ref in references:
            try:
                verse = BibleTranslation.objects.get(
                    translation=translation,
                    book__iexact=ref['book'],
                    chapter=ref['chapter'],
                    verse=ref['verse']
                )
                verses.append(BibleTranslationSerializer(verse).data)
            except BibleTranslation.DoesNotExist:
                logger.warning(f"Verse not found: {ref}")
                continue
            except Exception as e:
                logger.error(f"Error retrieving verse: {str(e)}")
                continue
        return verses

    def process_audio_chunk(self, audio_file):
        """
        Process an audio chunk using Faster Whisper for transcription.
        """
        if not self.whisper_model:
            raise ValueError("Whisper model not properly initialized")

        # Save the audio chunk to a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_file:
            for chunk in audio_file.chunks():
                tmp_file.write(chunk)
            tmp_file_path = tmp_file.name

        try:
            # Transcribe the audio using Faster Whisper
            segments, info = self.whisper_model.transcribe(tmp_file_path, beam_size=1)
            transcription = " ".join([segment.text for segment in segments])

            # Extract Bible references
            references = self.extract_bible_reference(transcription)
            
            # Get the corresponding verses
            verses = self.get_bible_verses(references)

            return {
                'transcription': transcription,
                'verses': verses
            }

        except Exception as e:
            logger.error(f"Error processing audio: {str(e)}")
            raise
        finally:
            # Clean up temporary file
            try:
                os.unlink(tmp_file_path)
            except Exception as e:
                logger.error(f"Error removing temporary file: {str(e)}")

    def post(self, request):
        """
        Handle POST requests with audio data.
        """
        serializer = LivesermonsSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            
            result = self.process_audio_chunk(request.FILES['audio'])
            
            return Response({
                'status': 'success',
                'data': result
            }, status=status.HTTP_200_OK)

        except ValueError as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return Response({
                'status': 'error',
                'message': 'An unexpected error occurred while processing the audio'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)