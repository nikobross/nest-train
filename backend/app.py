"""
Flask backend for Bird Nest Plastic Annotation Tool.
Handles OAuth, Google Sheets sync, image serving, annotation storage, and progress tracking.
"""

from datetime import datetime
from functools import wraps
import sys

from flask import Flask, jsonify, redirect, request, send_from_directory, session
from flask_cors import CORS
from google_auth_oauthlib import flow as google_auth_flow

from config import Config
from utils.google_sheets_service import GoogleSheetsService


app = Flask(__name__)
app.secret_key = Config.SECRET_KEY
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = False
CORS(app, supports_credentials=True, origins=Config.CORS_ORIGINS)

# Initialize handlers
sheets_service = GoogleSheetsService(Config)

# Server-side cache for OAuth Flow objects (keyed by state)
_oauth_flow_cache = {}

# In-memory queue for batched sheet writes.
# Keyed by (sheet_input, image_index) so latest annotation per image wins.
_sheet_write_queue = {}
SHEET_FLUSH_THRESHOLD = 25
SHEET_FLUSH_BATCH_SIZE = 100


def validate_oauth_on_startup():
    """Validate OAuth configuration on startup."""
    is_configured = Config.validate_oauth_config()
    if not is_configured:
        print(
            'WARNING: OAuth environment variables not configured. Users will not be able to sign in.',
            file=sys.stderr,
        )
    return is_configured


def build_oauth_flow():
    """Build a Google OAuth flow object for authorization."""
    flow = google_auth_flow.Flow.from_client_config(
        {
            'installed': {
                'client_id': Config.GOOGLE_CLIENT_ID,
                'client_secret': Config.GOOGLE_CLIENT_SECRET,
                'redirect_uris': [Config.GOOGLE_REDIRECT_URI],
                'auth_uri': 'https://accounts.google.com/o/oauth2/auth',
                'token_uri': 'https://oauth2.googleapis.com/token',
            }
        },
        scopes=[
            'openid',
            'https://www.googleapis.com/auth/userinfo.profile',
            'https://www.googleapis.com/auth/userinfo.email',
            Config.GOOGLE_SHEETS_SCOPE,
        ],
        redirect_uri=Config.GOOGLE_REDIRECT_URI,
    )
    return flow


def require_google_auth(route_fn):
    """Require a valid Google OAuth session for protected routes."""

    @wraps(route_fn)
    def wrapped(*args, **kwargs):
        if not session.get('google_credentials'):
            return (
                jsonify(
                    {
                        'success': False,
                        'error': 'Not authenticated with Google. Please sign in first.',
                        'error_code': 'AUTH_REQUIRED',
                    }
                ),
                401,
            )
        return route_fn(*args, **kwargs)

    return wrapped


def current_sheet_input():
    """Get active sheet URL/ID from session."""
    return (session.get('sheet_input') or '').strip()


def update_session_credentials(refreshed_credentials):
    """Persist refreshed credentials after token refresh."""
    if refreshed_credentials:
        session['google_credentials'] = refreshed_credentials
        session.modified = True


def ensure_row_map_for_index(image_index):
    """Fetch row map on demand and validate requested index."""
    sheet_input = current_sheet_input()
    creds = session.get('google_credentials')
    if not sheet_input or not creds:
        return []

    payload = sheets_service.get_image_rows(creds, sheet_input)
    update_session_credentials(payload.get('refreshed_credentials'))
    return payload.get('row_map', [])


def enqueue_sheet_write(sheet_input, image_index, sheet_row, annotation):
    """Queue a sheet write, replacing any prior queued entry for the same image."""
    key = (str(sheet_input), int(image_index))
    _sheet_write_queue[key] = {
        'sheet_input': str(sheet_input),
        'image_index': int(image_index),
        'sheet_row': int(sheet_row),
        'annotation': annotation,
    }


def queue_size_for_sheet(sheet_input):
    """Count queued writes for one sheet."""
    normalized = str(sheet_input)
    return sum(1 for item in _sheet_write_queue.values() if item['sheet_input'] == normalized)


