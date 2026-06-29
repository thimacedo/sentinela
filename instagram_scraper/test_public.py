import instaloader
import sys

L = instaloader.Instaloader(
    download_pictures=False,
    download_videos=False,
    download_video_thumbnails=False,
    download_geotags=False,
    download_comments=False,
    save_metadata=False,
    compress_json=False,
)

# Try a public profile, e.g., 'instagram' itself
test_username = 'instagram'
try:
    profile = instaloader.Profile.from_username(L.context, test_username)
    print(f"Successfully loaded profile for {test_username}")
    print(f"User ID: {profile.userid}")
    print(f"Followers: {profile.followers}")
    # Get first few posts
    count = 0
    for post in profile.get_posts():
        print(f"Post {post.shortcode} - {post.date_utc} - {post.likes} likes")
        count += 1
        if count >= 3:
            break
        # Try to get comments (first few)
        try:
            comment_count = 0
            for comment in post.get_comments():
                print(f"  Comment by {comment.owner.username}: {comment.text[:50]}")
                comment_count += 1
                if comment_count >= 2:
                    break
        except Exception as e:
            print(f"  Could not fetch comments: {e}")
except Exception as e:
    print(f"Failed to load profile: {e}")
    sys.exit(1)