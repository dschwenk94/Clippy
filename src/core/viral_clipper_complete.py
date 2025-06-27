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
        from src.core.storage_optimizer import StorageOptimizer
        
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
        """Detect speakers from a specific segment of the video with smart sampling"""
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
            
            # First, try to get audio speaker info for smarter sampling
            try:
                import whisper
                print("🎤 Analyzing audio for speaker patterns...")
                
                # Extract audio for analysis
                audio_path = temp_clip_path.replace('.mp4', '_audio.wav')
                (
                    ffmpeg
                    .input(temp_clip_path)
                    .output(audio_path, acodec='pcm_s16le', ac=1, ar='16000')
                    .overwrite_output()
                    .run(quiet=True)
                )
                
                # Get transcription with segments
                model = whisper.load_model("base")
                result = model.transcribe(audio_path, language='en')
                segments = result.get('segments', [])
                
                # Estimate number of speakers from segment patterns
                estimated_speakers = self.estimate_speakers_from_segments(segments)
                print(f"📊 Estimated {estimated_speakers} speaker(s) from audio patterns")
                
                # Clean up audio file
                if os.path.exists(audio_path):
                    os.remove(audio_path)
                    
            except Exception as e:
                print(f"⚠️  Audio analysis failed, using standard detection: {e}")
                estimated_speakers = 2  # Default assumption
            
            # Detect speakers with smart sampling
            speakers = self.detect_speakers_with_smart_sampling(temp_clip_path, estimated_speakers)
            
            # Clean up temp file
            if os.path.exists(temp_clip_path):
                os.remove(temp_clip_path)
            
            return speakers
            
        except Exception as e:
            print(f"⚠️  Error in speaker detection: {e}")
            return []

    def estimate_speakers_from_segments(self, segments):
        """Estimate number of speakers from audio segment patterns"""
        if not segments:
            return 1
            
        # Look for conversation patterns
        segment_lengths = [seg['end'] - seg['start'] for seg in segments]
        avg_length = sum(segment_lengths) / len(segment_lengths) if segment_lengths else 0
        
        # Short segments with alternation suggest multiple speakers
        if avg_length < 5.0 and len(segments) > 3:
            # Check for alternating pattern
            return 2
        elif len(segments) > 10 and avg_length < 3.0:
            # Many short segments might indicate 3+ speakers
            return 3
        else:
            # Longer segments suggest single speaker
            return 1
    
    def detect_speakers_with_smart_sampling(self, video_path, estimated_speakers):
        """Detect speakers using smart sampling based on estimated speaker count"""
        try:
            print(f"👥 Smart speaker detection for {estimated_speakers} estimated speaker(s)...")
            
            # Determine sampling strategy
            cap = cv2.VideoCapture(video_path)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            duration = frame_count / fps if fps > 0 else 10
            cap.release()
            
            # Calculate sample points based on estimated speakers
            if estimated_speakers == 1:
                # Single speaker: sample evenly throughout
                num_samples = 15
                sample_points = [i * duration / num_samples for i in range(num_samples)]
                print(f"📍 Single speaker mode: sampling {num_samples} frames evenly")
            else:
                # Multiple speakers: dense sampling for better detection
                num_samples = min(30, max(20, estimated_speakers * 10))
                sample_points = self.get_smart_sample_points(duration, estimated_speakers, num_samples)
                print(f"📍 Multi-speaker mode: sampling {num_samples} frames strategically")
            
            # Convert time points to frame numbers
            sample_frames = [int(t * fps) for t in sample_points if t * fps < frame_count]
            
            # Detect faces at sample points
            all_faces = self.detect_faces_at_frames(video_path, sample_frames, estimated_speakers)
            
            # Get video dimensions for clustering
            cap = cv2.VideoCapture(video_path)
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            cap.release()
            
            # Cluster faces into speakers
            speakers = self.cluster_faces_into_speakers(all_faces, width, height)
            
            # Verify detection against audio estimate
            if len(speakers) < estimated_speakers and estimated_speakers > 1:
                print(f"⚠️  Detected {len(speakers)} faces but audio suggests {estimated_speakers} speakers")
                print("🔄 Attempting enhanced detection...")
                
                # Try again with more aggressive detection
                enhanced_faces = self.detect_faces_enhanced(video_path, sample_frames)
                enhanced_speakers = self.cluster_faces_into_speakers(enhanced_faces, width, height)
                
                if len(enhanced_speakers) > len(speakers):
                    print(f"✅ Enhanced detection found {len(enhanced_speakers)} speakers")
                    return enhanced_speakers
            
            return speakers
            
        except Exception as e:
            print(f"❌ Error in smart speaker detection: {e}")
            # Fall back to original detection method
            return self.detect_speakers(video_path)
    
    def get_smart_sample_points(self, duration, estimated_speakers, num_samples):
        """Get smart sampling points for multi-speaker scenarios"""
        sample_points = []
        
        # Sample at potential speaker transitions
        # For 2 speakers, expect switches every 3-8 seconds
        # For 3+ speakers, expect more frequent switches
        avg_switch_time = 5.0 if estimated_speakers == 2 else 3.0
        
        # Add samples around expected transition points
        current_time = 0
        while current_time < duration:
            # Sample before, at, and after potential transition
            for offset in [-0.5, 0, 0.5]:
                sample_time = current_time + offset
                if 0 <= sample_time < duration:
                    sample_points.append(sample_time)
            current_time += avg_switch_time
        
        # Add some random samples to catch unexpected moments
        import random
        for _ in range(num_samples // 4):
            sample_points.append(random.uniform(0, duration))
        
        # Remove duplicates and sort
        sample_points = sorted(list(set(sample_points)))[:num_samples]
        
        return sample_points
    
    def detect_faces_at_frames(self, video_path, frame_numbers, estimated_speakers):
        """Detect faces at specific frame numbers with progressive detection"""
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        profile_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_profileface.xml')
        
        cap = cv2.VideoCapture(video_path)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        all_faces = []
        
        # Adjust detection parameters based on estimated speakers
        if estimated_speakers == 1:
            # Single speaker: look for larger, centered faces
            detection_passes = [
                {'cascade': face_cascade, 'scaleFactor': 1.05, 'minNeighbors': 4, 'minSize': (120, 120), 'name': 'frontal-single'},
                {'cascade': face_cascade, 'scaleFactor': 1.03, 'minNeighbors': 3, 'minSize': (100, 100), 'name': 'frontal-relaxed'},
            ]
        else:
            # Multiple speakers: more aggressive detection
            detection_passes = [
                {'cascade': face_cascade, 'scaleFactor': 1.05, 'minNeighbors': 3, 'minSize': (100, 100), 'name': 'frontal-optimized'},
                {'cascade': face_cascade, 'scaleFactor': 1.03, 'minNeighbors': 2, 'minSize': (80, 80), 'name': 'frontal-aggressive'},
                {'cascade': profile_cascade, 'scaleFactor': 1.05, 'minNeighbors': 3, 'minSize': (100, 100), 'name': 'profile'},
                {'cascade': face_cascade, 'scaleFactor': 1.02, 'minNeighbors': 1, 'minSize': (60, 60), 'name': 'frontal-relaxed'}
            ]
        
        for i, frame_num in enumerate(frame_numbers):
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
            ret, frame = cap.read()
            if not ret:
                continue
                
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            frame_faces = []
            
            # Try detection passes
            for pass_config in detection_passes:
                if len(frame_faces) >= estimated_speakers:
                    break
                    
                faces = pass_config['cascade'].detectMultiScale(
                    gray,
                    scaleFactor=pass_config['scaleFactor'],
                    minNeighbors=pass_config['minNeighbors'],
                    minSize=pass_config['minSize']
                )
                
                if len(faces) > 0:
                    print(f"   Frame {i}: Found {len(faces)} faces using {pass_config['name']} detection")
                    frame_faces.extend(faces)
            
            # Add valid faces
            for (x, y, w, h) in frame_faces:
                face_area_ratio = (w * h) / (width * height)
                # Adjusted thresholds based on speaker count
                min_ratio = 0.03 if estimated_speakers > 1 else 0.05
                if min_ratio < face_area_ratio < 0.5:
                    aspect_ratio = w / h
                    if 0.5 < aspect_ratio < 2.0:
                        min_size = 120 if estimated_speakers == 1 else 100
                        if w >= min_size and h >= min_size:
                            all_faces.append({
                                'x': x, 'y': y, 'w': w, 'h': h,
                                'center_x': x + w//2,
                                'center_y': y + h//2,
                                'area': w * h,
                                'face_area_ratio': face_area_ratio,
                                'frame': frame_num
                            })
        
        cap.release()
        return all_faces
    
    def detect_faces_enhanced(self, video_path, frame_numbers):
        """Enhanced face detection with lower thresholds for difficult cases"""
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        cap = cv2.VideoCapture(video_path)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        all_faces = []
        
        # Very aggressive detection for last resort
        for frame_num in frame_numbers:
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
            ret, frame = cap.read()
            if not ret:
                continue
                
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Try with very low thresholds
            faces = face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.01,
                minNeighbors=1,
                minSize=(50, 50)
            )
            
            for (x, y, w, h) in faces:
                face_area_ratio = (w * h) / (width * height)
                if 0.02 < face_area_ratio < 0.6:  # Even more relaxed
                    all_faces.append({
                        'x': x, 'y': y, 'w': w, 'h': h,
                        'center_x': x + w//2,
                        'center_y': y + h//2,
                        'area': w * h,
                        'face_area_ratio': face_area_ratio,
                        'frame': frame_num
                    })
        
        cap.release()
        return all_faces
    
    def detect_speakers(self, video_path):
        """Detect faces and create speaker profiles with multiple detection passes"""
        try:
            print("👥 Detecting speakers...")
            
            # Load face detection cascades
            face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            profile_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_profileface.xml')
            
            # Open video
            cap = cv2.VideoCapture(video_path)
            
            # Get video dimensions
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            print(f"📐 Video dimensions: {width}x{height}")
            
            # Sample frames for face detection
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            sample_frames = min(20, max(5, frame_count // 30))
            
            all_faces = []
            
            # Multiple detection passes with different parameters
            detection_passes = [
                # Pass 1: Normal detection with larger minimum size for primary speakers
                {'cascade': face_cascade, 'scaleFactor': 1.05, 'minNeighbors': 3, 'minSize': (100, 100), 'name': 'frontal-optimized'},
                # Pass 2: More aggressive detection but still decent size
                {'cascade': face_cascade, 'scaleFactor': 1.03, 'minNeighbors': 2, 'minSize': (80, 80), 'name': 'frontal-aggressive'},
                # Pass 3: Profile face detection
                {'cascade': profile_cascade, 'scaleFactor': 1.05, 'minNeighbors': 3, 'minSize': (100, 100), 'name': 'profile'},
                # Pass 4: Last resort with smaller faces (but not tiny)
                {'cascade': face_cascade, 'scaleFactor': 1.02, 'minNeighbors': 1, 'minSize': (60, 60), 'name': 'frontal-relaxed'}
            ]
            
            for i in range(sample_frames):
                frame_pos = (frame_count // sample_frames) * i
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_pos)
                
                ret, frame = cap.read()
                if not ret:
                    continue
                
                # Convert to grayscale for face detection
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                
                # Try multiple detection passes
                frame_faces = []
                for pass_config in detection_passes:
                    if len(frame_faces) > 0:  # If we already found faces, skip remaining passes
                        break
                    
                    faces = pass_config['cascade'].detectMultiScale(
                        gray, 
                        scaleFactor=pass_config['scaleFactor'], 
                        minNeighbors=pass_config['minNeighbors'], 
                        minSize=pass_config['minSize']
                    )
                    
                    if len(faces) > 0:
                        print(f"   Frame {i}: Found {len(faces)} faces using {pass_config['name']} detection")
                        frame_faces.extend(faces)
                
                # Add detected faces with size filtering
                for (x, y, w, h) in frame_faces:
                    # Filter out faces that are too small or too large (likely false positives)
                    face_area_ratio = (w * h) / (width * height)
                    # INCREASED minimum from 0.1% to 5% to filter out background faces
                    if 0.05 < face_area_ratio < 0.5:  # Face should be 5% to 50% of frame
                        aspect_ratio = w / h
                        if 0.5 < aspect_ratio < 2.0:  # Face should be roughly square
                            # Additional size check - face should be at least 150x150 pixels
                            if w >= 150 and h >= 150:
                                all_faces.append({
                                    'x': x, 'y': y, 'w': w, 'h': h,
                                    'center_x': x + w//2,
                                    'center_y': y + h//2,
                                    'area': w * h,
                                    'face_area_ratio': face_area_ratio
                                })
            
            cap.release()
            
            if not all_faces:
                print("⚠️  No faces detected (or all were too small), using default positions")
                return self.create_default_speakers(width, height)
            
            # Sort faces by size (largest first) for debugging
            all_faces.sort(key=lambda f: f['area'], reverse=True)
            print(f"🔍 Found {len(all_faces)} valid faces after filtering")
            if all_faces:
                largest = all_faces[0]
                print(f"   Largest face: {largest['w']}x{largest['h']} pixels ({largest['face_area_ratio']*100:.1f}% of frame)")
            
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
        """Group detected faces into distinct speakers with improved clustering"""
        if not faces:
            return self.create_default_speakers(width, height)
        
        # Calculate center of frame
        center_x = width // 2
        center_y = height // 2
        
        # Add distance from center and normalize positions
        for face in faces:
            face['distance_from_center'] = abs(face['center_x'] - center_x)
            face['face_size'] = face['w'] * face['h']
            face['normalized_x'] = face['center_x'] / width
            face['normalized_y'] = face['center_y'] / height
        
        # Use DBSCAN-like clustering for better grouping
        clusters = self.improved_face_clustering(faces, width, height)
        
        # Filter clusters by size and consistency
        valid_clusters = []
        for cluster in clusters:
            # Require at least 2 detections per speaker (temporal consistency)
            if len(cluster) >= 2:
                valid_clusters.append(cluster)
            # Or a single very large/centered face (likely single speaker)
            elif len(cluster) == 1 and cluster[0]['face_area_ratio'] > 0.1:
                valid_clusters.append(cluster)
        
        # If no valid clusters, use all clusters
        if not valid_clusters:
            valid_clusters = clusters
        
        # Create speakers from clusters
        speakers = []
        for i, cluster in enumerate(valid_clusters[:3]):  # Max 3 speakers
            # Calculate weighted average position (larger faces have more weight)
            total_weight = sum(f['face_size'] for f in cluster)
            avg_x = sum(f['center_x'] * f['face_size'] for f in cluster) // total_weight
            avg_y = sum(f['center_y'] * f['face_size'] for f in cluster) // total_weight
            avg_size = total_weight // len(cluster)
            
            # Determine position type
            if abs(avg_x - center_x) < width * 0.15:
                position = "center"
            elif avg_x < center_x:
                position = "left"
            else:
                position = "right"
            
            crop_zone = self.calculate_crop_zone(avg_x, avg_y, width, height, position)
            
            speakers.append(Speaker(
                id=i,
                face_box=(avg_x - 100, avg_y - 100, 200, 200),
                center_x=avg_x,
                center_y=avg_y,
                crop_zone=crop_zone
            ))
        
        # Sort speakers by combination of size and center distance
        # Primary speaker should be large and/or centered
        speakers.sort(key=lambda s: (abs(s.center_x - center_x) / width) * 0.5 + 
                                   (1.0 - (s.face_box[2] * s.face_box[3]) / (width * height)) * 0.5)
        
        # Re-assign IDs based on importance
        for i, speaker in enumerate(speakers):
            speaker.id = i
        
        return speakers if speakers else self.create_default_speakers(width, height)
    
    def improved_face_clustering(self, faces, width, height):
        """Improved clustering using spatial and temporal information"""
        if not faces:
            return []
        
        # Parameters for clustering
        spatial_threshold = 0.15  # 15% of frame width/height
        
        clusters = []
        used_indices = set()
        
        # Sort faces by size (larger first) to prioritize main speakers
        sorted_faces = sorted(enumerate(faces), key=lambda x: x[1]['face_size'], reverse=True)
        
        for idx, face in sorted_faces:
            if idx in used_indices:
                continue
                
            # Start new cluster
            cluster = [face]
            used_indices.add(idx)
            
            # Find similar faces
            for other_idx, other_face in sorted_faces:
                if other_idx in used_indices:
                    continue
                    
                # Calculate normalized distance
                x_dist = abs(face['normalized_x'] - other_face['normalized_x'])
                y_dist = abs(face['normalized_y'] - other_face['normalized_y'])
                
                # Check spatial proximity
                if x_dist < spatial_threshold and y_dist < spatial_threshold:
                    # Also check size similarity (faces shouldn't vary too much in size)
                    size_ratio = min(face['face_size'], other_face['face_size']) / max(face['face_size'], other_face['face_size'])
                    if size_ratio > 0.4:  # Sizes are reasonably similar
                        cluster.append(other_face)
                        used_indices.add(other_idx)
            
            clusters.append(cluster)
        
        return clusters

    def calculate_crop_zone(self, face_x, face_y, video_width, video_height, position):
        """Calculate optimal crop zone with center-focus priority"""
        # Target: 1080x1920 (9:16)
        target_width = 1080
        target_height = 1920
        
        # Scale to fit height
        scale_factor = target_height / video_height
        scaled_width = int(video_width * scale_factor)
        scaled_face_x = int(face_x * scale_factor)
        
        if scaled_width <= target_width:
            # Video is narrower than target - no horizontal cropping needed
            crop_x = 0
        else:
            if position == "center":
                # Center the crop on the face with slight headroom preference
                ideal_crop_x = scaled_face_x - target_width // 2
                # Add slight offset up for headroom (news presenter framing)
                ideal_crop_x -= int(target_width * 0.05)  # 5% offset for better framing
                
                # Ensure crop stays within bounds
                crop_x = max(0, min(ideal_crop_x, scaled_width - target_width))
                
            elif position == "left":
                # For left position, keep some space on the left but focus on speaker
                ideal_crop_x = scaled_face_x - int(target_width * 0.6)  # Speaker at 60% from left
                crop_x = max(0, min(ideal_crop_x, scaled_width - target_width))
                
            elif position == "right":
                # For right position, keep some space on the right but focus on speaker
                ideal_crop_x = scaled_face_x - int(target_width * 0.4)  # Speaker at 40% from left
                crop_x = max(0, min(ideal_crop_x, scaled_width - target_width))
                
            else:
                # Default fallback - center crop
                crop_x = (scaled_width - target_width) // 2
        
        return (crop_x, 0, target_width, target_height)

    def create_default_speakers(self, width, height):
        """Create default speaker positions with center focus"""
        # For news/interviews, default to center position
        center_crop = self.calculate_crop_zone(width // 2, height // 2, width, height, "center")
        
        # Single default speaker at center
        default_speakers = [
            Speaker(
                id=0,
                face_box=(width//2 - 100, height//2 - 100, 200, 200),
                center_x=width//2,
                center_y=height//2,
                crop_zone=center_crop
            )
        ]
        
        return default_speakers

    def create_viral_clip_with_speaker_switching(self, video_path, start_time, duration, output_path, speakers):
        """🔥 CREATE VIRAL CLIP WITH EXACT TIMING! 🔥"""
        try:
            print("🔥 CREATING VIRAL CLIP WITH SPEAKER SWITCHING!")
            print(f"📺 Found {len(speakers)} speakers - creating EPIC viral content!")
            
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Calculate segments based on content type
            def calculate_segments(total_duration, speakers_count):
                # For single speaker or news style, use longer segments
                if speakers_count == 1:
                    return [total_duration]  # No cuts for single speaker
                elif speakers_count == 2:
                    # For 2 speakers (interview style), use 5-8 second segments
                    segment_duration = 6.0
                else:
                    # For multiple speakers, use shorter segments
                    segment_duration = 4.0
                
                full_segments = int(total_duration / segment_duration)
                if full_segments == 0:
                    return [total_duration]
                
                remaining_time = total_duration - (full_segments * segment_duration)
                
                if remaining_time <= 1.0:
                    # Distribute evenly across all segments
                    adjusted_duration = total_duration / full_segments
                    return [adjusted_duration] * full_segments
                else:
                    # Add remainder as final segment
                    segments = [segment_duration] * full_segments
                    segments.append(remaining_time)
                    return segments
            
            segment_durations = calculate_segments(duration, len(speakers))
            temp_segments = []
            
            print(f"🎬 Creating {len(segment_durations)} segments with exact timing:")
            print(f"   Segments: {[round(d, 1) for d in segment_durations]} = {sum(segment_durations)}s total")
            
            current_time = 0
            for i, segment_dur in enumerate(segment_durations):
                segment_start_time = start_time + current_time
                
                # For news/interview style, prioritize primary (center) speaker
                if len(speakers) == 1:
                    speaker = speakers[0]
                elif i == 0 or (i % 3 == 0):  # Start with and return to primary speaker
                    speaker = speakers[0]  # Primary speaker (closest to center)
                else:
                    # Occasionally show other speakers
                    speaker_idx = (i // 3) % (len(speakers) - 1) + 1
                    speaker = speakers[min(speaker_idx, len(speakers) - 1)]
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