def flush_sheet_queue_for_sheet(session_credentials, sheet_input, max_items=SHEET_FLUSH_BATCH_SIZE):
    """Flush queued writes for a sheet in one bulk request (up to max_items)."""
    normalized = str(sheet_input)
    items = [item for item in _sheet_write_queue.values() if item['sheet_input'] == normalized]
    if not items:
        return {'flushed': 0, 'refreshed_credentials': None}

    # Flush oldest indexes first for predictable behavior.
    items.sort(key=lambda x: x['image_index'])
    batch = items[: max(1, int(max_items))]

    entries = [
        {
            'sheet_row': item['sheet_row'],
            'annotation': item['annotation'],
            'image_index': item['image_index'],
        }
        for item in batch
    ]

    refreshed = sheets_service.write_annotations_batch(session_credentials, normalized, entries)

    for item in batch:
        key = (normalized, item['image_index'])
        _sheet_write_queue.pop(key, None)

    return {'flushed': len(batch), 'refreshed_credentials': refreshed}


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify(
        {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'google_oauth_configured': bool(
                Config.GOOGLE_CLIENT_ID and Config.GOOGLE_CLIENT_SECRET
            ),
        }
    )


@app.route('/api/auth/google-login', methods=['GET'])
def google_login():
    """Start Google OAuth flow by returning an authorization URL."""
    try:
        if not Config.GOOGLE_CLIENT_ID or not Config.GOOGLE_CLIENT_SECRET:
            missing = []
            if not Config.GOOGLE_CLIENT_ID:
                missing.append('GOOGLE_CLIENT_ID')
            if not Config.GOOGLE_CLIENT_SECRET:
                missing.append('GOOGLE_CLIENT_SECRET')
            return (
                jsonify(
                    {
                        'success': False,
                        'error': f"Google OAuth is not configured. Missing: {', '.join(missing)}",
                        'error_code': 'OAUTH_NOT_CONFIGURED',
                    }
                ),
                400,
            )

        flow = build_oauth_flow()
        auth_url, state = flow.authorization_url(
            prompt='consent',
            access_type='offline',
            include_granted_scopes='true',
        )
        _oauth_flow_cache[state] = flow

        return jsonify({'success': True, 'auth_url': auth_url, 'state': state})
    except Exception as e:
        print(f'ERROR in google_login: {str(e)}', file=sys.stderr)
        return (
            jsonify(
                {
                    'success': False,
                    'error': f'Failed to start OAuth flow: {str(e)}',
                    'error_code': 'OAUTH_FLOW_ERROR',
                }
            ),
            500,
        )


@app.route('/api/auth/google-callback', methods=['GET'])
def google_callback():
    """Complete Google OAuth callback and store credentials in session."""
    try:
        code = request.args.get('code')
        state = request.args.get('state')
        error = request.args.get('error')

        if error:
            error_description = request.args.get('error_description', 'Unknown error')
            return (
                jsonify(
                    {
                        'success': False,
                        'error': f'OAuth canceled: {error_description}',
                        'error_code': 'OAUTH_CANCELED',
                    }
                ),
                400,
            )

        if not code:
            return (
                jsonify(
                    {
                        'success': False,
                        'error': 'Missing OAuth authorization code',
                        'error_code': 'MISSING_CODE',
                    }
                ),
                400,
            )

        if not state:
            return (
                jsonify(
                    {
                        'success': False,
                        'error': 'Missing state parameter from Google',
                        'error_code': 'MISSING_STATE',
                    }
                ),
                400,
            )

        flow = _oauth_flow_cache.get(state)
        if not flow:
            return (
                jsonify(
                    {
                        'success': False,
                        'error': 'State parameter not recognized. Please sign in again.',
                        'error_code': 'STATE_EXPIRED',
                    }
                ),
                400,
            )

        flow.fetch_token(code=code)
        creds = flow.credentials
        _oauth_flow_cache.pop(state, None)

        session['google_credentials'] = {
            'token': creds.token,
            'refresh_token': creds.refresh_token,
            'token_uri': creds.token_uri,
            'client_id': creds.client_id,
            'client_secret': creds.client_secret,
            'scopes': list(creds.scopes or []),
        }
        session.modified = True

        print('User authenticated successfully', file=sys.stderr)
        return redirect(f'{Config.FRONTEND_URL}?auth=success')

    except Exception as e:
        print(f'ERROR in google_callback: {str(e)}', file=sys.stderr)
        return (
            jsonify(
                {
                    'success': False,
                    'error': f'Google OAuth callback failed: {str(e)}',
                    'error_code': 'CALLBACK_ERROR',
                }
            ),
            500,
        )


@app.route('/api/auth/status', methods=['GET'])
def auth_status():
    """Return whether the current browser session is authenticated with Google."""
    return jsonify(
        {
            'success': True,
            'authenticated': bool(session.get('google_credentials')),
            'sheet_connected': bool(current_sheet_input()),
            'sheet_input': current_sheet_input(),
            'error_messages': [],
        }
    )


