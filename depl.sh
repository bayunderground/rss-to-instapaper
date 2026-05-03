gcloud projects list
gcloud config set project rss-to-instapush
gcloud services enable cloudscheduler.googleapis.com
gcloud scheduler jobs create http init-job   --schedule="every 24 hours"   --uri="https://rss-to-instapush.ey.r.appspot.com/"   --location=europe-west4
gcloud scheduler jobs list --location=europe-west4

set -a && source .env && set +a && envsubst < app.template.yaml > app.yaml && gcloud app deploy app.yaml cron.yaml