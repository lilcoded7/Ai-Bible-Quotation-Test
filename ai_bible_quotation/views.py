from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from faster_whisper import WhisperModel
import google.generativeai as genai
from django.conf import settings
import tempfile
import os
import logging
from .serializers import LivesermonsSerializer, BibleTranslationSerializer
from ai_bible_quotation.models.bible_translations import BibleTranslation

logger = logging.getLogger(__name__)

class LiveSermonQuotationView(APIView):
    """
    API endpoint for processing live sermon audio and extracting Bible quotations.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.initialize_models()

    def initialize_models(self):
        """Initialize AI models with error handling"""
        try:
            
            self.whisper_model = WhisperModel("tiny", device="cpu", compute_type="int8")
            
            genai.configure(api_key=settings.GOOGLE_API_KEY)
            self.gemini_model = genai.GenerativeModel('gemini-pro')
            
        except Exception as e:
            logger.error(f"Model initialization failed: {str(e)}")
            self.whisper_model = None
            self.gemini_model = None

    def transcribe_audio(self, audio_file):
        """
        Transcribe audio using Whisper model
        """
        if not self.whisper_model:
            raise ValueError("Speech recognition model not initialized")

        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_file:
            for chunk in audio_file.chunks():
                tmp_file.write(chunk)
            tmp_file_path = tmp_file.name

        try:
            segments, _ = self.whisper_model.transcribe(
                tmp_file_path, 
                beam_size=1,
                vad_filter=True,
                vad_parameters=dict(min_silence_duration_ms=500)
            )
            return " ".join([segment.text for segment in segments])
        finally:
            os.unlink(tmp_file_path)

    def extract_bible_references(self, text):
        """
        Extract Bible references using Gemini model
        """
        if not self.gemini_model:
            raise ValueError("Text analysis model not initialized")

        prompt = """
        Extract Bible verse references from this text.
        Format: book_name|chapter|verse
        Multiple verses: one per line
        If no reference found: return 'None'
        Only return the formatted references, no other text.
        Text to analyze: {text}
        """

        try:
            response = self.gemini_model.generate_content(prompt.format(text=text))
            references = []
            
            for line in response.text.strip().split('\n'):
                if line and line.lower() != 'none':
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
            logger.error(f"Reference extraction failed: {str(e)}")
            return []

    def fetch_bible_verses(self, references):
        """
        Retrieve verses from database
        """
        verses = []
        for ref in references:
            try:
                verse = BibleTranslation.objects.get(
                    translation='KJV',  
                    book__iexact=ref['book'],
                    chapter=ref['chapter'],
                    verse=ref['verse']
                )
                verses.append(BibleTranslationSerializer(verse).data)
            except BibleTranslation.DoesNotExist:
                logger.warning(f"Verse not found: {ref}")
            except Exception as e:
                logger.error(f"Error fetching verse: {str(e)}")
        
        return verses

    def post(self, request):
        """
        Handle incoming audio and return extracted Bible quotations
        """
        serializer = LivesermonsSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            
            audio_file = request.FILES['audio']
            
            transcription = self.transcribe_audio(audio_file)
            
            references = self.extract_bible_references(transcription)
            
            verses = self.fetch_bible_verses(references)
            
            return Response({
                'status': 'success',
                'data': {
                    'transcription': transcription,
                    'verses': verses
                }
            }, status=status.HTTP_200_OK)

        except ValueError as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
            
        except Exception as e:
            logger.error(f"Processing failed: {str(e)}")
            return Response({
                'status': 'error',
                'message': 'Audio processing failed'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)