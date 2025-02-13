from setup.basemodel import TimeBaseModel
from django.db import models


class BibleTranslation(TimeBaseModel):
    translation = models.CharField(max_length=10) 
    book = models.CharField(max_length=50)
    chapter = models.IntegerField()
    verse = models.IntegerField()
    text = models.TextField()

    class Meta:
        unique_together = ('translation', 'id', 'chapter', 'verse') 

    def __str(self):
        return f"Trnaslator: {self.translation} Book: {self.book} Chapter: {self.chapter} Verse: {self.verse}"