@app.route('/api/auth/logout', methods=['POST'])
def auth_logout():
    """Clear OAuth credentials from current session."""
    session.pop('google_credentials', None)
    session.pop('oauth_state', None)
    session.pop('sheet_input', None)
    session.modified = True
    return jsonify({'success': True, 'message': 'Logged out successfully'})


@app.route('/api/sheets/config', methods=['GET'])
@require_google_auth
def get_sheet_config():
    """Get active sheet URL/ID for current session."""
    return jsonify(
        {
            'success': True,
            'sheet_input': current_sheet_input(),
            'configured': bool(current_sheet_input()),
            'queued_writes': queue_size_for_sheet(current_sheet_input()) if current_sheet_input() else 0,
        }
    )


@app.route('/api/sheets/queue-status', methods=['GET'])
@require_google_auth
def get_sheet_queue_status():
    """Return pending batched write count for the current sheet."""
    sheet_input = current_sheet_input()
    if not sheet_input:
        return jsonify({'success': True, 'queue_size': 0, 'sheet_configured': False})

    return jsonify(
        {
            'success': True,
            'queue_size': queue_size_for_sheet(sheet_input),
            'sheet_configured': True,
        }
    )


@app.route('/api/sheets/flush', methods=['POST'])
@require_google_auth
def flush_sheet_queue():
    """Flush pending annotation writes for the current sheet."""
    sheet_input = current_sheet_input()
    if not sheet_input:
        return (
            jsonify(
                {
                    'success': False,
                    'error': 'No sheet configured. Add a sheet URL first.',
                    'error_code': 'SHEET_NOT_CONFIGURED',
                }
            ),
            400,
        )

    try:
        data = request.json or {}
        max_items = int(data.get('max_items', SHEET_FLUSH_BATCH_SIZE))
        result = flush_sheet_queue_for_sheet(
            session.get('google_credentials'),
            sheet_input,
            max_items=max_items,
        )
        update_session_credentials(result.get('refreshed_credentials'))
        return jsonify(
            {
                'success': True,
                'flushed': result.get('flushed', 0),
                'queue_size': queue_size_for_sheet(sheet_input),
            }
        )
    except Exception as e:
        return (
            jsonify({'success': False, 'error': str(e), 'error_code': 'SHEET_FLUSH_FAILED'}),
            500,
        )


@app.route('/api/sheets/config', methods=['POST'])
@require_google_auth
def set_sheet_config():
    """Set active sheet URL/ID for current session. This is required."""
    try:
        data = request.json or {}
        sheet_input = (data.get('sheet_input') or '').strip()
        if not sheet_input:
            return (
                jsonify(
                    {
                        'success': False,
                        'error': 'Sheet URL or Spreadsheet ID is required.',
                        'error_code': 'SHEET_REQUIRED',
                    }
                ),
                400,
            )

        payload = sheets_service.get_image_rows(session.get('google_credentials'), sheet_input)
        update_session_credentials(payload.get('refreshed_credentials'))

        session['sheet_input'] = sheet_input
        session.modified = True

        # Reset any stale queued writes from previous sheet configurations.
        stale_keys = [k for k in _sheet_write_queue if k[0] != str(sheet_input)]
        for key in stale_keys:
            _sheet_write_queue.pop(key, None)

        return jsonify(
            {
                'success': True,
                'sheet_input': sheet_input,
                'total_images': len(payload.get('images', [])),
            }
        )
    except Exception as e:
        return (
            jsonify(
                {
                    'success': False,
                    'error': str(e),
                    'error_code': 'SHEET_CONFIG_FAILED',
                }
            ),
            400,
        )


@app.route('/api/images/list', methods=['GET'])
@require_google_auth
def get_image_list():
    """Get images from configured Google Sheet list column."""
    try:
        sheet_input = current_sheet_input()
        if not sheet_input:
            return (
                jsonify(
                    {
                        'success': False,
                        'error': 'No sheet configured. Add a sheet URL first.',
                        'error_code': 'SHEET_NOT_CONFIGURED',
                    }
                ),
                400,
            )

        payload = sheets_service.get_image_rows(session.get('google_credentials'), sheet_input)
        update_session_credentials(payload.get('refreshed_credentials'))

        return jsonify(
            {
                'success': True,
                'images': payload.get('images', []),
                'total': len(payload.get('images', [])),
            }
        )
    except Exception as e:
        return (
            jsonify(
                {
                    'success': False,
                    'error': str(e),
                    'error_code': 'IMAGE_LIST_FAILED',
                }
            ),
            500,
        )


