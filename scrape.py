import io
from PIL import Image

from pyzbar.pyzbar import decode
from pyzbar.pyzbar import ZBarSymbol
import warnings

import praw
import requests

import creds


def scrape_reddit(subreddit_name):
    """
    Scrape Reddit for QR codes in images from a specified subreddit.

    Args:
        subreddit_name (str): The name of the subreddit to scrape.

    Returns:
        None
    """
    # Initialize Reddit API
    reddit = praw.Reddit(
        client_id=creds.client_id,
        client_secret=creds.client_secret,
        user_agent=creds.user_agent,
    )

    for submission in reddit.subreddit(subreddit_name).top(
        time_filter="day", limit=None
    ):
        if submission.is_video or submission.is_self:
            continue  # Skip video and self-posts

        if submission.url.endswith((".jpg", ".jpeg", ".png")):
            response = requests.get(submission.url)
            if response.status_code == 200:
                decode_qr_codes(Image.open(io.BytesIO(response.content)))

        if "gallery" in submission.url:
            post_id = submission.url.split(r"/")[-1]
            for image in extract_gallery_images(reddit.submission(id=post_id)):
                decode_qr_codes(Image.open(io.BytesIO(requests.get(image).content)))


def decode_qr_codes(image):
    """
    Decode QR codes in an image and print the QR code data.

    Args:
        image (PIL.Image): The image to decode.

    Returns:
        None
    """
    # Ignore DecompressionBombWarning for large images
    warnings.filterwarnings("ignore", category=Image.DecompressionBombWarning)
    try:
        # Convert to grayscale for better code detection
        gray_image = image.convert("L")

        # Decode QR codes in the image
        decoded_objects = decode(gray_image, symbols=[ZBarSymbol.QRCODE])

        if decoded_objects:
            for obj in decoded_objects:
                qr_data = obj.data.decode("utf-8")
                print(f"QR Code Data: {qr_data}")

    except Exception as e:
        print(f"Error: {e}")


def extract_gallery_images(post):
    """
    Extract image URLs from a Reddit gallery post.

    Args:
        post (praw.models.Submission): The Reddit gallery post.

    Returns:
        list: A list of image URLs.
    """
    images = []

    # Iterate through the gallery items
    for item in post.gallery_data["items"]:
        media_id = item["media_id"]
        media_metadata = post.media_metadata[media_id]
        if media_metadata["e"] == "Image":  # Check if it's an image
            image_url = media_metadata["s"]["u"]
            images.append(image_url)

    return images


if __name__ == "__main__":
    scrape_reddit("lego")
    # scrape_reddit('legostarwars')
    print("Done.")
