from rest_framework import serializers
from ai_bible_quotation.models.bible_translations import BibleTranslation


class BibleTranslationSerializer(serializers.ModelSerializer):
    class Meta:
        model = BibleTranslation
        fields = '__all__'


class LivesermonsSerializer(serializers.Serializer):
    audio = serializers.FileField(
        allow_empty_file=False,
        required=True,
        error_messages={
            'required': 'Please provide an audio file.',
            'empty': 'The audio file cannot be empty.'
        }
    )

    def validate_audio(self, value):
        if value.size > 10 * 1024 * 1024:  
            raise serializers.ValidationError('Audio file size must be less than 10MB.')
        return value