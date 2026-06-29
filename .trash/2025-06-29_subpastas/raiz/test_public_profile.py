import instaloader
L = instaloader.Instaloader(
    download_pictures=False,
    download_videos=False,
    download_video_thumbnails=False,
    download_geotags=False,
    download_comments=False,
    save_metadata=False,
    compress_json=False,
)
try:
    profile = instaloader.Profile.from_username(L.context, "carlosjordy")
    print(f"Profile loaded: {profile.username}")
    print(f"Is private: {profile.is_private}")
    # Get first post
    for post in profile.get_posts():
        print(f"Post {post.shortcode} - {post.date_utc} - likes: {post.likes}")
        break
except Exception as e:
    print(f"Error: {e}")