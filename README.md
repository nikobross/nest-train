# Nest Train Annotation Tool

Lightweight Google Sheets annotation tool for labeling plastic in bird nest images.

## What It Does

- Google OAuth sign-in
- Reads image links from the `list` column in your Google Sheet
- Writes annotation columns back to the same sheet:
  - `has_plastic`
  - `plastic_location_labels`
  - `annotated_at`
  - `last_annotated_index`
- Uses batched writes for better performance

## One-Time Setup (after clone)

```bash
./setup.sh
```

Then edit `backend/.env` and set:

```env
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
GOOGLE_REDIRECT_URI=http://localhost:5001/api/auth/google-callback
FRONTEND_URL=http://localhost:8000
CORS_ORIGINS=http://localhost:8000,http://127.0.0.1:8000,null
```

## Run the Project

```bash
./run.sh
```

This starts:

- Frontend: http://localhost:8000
- Backend: http://localhost:5001

`./start.sh` also works (wrapper).

## Usage

1. Open http://localhost:8000
2. Click **Sign in with Google**
3. Paste Google Sheet URL/ID
4. Click **Connect Sheet**
5. Click **Start Annotation**

## Google Sheet Requirements

Required input column:

- `list`

Output columns are auto-created if missing:

- `has_plastic`
- `plastic_location_labels`
- `annotated_at`
- `last_annotated_index`

## Notes

- Annotation writes are queued and flushed in batches.
- If backend is killed unexpectedly, unsynced in-memory queue items may be lost.
- Keep the app running until pending writes are flushed.
