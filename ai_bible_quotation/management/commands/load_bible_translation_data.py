import os
import json
from django.core.management.base import BaseCommand
from ai_bible_quotation.models.bible_translations import BibleTranslation

# List of all translations
TRANSLATIONS = [
    "AKJV", "ASV", "BRG", "EHV", "ESV", "ESVUK", "GNV", "GW", "ISV", "JUB", 
    "KJ21", "KJV", "LEB", "MEV", "NASB", "NASB1995", "NET", "NIV", "NIVUK", 
    "NKJV", "NLT", "NLV", "NOG", "NRSV", "NRSVUE", "WEB", "YLT"
]

# Correct base directory based on folder structure
BASE_DIR = "BibleTranslations-master" 

class Command(BaseCommand):
    help = "Load Bible translations from JSON files into the database"

    def handle(self, *args, **kwargs):
        for translation in TRANSLATIONS:
            # Correct JSON file path: BibleTranslations-master/AKJV/AKJV_bible.json
            json_file = os.path.join(BASE_DIR, translation, f"{translation}_bible.json")

            if not os.path.isfile(json_file):  # Ensure file exists
                self.stdout.write(self.style.WARNING(f"Skipping {translation}: File not found at {json_file}"))
                continue

            self.stdout.write(self.style.SUCCESS(f"Processing {json_file}"))

            with open(json_file, "r", encoding="utf-8") as file:
                data = json.load(file)

            records = []
            for book, chapters in data.items():
                for chapter, verses in chapters.items():
                    for verse, text in verses.items():
                        records.append(BibleTranslation(
                            translation=translation,
                            book=book,
                            chapter=int(chapter),
                            verse=int(verse),
                            text=text
                        ))

            # Bulk insert for efficiency
            BibleTranslation.objects.bulk_create(records, ignore_conflicts=True)
            self.stdout.write(self.style.SUCCESS(f"Inserted data for {translation}"))

