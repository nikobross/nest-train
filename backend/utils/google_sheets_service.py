"""Google Sheets service for reading images and writing annotations."""

import json
import os
import re
from urllib.parse import urlparse

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build


class GoogleSheetsService:
    """Encapsulates Google Sheets operations for annotation workflow."""

    IMAGE_COLUMN_NAME = 'list'
    HAS_PLASTIC_COLUMN = 'has_plastic'
    LOCATION_COLUMN = 'plastic_location_labels'
    ANNOTATED_AT_COLUMN = 'annotated_at'
    LAST_INDEX_COLUMN = 'last_annotated_index'

    def __init__(self, config):
        self.config = config

    @staticmethod
    def parse_spreadsheet_id(sheet_input):
        """Extract a spreadsheet ID from URL or raw ID input."""
        value = (sheet_input or '').strip()
        if not value:
            raise ValueError('Sheet URL or Spreadsheet ID is required.')

        match = re.search(r'/spreadsheets/d/([a-zA-Z0-9-_]+)', value)
        if match:
            return match.group(1)

        if re.fullmatch(r'[a-zA-Z0-9-_]{20,}', value):
            return value

        raise ValueError('Invalid Google Sheet URL or Spreadsheet ID.')

    @staticmethod
    def _column_letter(col_index):
        """Convert 1-based column index to A1 column letter(s)."""
        letters = ''
        n = col_index
        while n > 0:
            n, remainder = divmod(n - 1, 26)
            letters = chr(65 + remainder) + letters
        return letters

    @staticmethod
    def _safe_filename(path_or_url):
        """Build a readable filename from a path or URL."""
        if not path_or_url:
            return ''

        parsed = urlparse(path_or_url)
        if parsed.scheme in ('http', 'https'):
            base = os.path.basename(parsed.path)
            return base or path_or_url

        return os.path.basename(path_or_url)

    def credentials_from_session(self, session_credentials):
        """Create refreshable Google credentials from session data."""
        if not isinstance(session_credentials, dict):
            raise ValueError('Google session credentials are missing or invalid.')

        token = session_credentials.get('token') or session_credentials.get('access_token')
        if not token:
            raise ValueError('Google session token is missing. Sign in again.')

        scopes = session_credentials.get('scopes')
        if isinstance(scopes, str):
            scopes = [s for s in scopes.split(' ') if s]
        elif isinstance(scopes, (list, tuple, set)):
            scopes = [str(s).strip() for s in scopes if str(s).strip()]
        else:
            scopes = []

        if not scopes:
            scope_value = session_credentials.get('scope', '')
            if isinstance(scope_value, str):
                scopes = [s for s in scope_value.split(' ') if s]
            elif isinstance(scope_value, (list, tuple, set)):
                scopes = [str(s).strip() for s in scope_value if str(s).strip()]
            else:
                scopes = []

        creds = Credentials(
            token=token,
            refresh_token=session_credentials.get('refresh_token'),
            token_uri=session_credentials.get('token_uri', 'https://oauth2.googleapis.com/token'),
            client_id=session_credentials.get('client_id') or self.config.GOOGLE_CLIENT_ID,
            client_secret=session_credentials.get('client_secret') or self.config.GOOGLE_CLIENT_SECRET,
            scopes=scopes or ['https://www.googleapis.com/auth/spreadsheets'],
        )

        if creds.expired and creds.refresh_token:
            creds.refresh(Request())

        return creds

    def _service(self, session_credentials):
        creds = self.credentials_from_session(session_credentials)
        return build('sheets', 'v4', credentials=creds), creds

    def _get_primary_sheet_title(self, service, spreadsheet_id):
        spreadsheet = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
        sheets = spreadsheet.get('sheets', [])
        if not sheets:
            raise ValueError('Spreadsheet has no sheets/tabs.')
        return sheets[0]['properties']['title']

    def _get_headers(self, service, spreadsheet_id, sheet_title):
        range_name = f"'{sheet_title}'!1:1"
        values = service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id,
            range=range_name
        ).execute().get('values', [])

        if not values:
            return []

        return [str(v).strip() for v in values[0]]

    def _ensure_columns(self, service, spreadsheet_id, sheet_title, headers, required_columns):
        existing_lower = {h.lower(): i for i, h in enumerate(headers)}
        changed = False

        for col_name in required_columns:
            if col_name.lower() not in existing_lower:
                headers.append(col_name)
                existing_lower[col_name.lower()] = len(headers) - 1
                changed = True

        if changed:
            range_name = f"'{sheet_title}'!1:1"
            service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range=range_name,
                valueInputOption='RAW',
                body={'values': [headers]}
            ).execute()

        return headers

    @staticmethod
    def _find_column_index(headers, column_name):
        for i, header in enumerate(headers):
            if str(header).strip().lower() == column_name.lower():
                return i
        return -1

    def get_image_rows(self, session_credentials, sheet_input):
        """Read image rows from the list column in the primary sheet."""
        spreadsheet_id = self.parse_spreadsheet_id(sheet_input)
        service, creds = self._service(session_credentials)
        sheet_title = self._get_primary_sheet_title(service, spreadsheet_id)
        headers = self._get_headers(service, spreadsheet_id, sheet_title)

        image_col_index = self._find_column_index(headers, self.IMAGE_COLUMN_NAME)
        if image_col_index < 0:
            raise ValueError(f"Missing required image column '{self.IMAGE_COLUMN_NAME}'.")

        image_col_letter = self._column_letter(image_col_index + 1)

        headers = self._ensure_columns(
            service,
            spreadsheet_id,
            sheet_title,
            headers,
            [
                self.HAS_PLASTIC_COLUMN,
                self.LOCATION_COLUMN,
                self.ANNOTATED_AT_COLUMN,
                self.LAST_INDEX_COLUMN,
            ],
        )

        rows = service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id,
            range=f"'{sheet_title}'!{image_col_letter}2:{image_col_letter}"
        ).execute().get('values', [])

        images = []
        row_map = []
        for offset, row in enumerate(rows):
            cell = row[0] if row else ''
            image_path = str(cell).strip()
            if not image_path:
                continue

            row_number = offset + 2
            row_map.append(row_number)
            images.append({
                'index': len(images),
                'path': image_path,
                'filename': self._safe_filename(image_path),
                'row': row_number,
                'col': self.IMAGE_COLUMN_NAME,
            })

        refreshed_session = {
            'token': creds.token,
            'refresh_token': creds.refresh_token,
            'token_uri': creds.token_uri,
            'client_id': creds.client_id,
            'client_secret': creds.client_secret,
            'scopes': list(creds.scopes or []),
        }

        return {
            'spreadsheet_id': spreadsheet_id,
            'sheet_title': sheet_title,
            'headers': headers,
            'images': images,
            'row_map': row_map,
            'refreshed_credentials': refreshed_session,
        }

    def get_last_annotated_index(self, session_credentials, sheet_input):
        """Read last annotated index from first data row in last_annotated_index column."""
        spreadsheet_id = self.parse_spreadsheet_id(sheet_input)
        service, creds = self._service(session_credentials)
        sheet_title = self._get_primary_sheet_title(service, spreadsheet_id)
        headers = self._get_headers(service, spreadsheet_id, sheet_title)
        headers = self._ensure_columns(
            service,
            spreadsheet_id,
            sheet_title,
            headers,
            [self.LAST_INDEX_COLUMN],
        )

        col_index = self._find_column_index(headers, self.LAST_INDEX_COLUMN)
        col_letter = self._column_letter(col_index + 1)

        value = service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id,
            range=f"'{sheet_title}'!{col_letter}2"
        ).execute().get('values', [])

        refreshed_session = {
            'token': creds.token,
            'refresh_token': creds.refresh_token,
            'token_uri': creds.token_uri,
            'client_id': creds.client_id,
            'client_secret': creds.client_secret,
            'scopes': list(creds.scopes or []),
        }

        if not value or not value[0]:
            return {'index': 0, 'refreshed_credentials': refreshed_session}

        try:
            return {'index': max(0, int(value[0][0])), 'refreshed_credentials': refreshed_session}
        except (TypeError, ValueError):
            return {'index': 0, 'refreshed_credentials': refreshed_session}

    def set_last_annotated_index(self, session_credentials, sheet_input, image_index):
        """Store last annotated index in first data row of last_annotated_index column."""
        spreadsheet_id = self.parse_spreadsheet_id(sheet_input)
        service, creds = self._service(session_credentials)
        sheet_title = self._get_primary_sheet_title(service, spreadsheet_id)
        headers = self._get_headers(service, spreadsheet_id, sheet_title)
        headers = self._ensure_columns(
            service,
            spreadsheet_id,
            sheet_title,
            headers,
            [self.LAST_INDEX_COLUMN],
        )

        col_index = self._find_column_index(headers, self.LAST_INDEX_COLUMN)
        col_letter = self._column_letter(col_index + 1)
        service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=f"'{sheet_title}'!{col_letter}2",
            valueInputOption='RAW',
            body={'values': [[int(image_index)]]}
        ).execute()

        return {
            'token': creds.token,
            'refresh_token': creds.refresh_token,
            'token_uri': creds.token_uri,
            'client_id': creds.client_id,
            'client_secret': creds.client_secret,
            'scopes': list(creds.scopes or []),
        }

    def write_annotation(self, session_credentials, sheet_input, sheet_row, annotation, image_index):
        """Write has_plastic and plastic_location_labels to a specific data row."""
        return self.write_annotations_batch(
            session_credentials,
            sheet_input,
            [
                {
                    'sheet_row': sheet_row,
                    'annotation': annotation,
                    'image_index': image_index,
                }
            ],
        )

    def write_annotations_batch(self, session_credentials, sheet_input, entries):
        """Write many annotation rows in a single Sheets batch update."""
        if not entries:
            return {
                'token': session_credentials.get('token'),
                'refresh_token': session_credentials.get('refresh_token'),
                'token_uri': session_credentials.get('token_uri'),
                'client_id': session_credentials.get('client_id'),
                'client_secret': session_credentials.get('client_secret'),
                'scopes': session_credentials.get('scopes', []),
            }

        spreadsheet_id = self.parse_spreadsheet_id(sheet_input)
        service, creds = self._service(session_credentials)
        sheet_title = self._get_primary_sheet_title(service, spreadsheet_id)
        headers = self._get_headers(service, spreadsheet_id, sheet_title)
        headers = self._ensure_columns(
            service,
            spreadsheet_id,
            sheet_title,
            headers,
            [
                self.HAS_PLASTIC_COLUMN,
                self.LOCATION_COLUMN,
                self.ANNOTATED_AT_COLUMN,
                self.LAST_INDEX_COLUMN,
            ],
        )

        has_col = self._find_column_index(headers, self.HAS_PLASTIC_COLUMN)
        loc_col = self._find_column_index(headers, self.LOCATION_COLUMN)
        at_col = self._find_column_index(headers, self.ANNOTATED_AT_COLUMN)

        has_letter = self._column_letter(has_col + 1)
        loc_letter = self._column_letter(loc_col + 1)
        at_letter = self._column_letter(at_col + 1)

        last_col = self._find_column_index(headers, self.LAST_INDEX_COLUMN)
        last_letter = self._column_letter(last_col + 1)

        data_ranges = []
        max_index = 0
        for entry in entries:
            row = int(entry['sheet_row'])
            annotation = entry.get('annotation', {})
            image_index = int(entry.get('image_index', 0))
            max_index = max(max_index, image_index)

            has_value = 1 if bool(annotation.get('has_plastic')) else 0
            location_value = json.dumps(annotation.get('boxes', []))
            annotated_at = annotation.get('annotated_at', '')

            data_ranges.append({'range': f"'{sheet_title}'!{has_letter}{row}", 'values': [[has_value]]})
            data_ranges.append({'range': f"'{sheet_title}'!{loc_letter}{row}", 'values': [[location_value]]})
            data_ranges.append({'range': f"'{sheet_title}'!{at_letter}{row}", 'values': [[annotated_at]]})

        data_ranges.append({'range': f"'{sheet_title}'!{last_letter}2", 'values': [[max_index]]})

        service.spreadsheets().values().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={'valueInputOption': 'RAW', 'data': data_ranges},
        ).execute()

        return {
            'token': creds.token,
            'refresh_token': creds.refresh_token,
            'token_uri': creds.token_uri,
            'client_id': creds.client_id,
            'client_secret': creds.client_secret,
            'scopes': list(creds.scopes or []),
        }

    def read_annotation(self, session_credentials, sheet_input, sheet_row):
        """Read annotation columns from a row and return annotation object."""
        spreadsheet_id = self.parse_spreadsheet_id(sheet_input)
        service, creds = self._service(session_credentials)
        sheet_title = self._get_primary_sheet_title(service, spreadsheet_id)
        headers = self._get_headers(service, spreadsheet_id, sheet_title)

        has_col = self._find_column_index(headers, self.HAS_PLASTIC_COLUMN)
        loc_col = self._find_column_index(headers, self.LOCATION_COLUMN)
        at_col = self._find_column_index(headers, self.ANNOTATED_AT_COLUMN)

        if has_col < 0 and loc_col < 0:
            return {'annotation': None, 'refreshed_credentials': session_credentials}

        data_ranges = []
        if has_col >= 0:
            data_ranges.append((self._column_letter(has_col + 1), 'has'))
        if loc_col >= 0:
            data_ranges.append((self._column_letter(loc_col + 1), 'loc'))
        if at_col >= 0:
            data_ranges.append((self._column_letter(at_col + 1), 'at'))

        result = {'has': '', 'loc': '', 'at': ''}
        for letter, key in data_ranges:
            value = service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id,
                range=f"'{sheet_title}'!{letter}{sheet_row}"
            ).execute().get('values', [])
            result[key] = value[0][0] if value and value[0] else ''

        boxes = []
        if result['loc']:
            try:
                boxes = json.loads(result['loc'])
            except json.JSONDecodeError:
                boxes = []

        has_plastic = False
        if str(result['has']).strip() in ('1', 'true', 'True'):
            has_plastic = True

        annotation = {
            'has_plastic': has_plastic,
            'boxes': boxes,
            'annotated_at': result['at'] or None,
        }

        refreshed_session = {
            'token': creds.token,
            'refresh_token': creds.refresh_token,
            'token_uri': creds.token_uri,
            'client_id': creds.client_id,
            'client_secret': creds.client_secret,
            'scopes': list(creds.scopes or []),
        }

        return {'annotation': annotation, 'refreshed_credentials': refreshed_session}
