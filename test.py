from config import load_settings
from instapaper import InstapaperClient, InstapaperError, RetryableInstapaperError


def main():
    settings = load_settings()

    client = InstapaperClient(
        settings.instapaper_username,
        settings.instapaper_password,
        timeout_seconds=10,
    )

    url = "https://example.com"

    try:
        client.add_bookmark(url=url, title="Test from script")
        print("✅ Successfully added to Instapaper")

    except RetryableInstapaperError as e:
        print("⚠️ Retryable error:", e)

    except InstapaperError as e:
        print("❌ Instapaper error:", e)

    except Exception as e:
        print("💥 Unexpected error:", e)


if __name__ == "__main__":
    main()