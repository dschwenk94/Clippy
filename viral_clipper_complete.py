#!/usr/bin/env python3
"""
YouTube Viral Clipper - ULTIMATE EDITION WITH SPEAKER SWITCHING
Dynamic speaker switching + smart cropping + viral formatting
This version ACTUALLY implements the viral features! 🔥
"""

import re
import yt_dlp
import ffmpeg
import os
import numpy as np
import cv2
import random
from datetime import datetime
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
import pickle
import time
from dataclasses import dataclass
from typing import List, Tuple, Optional

@dataclass
class Speaker:
    """Represents a detected speaker"""
    id: int
    face_box: Tuple[int, int, int, int]  # x, y, width, height
    center_x: int
    center_y: int
    crop_zone: Tuple[int, int, int, int]  # crop coordinates

class ViralClipGenerator:
    def __init__(self, api_key=None, oauth_credentials_file='client_secrets.json'):
        """Initialize the ULTIMATE viral clip generator"""
        self.api_key = api_key
        self.credentials_file = oauth_credentials_file
        self.credentials = None
        
        # OAuth2 scopes
        self.SCOPES = ['https://www.googleapis.com/auth/youtube.upload']
        
        # Initialize services
        if api_key:
            self.youtube_service = build('youtube', 'v3', developerKey=api_key)
        else:
            self.youtube_service = None
        self.youtube_upload_service = None

    def authenticate_oauth(self):
        """Authenticate using OAuth2 for upload permissions"""
        creds = None
        token_file = 'token.pickle'
        
        if os.path.exists(token_file):
            with open(token_file, 'rb') as token:
                creds = pickle.load(token)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                    print("Refreshed existing credentials")
                except Exception as e:
                    creds = None
            
            if not creds:
                if not os.path.exists(self.credentials_file):
                    print(f"ERROR: OAuth credentials file '{self.credentials_file}' not found!")
                    return False
                
                try:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_file, self.SCOPES)
                    creds = flow.run_local_server(port=0)
                    print("Successfully authenticated with OAuth2")
                except Exception as e:
                    print(f"Error during OAuth authentication: {e}")
                    return False
            
            with open(token_file, 'wb') as token:
                pickle.dump(creds, token)
        
        self.credentials = creds
        
        try:
            self.youtube_upload_service = build('youtube', 'v3', credentials=creds)
            print("Successfully connected to YouTube API with upload permissions")
            return True
        except Exception as e:
            print(f"Error building YouTube service: {e}")
            return False

    def get_video_info(self, video_url):
        """Get basic video information for UI display"""
        try:
            with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
                info = ydl.extract_info(video_url, download=False)
                
                return {
                    'video_id': info.get('id'),
                    'title': info.get('title'),
                    'duration': info.get('duration', 0),
                    'view_count': info.get('view_count'),
                    'upload_date': info.get('upload_date'),
                    'uploader': info.get('uploader'),
                    'description': info.get('description', '')[:500] + '...',
                    'thumbnail': info.get('thumbnail'),
                    'width': info.get('width', 1920),
                    'height': info.get('height', 1080)
                }
                
        except Exception as e:
            print(f"Error getting video info: {e}")
            return None

    def download_video(self, video_url, output_path='downloads'):
        """Download video with smart caching - avoids re-downloads"""
        # Import storage optimizer
        from storage_optimizer import StorageOptimizer
        
        if not os.path.exists(output_path):
            os.makedirs(output_path)
        
        # Initialize storage optimizer
        optimizer = StorageOptimizer(downloads_dir=output_path)
        
        # Check if video already exists
        existing_path, existing_title, video_id = optimizer.check_existing_download(video_url)
        if existing_path:
            return existing_path, existing_title, video_id
        
        # If not found, download it
        ydl_opts = {
            'format': 'best[height<=1080]',
            'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_url, download=False)
                video_title = info.get('title', 'video')
                video_id = info.get('id', '')
                
                print(f"📥 Downloading: {video_title}")
                ydl.download([video_url])
                
                # Find the downloaded file
                for file in os.listdir(output_path):
                    if video_id in file or any(word in file for word in video_title.split()[:3]):
                        file_path = os.path.join(output_path, file)
                        file_size = os.path.getsize(file_path) / (1024*1024)
                        print(f"✅ Downloaded: {file} ({file_size:.1f} MB)")
                        
                        # Add to cache
                        optimizer.add_to_cache(video_url, file_path, video_title)
                        
                        return file_path, video_title, video_id
                        
        except Exception as e:
            print(f"❌ Error downloading video: {e}")
            return None, None, None

    def detect_speakers_from_segment(self, video_path, start_time, duration):
        """Detect speakers from a specific segment of the video"""
        try:
            # Create a temporary clip for analysis
            temp_clip_path = os.path.join('clips', f'temp_analysis_{start_time}s.mp4')
            
            print(f"🎥 Creating temp clip for speaker detection...")
            
            (
                ffmpeg
                .input(video_path, ss=start_time, t=min(duration, 10))  # Analyze first 10 seconds
                .output(temp_clip_path, vcodec='libx264')
                .overwrite_output()
                .run(quiet=True)
            )
            
            # Detect speakers in this segment
            speakers = self.detect_speakers(temp_clip_path)
            
            # Clean up temp file
            if os.path.exists(temp_clip_path):
                os.remove(temp_clip_path)
            
            return speakers
            
        except Exception as e:
            print(f"⚠️  Error in speaker detection: {e}")
            return []

    def detect_speakers(self, video_path):
        """Detect faces and create speaker profiles"""
        try:
            print("👥 Detecting speakers...")
            
            # Load face detection cascade
            face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            
            # Open video
            cap = cv2.VideoCapture(video_path)
            
            # Get video dimensions
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            print(f"📐 Video dimensions: {width}x{height}")
            
            # Sample frames for face detection
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            sample_frames = min(5, max(1, frame_count // 5))
            
            all_faces = []
            
            for i in range(sample_frames):
                frame_pos = (frame_count // sample_frames) * i
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_pos)
                
                ret, frame = cap.read()
                if not ret:
                    continue
                
                # Convert to grayscale for face detection
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                
                # Detect faces
                faces = face_cascade.detectMultiScale(
                    gray, 
                    scaleFactor=1.1, 
                    minNeighbors=5, 
                    minSize=(50, 50)
                )
                
                for (x, y, w, h) in faces:
                    all_faces.append({
                        'x': x, 'y': y, 'w': w, 'h': h,
                        'center_x': x + w//2,
                        'center_y': y + h//2
                    })
            
            cap.release()
            
            if not all_faces:
                print("⚠️  No faces detected, using default positions")
                return self.create_default_speakers(width, height)
            
            # Cluster faces into speakers
            speakers = self.cluster_faces_into_speakers(all_faces, width, height)
            
            print(f"✅ Detected {len(speakers)} speakers")
            for i, speaker in enumerate(speakers):
                print(f"   Speaker {i+1}: Position ({speaker.center_x}, {speaker.center_y})")
            
            return speakers
            
        except Exception as e:
            print(f"❌ Error detecting speakers: {e}")
            return self.create_default_speakers(1920, 1080)

    def cluster_faces_into_speakers(self, faces, width, height):
        """Group detected faces into distinct speakers"""
        if not faces:
            return self.create_default_speakers(width, height)
        
        # Simple clustering by X position (left vs right)
        left_faces = [f for f in faces if f['center_x'] < width // 2]
        right_faces = [f for f in faces if f['center_x'] >= width // 2]
        
        speakers = []
        
        if left_faces:
            avg_x = sum(f['center_x'] for f in left_faces) // len(left_faces)
            avg_y = sum(f['center_y'] for f in left_faces) // len(left_faces)
            crop_zone = self.calculate_crop_zone(avg_x, avg_y, width, height, "left")
            
            speakers.append(Speaker(
                id=0,
                face_box=(avg_x - 100, avg_y - 100, 200, 200),
                center_x=avg_x,
                center_y=avg_y,
                crop_zone=crop_zone
            ))
        
        if right_faces:
            avg_x = sum(f['center_x'] for f in right_faces) // len(right_faces)
            avg_y = sum(f['center_y'] for f in right_faces) // len(right_faces)
            crop_zone = self.calculate_crop_zone(avg_x, avg_y, width, height, "right")
            
            speakers.append(Speaker(
                id=1,
                face_box=(avg_x - 100, avg_y - 100, 200, 200),
                center_x=avg_x,
                center_y=avg_y,
                crop_zone=crop_zone
            ))
        
        return speakers if speakers else self.create_default_speakers(width, height)

    def calculate_crop_zone(self, face_x, face_y, video_width, video_height, position):
        """Calculate optimal crop zone for a speaker"""
        # Target: 1080x1920 (9:16)
        target_width = 1080
        target_height = 1920
        
        # Scale to fit height
        scale_factor = target_height / video_height
        scaled_width = int(video_width * scale_factor)
        
        if scaled_width <= target_width:
            crop_x = 0
        else:
            if position == "left":
                crop_x = max(0, int(face_x * scale_factor) - target_width // 3)
            elif position == "right":
                crop_x = min(scaled_width - target_width, int(face_x * scale_factor) - 2 * target_width // 3)
            else:
                crop_x = (scaled_width - target_width) // 2
        
        return (crop_x, 0, target_width, target_height)

    def create_default_speakers(self, width, height):
        """Create default speaker positions"""
        left_crop = self.calculate_crop_zone(width//4, height//2, width, height, "left")
        right_crop = self.calculate_crop_zone(3*width//4, height//2, width, height, "right")
        
        return [
            Speaker(
                id=0,
                face_box=(width//4 - 100, height//2 - 100, 200, 200),
                center_x=width//4,
                center_y=height//2,
                crop_zone=left_crop
            ),
            Speaker(
                id=1,
                face_box=(3*width//4 - 100, height//2 - 100, 200, 200),
                center_x=3*width//4,
                center_y=height//2,
                crop_zone=right_crop
            )
        ]

    def create_viral_clip_with_speaker_switching(self, video_path, start_time, duration, output_path, speakers):
        """🔥 CREATE VIRAL CLIP WITH EXACT TIMING! 🔥"""
        try:
            print("🔥 CREATING VIRAL CLIP WITH SPEAKER SWITCHING!")
            print(f"📺 Found {len(speakers)} speakers - creating EPIC viral content!")
            
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # 🔧 FIXED: Calculate segments to fill exact duration
            def calculate_segments(total_duration, max_segment_duration=3.5):
                full_segments = int(total_duration / max_segment_duration)
                if full_segments == 0:
                    return [total_duration]
                
                remaining_time = total_duration - (full_segments * max_segment_duration)
                
                if remaining_time <= 0.5:
                    # Distribute evenly across all segments
                    segment_duration = total_duration / full_segments
                    return [segment_duration] * full_segments
                else:
                    # Add remainder as final segment
                    segments = [max_segment_duration] * full_segments
                    segments.append(remaining_time)
                    return segments
            
            segment_durations = calculate_segments(duration, 3.5)
            temp_segments = []
            
            print(f"🎬 Creating {len(segment_durations)} segments with exact timing:")
            print(f"   Segments: {[round(d, 1) for d in segment_durations]} = {sum(segment_durations)}s total")
            
            current_time = 0
            for i, segment_dur in enumerate(segment_durations):
                segment_start_time = start_time + current_time
                
                # Alternate between speakers for viral effect
                speaker = speakers[i % len(speakers)]
                crop_x, crop_y, crop_w, crop_h = speaker.crop_zone
                
                # Create individual segment with speaker-specific crop
                temp_segment = os.path.join('clips', f'viral_seg_{i}.mp4')
                
                print(f"   📹 Segment {i+1}: {segment_start_time:.1f}s for {segment_dur:.1f}s → Speaker {speaker.id+1}")
                
                (
                    ffmpeg
                    .input(video_path, ss=segment_start_time, t=segment_dur)
                    .output(
                        temp_segment,
                        vcodec='libx264',
                        acodec='aac',
                        vf=f'scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920:{crop_x}:{crop_y}',
                        **{'b:v': '3M', 'b:a': '128k', 'preset': 'fast'}
                    )
                    .overwrite_output()
                    .run(quiet=True)
                )
                
                if os.path.exists(temp_segment):
                    temp_segments.append(temp_segment)
                
                current_time += segment_dur
            
            # Combine segments with viral quick cuts
            if temp_segments:
                print("🔗 Combining segments with VIRAL quick cuts...")
                
                # Create concat file for FFmpeg
                concat_file = os.path.join('clips', 'viral_concat_list.txt')
                with open(concat_file, 'w') as f:
                    for segment in temp_segments:
                        f.write(f"file '{os.path.abspath(segment)}'\n")
                
                # Combine all segments into final viral clip
                (
                    ffmpeg
                    .input(concat_file, format='concat', safe=0)
                    .output(output_path, c='copy')
                    .overwrite_output()
                    .run(quiet=True)
                )
                
                # Clean up temp files
                for temp_seg in temp_segments:
                    if os.path.exists(temp_seg):
                        os.remove(temp_seg)
                if os.path.exists(concat_file):
                    os.remove(concat_file)
                
                if os.path.exists(output_path):
                    file_size = os.path.getsize(output_path) / (1024*1024)
                    print(f"🔥 VIRAL CLIP WITH SPEAKER SWITCHING CREATED! ({file_size:.1f} MB)")
                    print(f"🎯 {len(temp_segments)} quick cuts between speakers!")
                    return True
            
            return False
            
        except Exception as e:
            print(f"❌ Error creating viral clip: {e}")
            # Fallback to basic clip
            return self.create_basic_viral_clip(video_path, start_time, duration, output_path)

    def create_smart_single_speaker_clip(self, video_path, start_time, duration, output_path, speakers):
        """Create smart crop for single speaker"""
        try:
            print("🎯 Creating smart single-speaker clip...")
            
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            if speakers and len(speakers) > 0:
                # Use the detected speaker's crop zone
                speaker = speakers[0]
                crop_x, crop_y, crop_w, crop_h = speaker.crop_zone
                
                print(f"👥 Using detected speaker position: crop at ({crop_x}, {crop_y})")
                
                (
                    ffmpeg
                    .input(video_path, ss=start_time, t=duration)
                    .output(
                        output_path,
                        vcodec='libx264',
                        acodec='aac',
                        vf=f'scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920:{crop_x}:{crop_y}',
                        **{'b:v': '3M', 'b:a': '128k', 'preset': 'medium', 'crf': '23'}
                    )
                    .overwrite_output()
                    .run(quiet=True)
                )
            else:
                # Use center crop as fallback
                (
                    ffmpeg
                    .input(video_path, ss=start_time, t=duration)
                    .output(
                        output_path,
                        vcodec='libx264',
                        acodec='aac',
                        vf='scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920',
                        **{'b:v': '3M', 'b:a': '128k', 'preset': 'medium', 'crf': '23'}
                    )
                    .overwrite_output()
                    .run(quiet=True)
                )
            
            if os.path.exists(output_path):
                file_size = os.path.getsize(output_path) / (1024*1024)
                print(f"✅ Smart clip created: {output_path} ({file_size:.1f} MB)")
                return True
            
            return False
            
        except Exception as e:
            print(f"❌ Error creating smart clip: {e}")
            return False

    def create_basic_viral_clip(self, video_path, start_time, duration, output_path):
        """Create a basic viral clip with perfect formatting"""
        try:
            print(f"🎬 Creating basic viral clip: {start_time}s for {duration}s")
            
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            (
                ffmpeg
                .input(video_path, ss=start_time, t=duration)
                .output(
                    output_path,
                    vcodec='libx264',
                    acodec='aac',
                    vf='scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920',
                    **{'b:v': '3M', 'b:a': '128k', 'preset': 'medium', 'crf': '23'}
                )
                .overwrite_output()
                .run(quiet=True)
            )
            
            if os.path.exists(output_path):
                file_size = os.path.getsize(output_path) / (1024*1024)
                print(f"✅ Created basic viral clip: {output_path} ({file_size:.1f} MB)")
                return True
            
            return False
            
        except Exception as e:
            print(f"❌ Error creating basic clip: {e}")
            return False

    def generate_viral_clip(self, video_url, start_time=None, duration=30):
        """
        🔥 MAIN FUNCTION: Generate a viral clip with SPEAKER SWITCHING! 🔥
        This version actually implements the viral features!
        """
        print("🔥 GENERATING VIRAL CLIP WITH SPEAKER SWITCHING!")
        print("🚀 This is the REAL viral engine!")
        print("=" * 60)
        
        # Step 1: Download video
        print("📥 Step 1: Downloading video...")
        video_path, video_title, video_id = self.download_video(video_url)
        if not video_path:
            return None
        
        # Step 2: Find optimal moment if not specified
        if start_time is None:
            # Use strategic timing for podcasts
            fallback_times = [180, 300, 420, 600, 900]
            start_time = random.choice(fallback_times)
            print(f"🎯 Using strategic timing: {start_time}s")
        
        print(f"🎬 Creating viral clip from {start_time}s for {duration}s")
        
        # Step 3: ANALYZE SPEAKERS IN THE SEGMENT
        print("🤖 Step 3: Analyzing speakers in this segment...")
        speakers = self.detect_speakers_from_segment(video_path, start_time, duration)
        
        # Step 4: Create viral clip based on speaker detection
        print("💥 Step 4: Creating VIRAL clip...")
        clip_filename = f"viral_clip_{video_id}_{start_time}s.mp4"
        clip_path = os.path.join('clips', clip_filename)
        
        if len(speakers) >= 2:
            print("🎯 MULTIPLE SPEAKERS DETECTED - CREATING DYNAMIC VIRAL CLIP!")
            success = self.create_viral_clip_with_speaker_switching(
                video_path, start_time, duration, clip_path, speakers
            )
        else:
            print("⚠️  Single/no speakers - using smart crop")
            success = self.create_smart_single_speaker_clip(
                video_path, start_time, duration, clip_path, speakers
            )
        
        if success:
            print("🎉 VIRAL CLIP GENERATED!")
            
            clip_data = {
                'path': clip_path,
                'video_id': video_id,
                'original_title': video_title,
                'start_time': start_time,
                'duration': duration,
                'speakers_detected': len(speakers) if speakers else 0,
                'dynamic_cropping': len(speakers) >= 2,
                'speaker_switching': len(speakers) >= 2,
                'file_size_mb': os.path.getsize(clip_path) / (1024*1024),
                'created_at': datetime.now().isoformat(),
                'title': '',
                'description': '',
                'tags': []
            }
            
            return clip_data
        else:
            print("❌ Failed to generate viral clip")
            return None

    def list_generated_clips(self, clips_dir='clips'):
        """List all generated clips for UI display"""
        clips = []
        
        if not os.path.exists(clips_dir):
            return clips
        
        for filename in os.listdir(clips_dir):
            if filename.endswith('.mp4') and 'viral_clip' in filename:
                file_path = os.path.join(clips_dir, filename)
                file_size = os.path.getsize(file_path) / (1024*1024)
                
                # Extract info from filename
                parts = filename.replace('.mp4', '').split('_')
                if len(parts) >= 4:
                    video_id = parts[2]
                    start_time = parts[3].replace('s', '')
                    
                    clips.append({
                        'filename': filename,
                        'path': file_path,
                        'video_id': video_id,
                        'start_time': start_time,
                        'file_size_mb': file_size,
                        'created_at': datetime.fromtimestamp(os.path.getctime(file_path)).isoformat()
                    })
        
        # Sort by creation time (newest first)
        clips.sort(key=lambda x: x['created_at'], reverse=True)
        return clips

    def upload_to_youtube_shorts(self, video_path, title, description, tags=None):
        """Upload the viral clip to YouTube Shorts"""
        if not self.youtube_upload_service:
            print("❌ Error: OAuth authentication required for upload")
            return False
            
        try:
            if not tags:
                tags = ['Shorts', 'Viral', 'Clip', 'Podcast', 'Trending']
            
            body = {
                'snippet': {
                    'title': title[:100],
                    'description': description[:5000],
                    'tags': tags[:10],
                    'categoryId': '22',
                    'defaultLanguage': 'en',
                    'defaultAudioLanguage': 'en'
                },
                'status': {
                    'privacyStatus': 'private',
                    'selfDeclaredMadeForKids': False,
                    'madeForKids': False
                }
            }
            
            media = MediaFileUpload(video_path, chunksize=-1, resumable=True, mimetype='video/*')
            
            print(f"📤 Uploading viral clip: {title}")
            
            insert_request = self.youtube_upload_service.videos().insert(
                part=','.join(body.keys()),
                body=body,
                media_body=media
            )
            
            response = self.resumable_upload(insert_request)
            
            if response:
                video_id = response.get('id')
                print(f"🔥 VIRAL CLIP UPLOADED! Video ID: {video_id}")
                print(f"🚀 URL: https://www.youtube.com/watch?v={video_id}")
                return video_id
            else:
                return False
                
        except Exception as e:
            print(f"❌ Upload error: {e}")
            return False

    def resumable_upload(self, insert_request):
        """Handle resumable upload with progress tracking"""
        response = None
        error = None
        retry = 0
        
        while response is None:
            try:
                status, response = insert_request.next_chunk()
                if status:
                    progress = int(status.progress() * 100)
                    print(f"📊 Upload progress: {progress}%")
            except Exception as e:
                error = e
                if retry < 3:
                    retry += 1
                    print(f"⚠️  Upload error, retrying ({retry}/3): {error}")
                    time.sleep(2 ** retry)
                else:
                    print(f"❌ Upload failed after 3 retries: {error}")
                    break
        
        return response


def main():
    """Test the VIRAL clip generator with speaker switching"""
    print("🔥 VIRAL CLIP GENERATOR - SPEAKER SWITCHING EDITION")
    print("🎯 This version ACTUALLY does speaker switching!")
    print("=" * 60)
    
    # Test video
    VIDEO_URL = "https://www.youtube.com/watch?v=dLCbvgFJphA"
    
    generator = ViralClipGenerator()
    
    # Test 1: Get video info
    print("📺 Test 1: Getting video info...")
    video_info = generator.get_video_info(VIDEO_URL)
    if video_info:
        print(f"   Title: {video_info['title'][:50]}...")
        print(f"   Duration: {video_info['duration']}s")
        print(f"   Dimensions: {video_info['width']}x{video_info['height']}")
    
    # Test 2: Generate VIRAL clip with speaker switching
    print("\n🔥 Test 2: Generating VIRAL clip with speaker switching...")
    clip_data = generator.generate_viral_clip(VIDEO_URL, start_time=300, duration=25)
    
    if clip_data:
        print("✅ VIRAL CLIP GENERATED!")
        print(f"   Path: {clip_data['path']}")
        print(f"   Size: {clip_data['file_size_mb']:.1f} MB")
        print(f"   Speakers: {clip_data['speakers_detected']}")
        print(f"   Dynamic cropping: {clip_data['dynamic_cropping']}")
        print(f"   Speaker switching: {clip_data.get('speaker_switching', False)}")
        
        if clip_data.get('speaker_switching'):
            print("🔥 SUCCESS! This clip has VIRAL speaker switching!")
        else:
            print("⚠️  Single speaker detected - smart crop applied")
        
        # Test 3: List generated clips
        print("\n📋 Test 3: Listing generated clips...")
        clips = generator.list_generated_clips()
        print(f"   Found {len(clips)} total clips")
        
        print("\n🎉 VIRAL ENGINE WITH SPEAKER SWITCHING READY!")
        print("💡 Next: Build UI to control this viral machine!")
    else:
        print("❌ Clip generation failed")

if __name__ == "__main__":
    main()
