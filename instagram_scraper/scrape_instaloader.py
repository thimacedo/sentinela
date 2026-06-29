import os
import json
import csv
from datetime import datetime, timedelta
import time
import requests
from pathlib import Path
from dotenv import load_dotenv
import instaloader

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

def send_ntfy_message(title, message, tags="info", priority="default"):
    """Send a notification to ntfy"""
    headers = {
        "Title": title,
        "Tags": tags,
        "Priority": priority
    }
    try:
        requests.post(NTFY_URL, data=message.encode('utf-8'), headers=headers)
    except Exception as e:
        print(f"Failed to send ntfy notification: {e}")

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
        # Assuming semicolon delimiter based on earlier inspection
        reader = csv.DictReader(f, delimiter=';')
        for row in reader:
            username = row.get('username', '').strip()
            if username:
                usernames.append(username)
    
    print(f"Loaded {len(usernames)} usernames from CSV.")
    send_ntfy_message(
        "Targets Loaded",
        f"Loaded {len(usernames)} target usernames from CSV",
        tags="page_facing_up",
        priority="low"
    )
    
    # We'll process a limited number for testing (first 5)
    # Remove this limit in production
    test_limit = 5
    if len(usernames) > test_limit:
        print(f"Limiting to first {test_limit} usernames for testing.")
        usernames = usernames[:test_limit]
        send_ntfy_message(
            "Test Mode",
            f"Limiting to first {test_limit} usernames for testing",
            tags="mag",
            priority="medium"
        )
    
    all_comments = []
    from datetime import timezone
    two_days_ago = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=2)
    
    for idx, username in enumerate(usernames, start=1):
        try:
            send_ntfy_message(
                f"Processing {username}",
                f"Starting to process target {idx}/{len(usernames)}: {username}",
                tags="hourglass_flowing_sand",
                priority="low"
            )
            
            # Load the profile
            profile = instaloader.Profile.from_username(L.context, username)
            print(f"Processing profile: {profile.username} (full name: {profile.full_name})")
            
            # Get recent posts (non-pinned, from the last 2 days)
            posts = []
            for post in profile.get_posts():
                # Skip pinned posts
                if post.pinned:
                    continue
                # Check if the post is within the last 2 days
                if post.date_utc < two_days_ago:
                    # We've gone back far enough, break
                    break
                posts.append(post)
            
            print(f"Found {len(posts)} recent non-pinned posts from the last 2 days for {username}")
            send_ntfy_message(
                f"Posts Found for {username}",
                f"Found {len(posts)} recent non-pinned posts from the last 2 days",
                tags="mag_right",
                priority="low"
            )
            
            # For each post, get comments
            for post_idx, post in enumerate(posts, start=1):
                try:
                    print(f"  Processing post {post_idx}/{len(posts)}: {post.shortcode}")
                    send_ntfy_message(
                        f"Processing Post {post.shortcode}",
                        f"Extracting comments from post {post.shortcode} ({post_idx}/{len(posts)})",
                        tags="mag_right",
                        priority="low"
                    )
                    
                    # Get comments for this post
                    # Note: Instaloader does not load comments by default, we need to fetch them
                    comments = []
                    try:
                        # We'll get the first page of comments (Instaloader's get_comments returns an iterator)
                        # We can set a limit to avoid too many requests
                        comment_count = 0
                        max_comments_per_post = 100  # Adjust as needed
                        for comment in post.get_comments():
                            # Extract comment data
                            comment_data = {
                                "id": str(comment.id),
                                "username": comment.owner.username,
                                "text": comment.text,
                                "timestamp": comment.created_at_utc.isoformat() if comment.created_at_utc else None,
                                "likes": comment.likes_count,
                                "scraped_at": datetime.now().isoformat(),
                                "target_username": username,
                                "post_shortcode": post.shortcode,
                                "post_url": f"https://www.instagram.com/p/{post.shortcode}/"
                            }
                            comments.append(comment_data)
                            comment_count += 1
                            if comment_count >= max_comments_per_post:
                                print(f"    Reached comment limit ({max_comments_per_post}) for post {post.shortcode}")
                                break
                    except Exception as e:
                        print(f"    Error fetching comments for post {post.shortcode}: {e}")
                        # Continue to next post
                    
                    print(f"    Extracted {len(comments)} comments from post {post.shortcode}")
                    all_comments.extend(comments)
                    
                    # Send a notification for every 10 posts or so to avoid too many messages
                    if post_idx % 10 == 0 or post_idx == len(posts):
                        send_ntfy_message(
                            f"Post {post_idx} Processed",
                            f"Processed {post_idx}/{len(posts)} posts for {username}. Total comments so far: {len(all_comments)}",
                            tags="mag_right",
                            priority="low"
                        )
                    
                    # Be respectful: delay between posts
                    time.sleep(2)
                    
                except Exception as e:
                    print(f"  Error processing post {post.shortcode}: {e}")
                    send_ntfy_message(
                        f"Error Processing Post",
                        f"Error processing post {post.shortcode} for {username}: {str(e)}",
                        tags="warning",
                        priority="medium"
                    )
                    continue
            
            print(f"Finished processing {username}. Total comments collected so far: {len(all_comments)}")
            send_ntfy_message(
                f"Finished {username}",
                f"Finished processing {username}. Total comments collected so far: {len(all_comments)}",
                tags="white_check_mark",
                priority="low"
            )
            
            # Be respectful: delay between targets
            time.sleep(5)
            
        except Exception as e:
            print(f"Error processing username {username}: {e}")
            send_ntfy_message(
                f"Error Processing User",
                f"Error processing username {username}: {str(e)}",
                tags="x",
                priority="high"
            )
            continue
    
    # Save results
    if all_comments:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        json_file = DATA_DIR / f"instagram_comments_{timestamp}.json"
        csv_file = DATA_DIR / f"instagram_comments_{timestamp}.csv"
        
        # Save JSON
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(all_comments, f, ensure_ascii=False, indent=2)
        
        # Save CSV
        if all_comments:
            # Define the order of columns
            fieldnames = [
                "id", "username", "text", "timestamp", "likes", "scraped_at",
                "target_username", "post_shortcode", "post_url"
            ]
            with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(all_comments)
        
        print(f"Saved {len(all_comments)} comments to {json_file} and {csv_file}")
        send_ntfy_message(
            "Scraping Completed",
            f"Successfully scraped {len(all_comments)} comments. Saved to:\n{json_file}\n{csv_file}",
            flags="check_mark",
            priority="default"
        )
    else:
        print("No comments were collected.")
        send_ntfy_message(
            "Scraping Completed - No Data",
            "Scraping process completed but no comments were collected.",
            flags="x",
            priority="medium"
        )
    
    end_time = datetime.now()
    duration = end_time - start_time
    send_ntfy_message(
        "Instagram Scraper Finished",
        f"Scraping process finished at {end_time.isoformat()}. Duration: {duration}",
        tags="wave",
        priority="default"
    )

if __name__ == "__main__":
    main()