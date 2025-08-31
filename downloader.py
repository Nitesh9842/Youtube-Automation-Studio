import instaloader
import os
from urllib.parse import urlparse
from typing import Optional

def extract_shortcode(reel_url: str) -> str:
    """Extract shortcode from Instagram URL"""
    path = urlparse(reel_url).path.strip("/")
    parts = [p for p in path.split("/") if p]
    # Expect ["reel", "<shortcode>"] or ["p", "<shortcode>"]
    if len(parts) >= 2 and parts[0] in {"reel", "p"}:
        return parts[1]
    return parts[-1] if parts else ""
def download_reel_with_audio(
    reel_url: str,
    download_dir: str = "downloads",
    username: Optional[str] = None,
    sessionfile: Optional[str] = None,
    cookiefile: Optional[str] = None,
) -> str:
    """Download Instagram Reel with audio"""
    """Download Instagram Reel with audio"""
    try:
        L = instaloader.Instaloader(
            download_videos=True,
            download_video_thumbnails=False,
            download_geotags=False,
            download_comments=False,
            save_metadata=False,
            compress_json=False,
            max_connection_attempts=3,
        )

       

        # Extract shortcode from URL
        shortcode = extract_shortcode(reel_url)

        # Get the post
        post = instaloader.Post.from_shortcode(L.context, shortcode)

        # Get video URL (contains audio)
        video_url = post.video_url
        if not video_url:
            # Handle sidecar posts (multiple media)
            if post.typename == "GraphSidecar":
                for node in post.get_sidecar_nodes():
                    if node.is_video:
                        video_url = node.video_url
                        break
        
        if not video_url:
            raise Exception("No video URL found for this post")

        # Create download directory
        os.makedirs(download_dir, exist_ok=True)
        
        # Build filename
        filename_base = f"reel_{shortcode}"
        filepath_no_ext = os.path.join(download_dir, filename_base)

        print("Downloading video with audio...")
        # Download the video file with audio
        L.download_pic(filename=filepath_no_ext, url=video_url, mtime=post.date_utc)

        # Find the downloaded file
        target_path = filepath_no_ext + ".mp4"
        if not os.path.exists(target_path):
            # Look for any file starting with our base name
            for f in os.listdir(download_dir):
                if f.startswith(filename_base):
                    target_path = os.path.join(download_dir, f)
                    break

        if not os.path.exists(target_path):
            raise Exception("Download completed but file not found")

        return target_path

    except Exception as e:
        raise Exception(f"Failed to download reel: {str(e)}")

def main():
    """Main function with user interaction"""
    print("Instagram Reel Downloader with Audio")
    print("="*40)
    
    try:
        reel_url = input("Enter Instagram reel URL: ").strip()
        if not reel_url:
            print("No URL provided")
            return                             
        
        print("\nStarting download...")
        video_path = download_reel_with_audio(reel_url)
        
        print(f"\n✅ Successfully downloaded with audio!")
        print(f"📁 File location: {video_path}")
        print(f"📊 File size: {os.path.getsize(video_path) / 1024 / 1024:.2f} MB")
        
    except KeyboardInterrupt:
        print("\n\nDownload cancelled by user")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        print("\nTips:")
        print("- Make sure the URL is correct")
        print("- If the reel is private, ensure you are logged in with valid credentials")

if __name__ == "__main__":
    main()