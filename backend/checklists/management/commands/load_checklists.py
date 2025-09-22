import os
import re
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from checklists.models import ChecklistTemplate, ChecklistItem

class Command(BaseCommand):
    help = 'Loads checklist templates and items from Markdown files in the project root.'

    # Define expected filenames or a pattern
    CHECKLIST_FILES_PATTERN = r'aprendizagens_([A-Z]{2})_(\d+)Ano\.md' # e.g., aprendizagens_PT_5Ano.md

    # Regex to capture domain code and description from objective lines
    # Example: "OC1. Compreender o essencial de textos orais..." captures 'OC' and 'Compreender...'
    # Allows for multi-digit numbers like LE10.
    OBJECTIVE_LINE_PATTERN = r'^([A-Z]+\d+)\.\s+(.*)$'

    # Simple mapping for subject code to full name for Template Name
    SUBJECT_NAME_MAPPING = {
        'PT': 'Português',
        # Add others like 'MA': 'Matemática' if needed
    }

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting checklist loading process...'))
        
        project_root = settings.BASE_DIR
        files_processed = 0

        for filename in os.listdir(project_root):
            match = re.match(self.CHECKLIST_FILES_PATTERN, filename, re.IGNORECASE)
            if match:
                subject_code = match.group(1).upper() # e.g., PT
                grade_level = int(match.group(2))    # e.g., 5
                filepath = os.path.join(project_root, filename)
                
                self.stdout.write(f'Processing file: {filename} (Subject: {subject_code}, Grade: {grade_level})')
                try:
                    self.process_markdown_file(filepath, subject_code, grade_level)
                    files_processed += 1
                except Exception as e:
                    raise CommandError(f'Error processing file {filename}: {e}')

        if files_processed == 0:
            self.stdout.write(self.style.WARNING('No checklist Markdown files found matching the pattern.'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Successfully processed {files_processed} checklist files.'))

    def process_markdown_file(self, filepath, subject_code, grade_level):
        """Parses a single Markdown file and creates/updates ChecklistTemplate and ChecklistItems."""
        
        subject_name = self.SUBJECT_NAME_MAPPING.get(subject_code, subject_code)
        template_name = f"{subject_name} {grade_level}º Ano"
        
        # Get or create the template based on name
        template, created = ChecklistTemplate.objects.update_or_create(
            name=template_name,
            defaults={'description': f'Aprendizagens Essenciais de {subject_name} para o {grade_level}º Ano.'} # Optional description
        )
        if created:
            self.stdout.write(f'  Created template: {template_name}')
        else:
            self.stdout.write(f'  Found existing template: {template_name}')
            # Optional: Clear existing items if you want a full reload
            # template.items.all().delete()
            # self.stdout.write(f'    Deleted existing items for this template.')

        item_order = 0
        items_processed = 0
        skipped_lines = 0
        
        with open(filepath, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue

                match = re.match(self.OBJECTIVE_LINE_PATTERN, line)
                if match:
                    item_code = match.group(1).strip()
                    item_text = match.group(2).strip()
                    
                    if not item_text:
                        self.stdout.write(self.style.WARNING(f'  Line {line_num}: Found objective code ({item_code}) but empty description, skipping.'))
                        skipped_lines += 1
                        continue

                    item_order += 1
                    items_processed += 1
                    
                    # Use update_or_create based on template and CODE
                    item, item_created = ChecklistItem.objects.update_or_create(
                        template=template,
                        code=item_code,
                        defaults={
                            'text': item_text,
                            'order': item_order, # Update order based on file sequence
                        }
                    )
                else:
                    skipped_lines += 1
            
            self.stdout.write(f'  Processed {items_processed} objectives from {os.path.basename(filepath)}. Skipped {skipped_lines} lines.')

        # --- End Parsing Logic --- 