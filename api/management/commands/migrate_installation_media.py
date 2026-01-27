"""
Management command to migrate legacy installation_media notes into Document rows.

Usage:
  python manage.py migrate_installation_media [--remove-note]

The command looks for notes starting with 'installation_media:' on each Installation,
parses the JSON payload, and for any media URL that points into MEDIA_URL (e.g. /media/...),
it will create a Document instance pointing to the existing file (no file copy).

It will skip blob: URLs, data URLs, and any URLs that do not reference MEDIA_URL.
By default the original note is retained; pass --remove-note to delete the note after successful migration.
"""
from django.core.management.base import BaseCommand
from django.conf import settings
import os
from django.core.files.storage import default_storage
from django.db import transaction
from urllib.parse import urlparse
import json

from api.models import Installation, Document


def extract_urls_from_payload(payload):
    """Yield tuples of (url, inferred_category) from the parsed payload."""
    mapping = {
        'before': ['db', 'place', 'carPlace'],
        'after': ['db', 'place', 'carPlace'],
        'testingVideo': []
    }

    results = []

    # before/after groups
    for group in ('before', 'after'):
        if group in payload:
            g = payload[group] or {}
            for field in mapping[group]:
                val = g.get(field)
                if not val:
                    continue
                if isinstance(val, dict):
                    url = val.get('url')
                else:
                    url = val
                if url:
                    # infer category as photo
                    results.append((url, 'photo'))

    # testingVideo may be string or object
    if 'testingVideo' in payload and payload['testingVideo']:
        tv = payload['testingVideo']
        if isinstance(tv, dict):
            url = tv.get('url')
        else:
            url = tv
        if url:
            results.append((url, 'other'))

    return results


class Command(BaseCommand):
    help = 'Migrate installation_media notes to Document rows.'

    def add_arguments(self, parser):
        parser.add_argument('--remove-note', action='store_true', help='Remove the installation_media note after migrating')

    def handle(self, *args, **options):
        remove_note = options.get('remove_note', False)
        media_url = getattr(settings, 'MEDIA_URL', '/media/')
        created_count = 0
        skipped_count = 0
        updated_installations = 0

        installations = Installation.objects.all()
        self.stdout.write(f'Found {installations.count()} installations to scan...')

        for inst in installations:
            notes = inst.notes or []
            idx = None
            for i, n in enumerate(notes):
                if isinstance(n, str) and n.startswith('installation_media:'):
                    idx = i
                    break

            if idx is None:
                continue

            raw = notes[idx]
            try:
                payload_json = raw.replace('installation_media:', '', 1)
                payload = json.loads(payload_json)
            except Exception as e:
                self.stderr.write(f'Installation {inst.id}: failed to parse installation_media note: {e}')
                skipped_count += 1
                continue

            urls = extract_urls_from_payload(payload)
            if not urls:
                continue

            any_created = False

            with transaction.atomic():
                for url, category in urls:
                    if not isinstance(url, str):
                        skipped_count += 1
                        continue

                    url = url.strip()
                    # skip blob/data URLs and inline object URLs
                    if url.startswith('blob:') or url.startswith('data:'):
                        skipped_count += 1
                        continue

                    # If it's a full URL, parse path
                    parsed = urlparse(url)
                    path = parsed.path if parsed.scheme else url

                    # Determine relative path by locating MEDIA_URL inside the path
                    if media_url and media_url in path:
                        idx = path.find(media_url)
                        relative_name = path[idx + len(media_url):]
                    else:
                        # Not a media URL we can reference
                        skipped_count += 1
                        continue

                    # Normalize leading slash
                    if relative_name.startswith('/'):
                        relative_name = relative_name[1:]

                    # Check file exists under MEDIA_ROOT when available, otherwise use storage.exists
                    media_root = getattr(settings, 'MEDIA_ROOT', None)
                    if media_root:
                        file_path = os.path.join(media_root, relative_name)
                        if not os.path.exists(file_path):
                            self.stderr.write(f'Installation {inst.id}: media file not found on disk: {file_path}')
                            skipped_count += 1
                            continue
                    else:
                        if not default_storage.exists(relative_name):
                            self.stderr.write(f'Installation {inst.id}: media file not found in storage: {relative_name}')
                            skipped_count += 1
                            continue

                    # Avoid duplicates: check Document with same installation and file name
                    exists = inst.documents.filter(file=relative_name).exists()
                    if exists:
                        self.stdout.write(f'Installation {inst.id}: document already exists for {relative_name}, skipping')
                        skipped_count += 1
                        continue

                    doc = Document(installation=inst, document_type=category, description='Migrated from installation_media note')
                    # Point FileField to existing file path (no copy)
                    doc.file.name = relative_name
                    doc.save()
                    created_count += 1
                    any_created = True

            if any_created:
                updated_installations += 1
                if remove_note:
                    # remove the note and save
                    try:
                        notes.pop(idx)
                        inst.notes = notes
                        inst.save(update_fields=['notes'])
                    except Exception as e:
                        self.stderr.write(f'Installation {inst.id}: failed to remove note: {e}')

        self.stdout.write(f'Migration complete. Documents created: {created_count}. Skipped: {skipped_count}. Installations updated: {updated_installations}.')
