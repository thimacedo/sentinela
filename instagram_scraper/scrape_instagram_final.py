import os
import json
import csv
from datetime import datetime, timedelta, timezone
import time
from pathlib import Path
from dotenv import load_dotenv
import instaloader
import requests

# Load environment variables from .env in the sentinel directory
env_path = Path(r"C:\Projetos\sentinela\.env")
load_dotenv(dotenv_path=env_path)

# Configuration
IG_USER = os.getenv("IG_USER")
IG_PASS = os.getenv("IG_PASS")
NTFY_TOPIC = "sentinela"
NTFY_URL = f"https://ntfy.sh/{NTFY_TOPIC}"
DATA_DIR = Path(r"C:\Projetos\sentinela\instagram_scraper\data")
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Helper function to send ntfy notifications
def send_ntfy_message(title, message, tags="info", priority="default"):
    """Send a notification to ntfy"""
    headers = {
        "Title": title,
        "Tags": tags,
        "Priority": priority
    }
    try:
        requests.post(NTFY_URL, data=message.encode('utf-8'), headers=headers)
        print(f"[NTFY] Sent: {title}")
    except Exception as e:
        print(f"[NTFailed to send ntfy notification: {e}")

def main():
    start_time = datetime.now()
    send_ntfy_message(
        "Instagram Scraper Started",
        f"Starting scraping process at {start_time.isoformat()}",
        tags="robot",
        priority="default"
    )
    
    # Initialize Instaloader
    L = instaloader.Instaloader(
        # We don't save photos, we only want metadata
        download_pictures=False,
        download_videos=False,
        download_video_thumbnails=False,
        download_geotags=False,
        download_comments=False,  # We'll handle comments separately
        save_metadata=False,
        compress_json=False,
        # Slow down to avoid being blocked
        request_timeout=10.0,
        # Add a delay between requests to be gentle
        sleep=True,
    )
    
    # Login if credentials are provided
    if IG_USER and IG_PASS:
        try:
            L.login(IG_USER, IG_PASS)
            print(f"Logged in as {IG_USER}")
            send_ntfy_message(
                "Login Successful",
                f"Successfully logged in as {IG_USER}",
                tags="white_check_mark",
                priority="low"
            )
        except Exception as e:
            print(f"Login failed: {e}")
            send_ntfy_message(
                "Login Failed",
                f"Failed to login as {IG_USER}: {str(e)}",
                tags="x",
                priority="high"
            )
            return
    else:
        print("No Instagram credentials provided. Using anonymous mode (limited).")
        send_ntfy_message(
            "No Credentials",
            "Running in anonymous mode (limited functionality)",
            tags="warning",
            priority="medium"
        )
    
    # Read targets from CSV
    csv_path = r"C:\Projetos\sentinela\alvos_sanitizacao.csv"
    if not os.path.exists(csv_path):
        print(f"CSV file not found: {csv_path}")
        send_ntfy_message(
            "Error: CSV not found",
            f"Could not find the target CSV file at {csv_path}",
            tags="x",
            priority="high"
        )
        return
    
    usernames = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        # Assuming semicolon delimiter
        reader = csv.DictReader(f, delimiter=';')
        for row in reader:
            username = row.get('username', '').strip()
            if username:
                usernames.append(username)
    
    print(f"Loaded {len(usernames)} usernames from CSV.")
    send_ntfy_message(
        "Targets Loaded",
        f"Loaded {len(usernames)} usernames from CSV.",
        tags="page_facing_up",
        priority="low"
    )
    
    # We'll process the first 5 users for testing (to avoid rate limits)
    # In production, you might want to process all or use a batch system.
    max_users = 5
    if len(usernames) > max_users:
        print(f"Limiting to first {max_users} users for this run.")
        usernames = usernames[:max_users]
        send_ntfy_message(
            "Limiting Users",
            f"Processing only the first {max_users} users to avoid rate limits.",
            tags="warning",
            priority="medium"
        )
    
    all_comments = []
    seen_post_shortcodes = set()  # To avoid duplicate posts
    cutoff_time = datetime.now(timezone.utc) - timedelta(days=2)
    
    for idx, username in enumerate(usernames, start=1):
        print(f"\n=== Processing {username} ({idx}/{len(usernames)}) ===")
        send_ntfy_message(
            f"Processing {username}",
            f"Starting to process user {username} ({idx}/{len(usernames)})",
            tags="hourglass",
            priority="low"
        )
        
        try:
            profile = instaloader.Profile.from_username(L.context, username)
        except Exception as e:
            print(f"Failed to load profile for {username}: {e}")
            send_ntfy_message(
                f"Profile Load Failed: {username}",
                f"Could not load profile for {username}: {str(e)}",
                tags="x",
                priority="medium"
            )
            continue
        
        post_count = 0
        comment_count_for_user = 0
        
        try:
            # Iterate over the profile's posts (newest first)
            for post in profile.get_posts():
                # Check if the post is within the last 2 days
                if post.date_utc < cutoff_time:
                    print(f"Post {post.shortcode} is older than 2 days, stopping for {username}.")
                    break
                
                # Skip if we've already seen this post (by shortcode)
                if post.shortcode in seen_post_shortcodes:
                    print(f"Skipping duplicate post {post.shortcode}")
                    continue
                
                # Mark this post as seen
                seen_post_shortcodes.add(post.shortcode)
                post_count += 1
                
                print(f"  Processing post {post.shortcode} from {post.date_utc}")
                
                # Try to get comments for this post
                try:
                    # Get all comments (this could be many, but we want as many as possible)
                    comments = list(post.get_comments())
                    print(f"    Found {len(comments)} comments")
                    
                    for comment in comments:
                        # Skip if the comment is from the profile owner? Not required, but we can keep all.
                        comment_data = {
                            "id": f"{post.shortcode}_{comment.id}",
                            "post_shortcode": post.shortcode,
                            "post_date": post.date_utc.isoformat(),
                            "comment_id": str(comment.id),
                            "comment_username": comment.owner.username,
                            "comment_text": comment.text,
                            "comment_created_at": comment.created_at_utc.isoformat(),
                            "comment_likes": comment.likes_count,
                            "target_username": username,
                            "scraped_at": datetime.now(timezone.utc).isoformat()
                        }
                        all_comments.append(comment_data)
                    
                    comment_count_for_user += len(comments)
                    
                except Exception as e:
                    print(f"    Error fetching comments for post {post.shortcode}: {e}")
                    # Continue to next post
                
                # Be gentle: pause between posts to avoid rate limiting
                time.sleep(2)
                
                # Optional: break after a certain number of posts per user to avoid too many requests
                # For now, we'll process all posts from the last 2 days.
            
            print(f"  Finished {username}: {post_count} posts, {comment_count_for_user} comments")
            send_ntfy_message(
                f"Finished {username}",
                f"Processed {post_count} posts, collected {comment_count_for_user} comments.",
                tags="white_check_mark",
                priority="low"
            )
            
        except Exception as e:
            print(f"Error processing {username}: {e}")
            send_ntfy_message(
                f"Error Processing {username}",
                f"Error while processing {username}: {str(e)}",
                tags="x",
                priority="medium"
            )
        
        # Pause between users to be gentle
        if idx < len(usernames):
            print(f"Pausing before next user...")
            time.sleep(5)
    
    # Save results
    if all_comments:
        # JSON output
        json_file = DATA_DIR / "instagram_comments.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(all_comments, f, ensure_ascii=False, indent=2)
        print(f"Saved {len(all_comments)} comments to {json_file}")
        
        # CSV output (flattened)
        csv_file = DATA_DIR / "instagram_comments.csv"
        # Define the order of columns
        fieldnames = [
            "id", "post_shortcode", "post_date",
            "comment_id", "comment_username", "comment_text",
            "comment_created_at", "comment_likes",
            "target_username", "scraped_at"
        ]
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for comment in all_comments:
                writer.writerow(comment)
        print(f"Saved {len(all_comments)} comments to {csv_file}")
        
        send_ntfy_message(
            "Scraping Completed",
            f"Successfully scraped {len(all_comments)} comments from {len(usernames)} users.",
            tags="tada",
            priority="high"
        )
    else:
        print("No comments were collected.")
        send_ntfy_message(
            "Scraping Completed",
            "No comments were collected during this run.",
            tags="warning",
            priority="medium"
        )
    
    end_time = datetime.now()
    duration = end_time - start_time
    print(f"\nTotal time: {duration}")
    send_ntfy_message(
        "Scraping Finished",
        f"Scraping process completed in {duration}.",
        tags="wave",
        priority="default"
    )

if __name__ == "__main__":
    main()