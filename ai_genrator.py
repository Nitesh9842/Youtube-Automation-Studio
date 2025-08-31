import google.generativeai as genai
import os
import json
from typing import Dict, List, Optional
import cv2
from datetime import datetime
from dotenv import load_dotenv
import base64
import tempfile
from PIL import Image
import numpy as np

# Load environment variables from .env file
load_dotenv()

class AIMetadataGenerator:
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the AI Metadata Generator with Gemini 2.0 Flash"""
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            raise ValueError("Gemini API key not found. Please set GEMINI_API_KEY in .env file or pass it as parameter.")
        
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
    
    def extract_video_frames(self, video_path: str, num_frames: int = 3) -> List[str]:
        """Extract representative frames from video for AI analysis"""
        try:
            cap = cv2.VideoCapture(video_path)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            frames = []
            
            # Extract frames at regular intervals
            for i in range(num_frames):
                frame_number = int((i + 1) * frame_count / (num_frames + 1))
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
                ret, frame = cap.read()
                
                if ret:
                    # Convert BGR to RGB
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    # Convert to PIL Image
                    pil_image = Image.fromarray(frame_rgb)
                    # Resize for efficient processing
                    pil_image = pil_image.resize((512, 512), Image.Resampling.LANCZOS)
                    frames.append(pil_image)
            
            cap.release()
            return frames
            
        except Exception as e:
            print(f"Error extracting frames: {e}")
            return []
    
    def analyze_video_content(self, video_path: str) -> str:
        """Analyze video content using AI vision to understand what's actually in the video"""
        try:
            frames = self.extract_video_frames(video_path, 2)
            
            if not frames:
                return "Unable to analyze video content"
            
            # Analyze the first frame for content
            frame = frames[0]
            
            prompt = """
            Analyze this video frame and describe what you see briefly. Focus on:
            1. Main subject/person and their actions
            2. Setting/location 
            3. Key objects or activities visible
            4. Overall mood and style
            
            Keep the description concise and specific to what's actually shown in the image.
            """
            
            response = self.model.generate_content([prompt, frame])
            return response.text.strip()
            
        except Exception as e:
            print(f"Error analyzing video content: {e}")
            return "Video content analysis unavailable"
    
    def generate_title(self, video_analysis: str) -> str:
        """Generate engaging YouTube title based on actual video content"""
        prompt = f"""
        Based on this video analysis, create a catchy YouTube title:
        
        VIDEO CONTENT: {video_analysis}
        
        Requirements:
        - Make it engaging and click-worthy
        - Keep it under 80 characters
        - Focus on the main subject/activity in the video
        - Make it SEO-friendly with trending keywords
        
        Return only the title, nothing else.
        """
        
        try:
            response = self.model.generate_content(prompt)
            return response.text.strip().replace('"', '').replace("'", "")
        except Exception as e:
            print(f"Error generating title: {e}")
            return "Amazing Video Content"
    
    def generate_description(self, video_analysis: str) -> str:
        """Generate complete YouTube description with everything needed"""
        prompt = f"""
        Create a complete YouTube video description based on this video analysis:
        
        VIDEO CONTENT: {video_analysis}
        
        Structure the description exactly like this:
        
        1. Write exactly 10 lines of engaging description about what viewers will see
        2. Add a line break then write "Keywords:" followed by exactly 20 relevant keywords separated by commas
        3. Add a line break then write "Hashtags:" followed by exactly 30 hashtags (include #shorts, #viral, #trending and other relevant ones)
        4. Add a line break then add this copyright disclaimer: "⚠️ Copyright Disclaimer: This content is used for educational and entertainment purposes. All rights belong to their respective owners. If you are the owner and want this removed, please contact us."
        
        Make sure to include trending keywords and hashtags relevant to the actual video content.
        """
        
        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            print(f"Error generating description: {e}")
            return self._fallback_description()
    
    def _fallback_description(self) -> str:
        """Fallback description when AI generation fails"""
        return """Amazing video content that will keep you entertained!
Watch this incredible moment captured on video.
Perfect for sharing with friends and family.
Don't forget to like and subscribe for more content.
This video showcases some really cool stuff.
You won't believe what happens in this video.
Make sure to watch until the end.
Comment below what you think about this.
Share this video if you enjoyed it.
Thanks for watching our content!

Keywords: viral video, trending content, amazing moments, entertainment, social media, short video, funny clips, must watch, incredible, awesome, cool stuff, viral clips, trending now, popular video, engaging content, shareable, entertaining, video content, social sharing, watch now

Hashtags: #shorts #viral #trending #amazing #entertainment #video #content #socialmedia #funny #cool #awesome #mustwatch #incredible #popular #engaging #shareable #entertaining #videooftheday #trend #viral2024 #shortsvideo #viralshorts #trendingshorts #amazingvideo #viralcontent #shortsfeed #explore #fyp #foryou #viralmoment

⚠️ Copyright Disclaimer: This content is used for educational and entertainment purposes. All rights belong to their respective owners. If you are the owner and want this removed, please contact us."""
    
    def generate_complete_metadata(self, video_path: str, **kwargs) -> Dict:
        """Generate complete metadata package based on actual video analysis"""
        
        print("🤖 Analyzing video content with AI...")
        video_analysis = self.analyze_video_content(video_path)
        print(f"📹 Video analysis complete")
        
        print("🎯 Generating title...")
        title = self.generate_title(video_analysis)
        
        print("📝 Generating description with keywords and hashtags...")
        description = self.generate_description(video_analysis)
        
        # Extract hashtags and keywords from description for separate fields
        description_lines = description.split('\n')
        hashtags = []
        keywords = []
        tags = []
        
        for line in description_lines:
            if line.startswith('Hashtags:'):
                hashtags_text = line.replace('Hashtags:', '').strip()
                hashtags = [tag.strip() for tag in hashtags_text.split() if tag.startswith('#')]
            elif line.startswith('Keywords:'):
                keywords_text = line.replace('Keywords:', '').strip()
                keywords = [kw.strip() for kw in keywords_text.split(',')]
                # Use first 15 keywords as tags for YouTube
                tags = keywords[:15]
        
        metadata = {
            "video_analysis": video_analysis,
            "title": title,
            "description": description,
            "tags": tags,
            "hashtags": hashtags,
            "keywords": keywords,
            "generated_at": datetime.now().isoformat()
        }
        
        return metadata
    
    def save_metadata(self, metadata: Dict, output_path: str):
        """Save metadata to JSON file"""
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            print(f"Metadata saved to: {output_path}")
        except Exception as e:
            print(f"Error saving metadata: {e}")

# Example usage
if __name__ == "__main__":
    # Initialize the generator (API key will be loaded from .env)
    generator = AIMetadataGenerator()
    
    # Example video processing
    video_path = r"c:\Users\DELL\OneDrive\Desktop\youtube automation ai\sample_video.mp4"
    
    # Generate complete metadata
    metadata = generator.generate_complete_metadata(video_path=video_path)
    
    # Print results
    print("Generated Metadata:")
    print("-" * 50)
    print(f"Title: {metadata['title']}")
    print(f"\nDescription:\n{metadata['description']}")
    
    # Save to file
    output_file = r"c:\Users\DELL\OneDrive\Desktop\youtube automation ai\metadata_output.json"
    generator.save_metadata(metadata, output_file)