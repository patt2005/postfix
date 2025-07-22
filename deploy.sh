#!/bin/bash

# Deploy to Google Cloud Run with environment variables

gcloud run deploy auto-poster-tt \
  --image gcr.io/$PROJECT_ID/revid-api:latest \
  --platform managed \
  --region northamerica-northeast1 \
  --allow-unauthenticated \
  --set-env-vars "TIKTOK_CLIENT_KEY=sbawzd7dk5t7haj6v6" \
  --set-env-vars "TIKTOK_CLIENT_SECRET=nZZLnLC2iYGDCWOQzyTKdIAUw9KBqGIy" \
  --set-env-vars "TIKTOK_REDIRECT_URI=https://auto-poster-tt-57018476417.northamerica-northeast1.run.app/auth/tiktok/callback" \
  --set-env-vars "FLASK_SECRET_KEY=Ks7n2_x9RJkHjqW5tXvFmR0BcZ1Y8pTfLw3aQnUg4xE"