@app.route('/api/images/<path:filename>', methods=['GET'])
def serve_image(filename):
    """Serve image file for local image paths."""
    try:
        return send_from_directory(Config.IMAGES_DIR, filename)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 404


@app.route('/api/progress', methods=['GET'])
def get_progress():
    """Get current annotation progress from sheet metadata when available."""
    try:
        progress = {
            'current_index': 0,
            'last_updated': datetime.now().isoformat(),
            'total_annotated': 0,
        }

        if session.get('google_credentials') and current_sheet_input():
            try:
                result = sheets_service.get_last_annotated_index(
                    session.get('google_credentials'), current_sheet_input()
                )
                progress['current_index'] = int(result.get('index', 0))
                update_session_credentials(result.get('refreshed_credentials'))
            except Exception as inner_error:
                print(f'Progress sheet read warning: {str(inner_error)}', file=sys.stderr)

        return jsonify({'success': True, 'progress': progress})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/progress', methods=['POST'])
def update_progress():
    """Update current annotation progress in sheet metadata when enabled."""
    try:
        data = request.json or {}
        current_index = int(data.get('current_index', 0))

        # Remote last-index writes are optional to avoid high-latency writes on every navigation.
        persist_remote = bool(data.get('persist_remote', False))
        if persist_remote and session.get('google_credentials') and current_sheet_input():
            try:
                refreshed = sheets_service.set_last_annotated_index(
                    session.get('google_credentials'),
                    current_sheet_input(),
                    current_index,
                )
                update_session_credentials(refreshed)
            except Exception as inner_error:
                print(f'Progress sheet write warning: {str(inner_error)}', file=sys.stderr)

        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/annotations/<int:image_index>', methods=['GET'])
def get_annotation(image_index):
    """Get annotation for specific image from queue (unsynced) or sheet."""
    try:
        if session.get('google_credentials') and current_sheet_input():
            queued = _sheet_write_queue.get((current_sheet_input(), image_index))
            if queued:
                return jsonify({'success': True, 'annotation': queued.get('annotation')})

            sheet_row_arg = request.args.get('sheet_row')
            sheet_row = int(sheet_row_arg) if sheet_row_arg and str(sheet_row_arg).isdigit() else None

            if sheet_row and sheet_row >= 2:
                result = sheets_service.read_annotation(
                    session.get('google_credentials'),
                    current_sheet_input(),
                    sheet_row,
                )
                update_session_credentials(result.get('refreshed_credentials'))
                return jsonify({'success': True, 'annotation': result.get('annotation')})

            row_map = ensure_row_map_for_index(image_index)
            if 0 <= image_index < len(row_map):
                result = sheets_service.read_annotation(
                    session.get('google_credentials'),
                    current_sheet_input(),
                    row_map[image_index],
                )
                update_session_credentials(result.get('refreshed_credentials'))
                return jsonify({'success': True, 'annotation': result.get('annotation')})

        return jsonify({'success': True, 'annotation': None})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/annotations/<int:image_index>', methods=['POST'])
def save_annotation(image_index):
    """Queue annotation for batched sheet write only (no local file persistence)."""
    try:
        data = request.json or {}

        response_payload = {'success': True}

        if session.get('google_credentials') and current_sheet_input():
            sheet_row = data.get('sheet_row')
            resolved_row = None
            if isinstance(sheet_row, int) and sheet_row >= 2:
                resolved_row = sheet_row
            else:
                row_map = ensure_row_map_for_index(image_index)
                if 0 <= image_index < len(row_map):
                    resolved_row = row_map[image_index]

            if resolved_row is not None:
                sheet_input = current_sheet_input()
                enqueue_sheet_write(sheet_input, image_index, resolved_row, data)

                queue_size = queue_size_for_sheet(sheet_input)
                flushed = 0
                should_flush = bool(data.get('flush_now', False)) or queue_size >= SHEET_FLUSH_THRESHOLD
                if should_flush:
                    result = flush_sheet_queue_for_sheet(
                        session.get('google_credentials'),
                        sheet_input,
                        max_items=SHEET_FLUSH_BATCH_SIZE,
                    )
                    update_session_credentials(result.get('refreshed_credentials'))
                    flushed = result.get('flushed', 0)

                response_payload.update(
                    {
                        'queued_for_sheet': True,
                        'queue_size': queue_size_for_sheet(sheet_input),
                        'flushed': flushed,
                    }
                )

        return jsonify(response_payload)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


if __name__ == '__main__':
    validate_oauth_on_startup()
    app.run(host=Config.HOST, port=Config.PORT, debug=Config.DEBUG)
