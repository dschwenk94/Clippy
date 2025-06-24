#!/usr/bin/env python3
"""
🎯 AUTO-PEAK VIRAL CLIPPER 🎯
Integrated system that automatically finds optimal viral moments
and creates clips with speaker switching + phrase-by-phrase captions
"""

import os
import json
import ffmpeg
import random
import cv2
import numpy as np
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

# Import our systems
from viral_clipper_complete import ViralClipGenerator as BaseClipGenerator, Speaker
from enhanced_heuristic_peak_detector import EnhancedHeuristicPeakDetector, ViralMoment
from ass_caption_update_system_v6 import ASSCaptionUpdateSystemV6 as ASSCaptionUpdateSystem

@dataclass
class PhraseSegment:
    """Phrase with timing and speaker info"""
    phrase: str
    start_time: float
    end_time: float
    speaker_id: int
    speaker_name: str
    speaker_color: str
    is_viral: bool
    accumulated_text: str

@dataclass
class SpeakerProfile:
    """Speaker profile with visual and caption info"""
    id: int
    name: str
    color: str
    word_count: int
    speaking_time: float
    crop_zone: Optional[Tuple[int, int, int, int]] = None

class AutoPeakViralClipper(BaseClipGenerator):
    """🎯 AUTO-PEAK: Automatically finds optimal moments and creates viral clips"""
    
    def __init__(self, api_key=None, oauth_credentials_file='client_secrets.json'):
        """Initialize the auto-peak viral clipper"""
        super().__init__(api_key, oauth_credentials_file)
        
        # Initialize peak detector
        self.peak_detector = EnhancedHeuristicPeakDetector()
        
        # Initialize ASS caption update system
        self.caption_updater = ASSCaptionUpdateSystem()
        
        # Enhanced color palette
        self.speaker_colors = [
            "#FF4500",   # Matt - Fire Red/Orange
            "#00BFFF",   # Shane - Electric Blue  
            "#00FF88"    # Speaker 3 - Neon Green (if needed)
        ]
        self.speaker_names = ["Speaker 1", "Speaker 2", "Speaker 3"]
        
        # Create configs directory
        self.config_dir = "configs"
        os.makedirs(self.config_dir, exist_ok=True)
        
        print("🎯 AUTO-PEAK VIRAL CLIPPER INITIALIZED")
        print("✅ Automatic peak detection: ENABLED")
        print("✅ Enhanced heuristics: ENABLED")
        print("✅ Speaker switching + captions: ENABLED")
    
    def generate_auto_peak_viral_clip(self, video_url: str, duration: int = 30, manual_start_time: Optional[float] = None):
        """
        🎯 MAIN FUNCTION: Auto-detect optimal moment and create viral clip
        """
        print("🎯 GENERATING AUTO-PEAK VIRAL CLIP!")
        print("🚀 Finding optimal moment + Creating viral clip!")
        print("=" * 80)
        
        # Step 1: Download video
        print("📥 Step 1: Downloading video...")
        video_path, video_title, video_id = self.download_video(video_url)
        if not video_path:
            print("❌ Video download failed")
            return None
        print(f"✅ Video downloaded: {os.path.basename(video_path)}")
        
        # Step 2: Find optimal moment (or use manual override)
        if manual_start_time is not None:
            print(f"\\n🎯 Step 2: Using manual start time: {manual_start_time}s")
            optimal_moment = None
            start_time = manual_start_time
            confidence = 0.5  # Default confidence for manual selection
            
        else:
            print("\\n🎯 Step 2: Auto-detecting optimal viral moment...")
            optimal_moment = self.peak_detector.find_optimal_viral_moment(video_path, duration)
            
            if not optimal_moment:
                print("⚠️  Auto-detection failed, using fallback heuristics...")
                start_time = self.get_fallback_start_time(video_path)
                confidence = 0.3
            else:
                start_time = optimal_moment.timestamp
                confidence = optimal_moment.confidence
                
                print("\\n🎉 OPTIMAL MOMENT DETECTED!")
                print(f"   ⏰ Best timestamp: {start_time:.1f}s ({start_time/60:.1f} min)")
                print(f"   🎯 Confidence: {confidence:.2f}")
                print(f"   💡 Reason: {optimal_moment.reason}")
        
        # Step 3: Detect speakers for video cropping
        print("\\n👥 Step 3: Detecting speakers for video cropping...")
        video_speakers = self.detect_speakers_from_segment(video_path, start_time, duration)
        print(f"✅ Video speakers detected: {len(video_speakers)}")
        
        # Step 4: Get phrase-level transcription
        print("\\n🎤 Step 4: Getting phrase-level transcription...")
        phrase_segments = self.get_phrase_level_transcription_debug(video_path, start_time, duration)
        
        if not phrase_segments:
            print("❌ No phrase segments generated")
            return None
        
        print(f"✅ Phrase segments created: {len(phrase_segments)}")
        
        # Step 5: Create speaker profiles for captions
        print("\\n🔍 Step 5: Creating speaker profiles...")
        caption_speakers = self.create_caption_speaker_profiles_debug(phrase_segments, video_speakers)
        print(f"✅ Caption speakers created: {len(caption_speakers)}")
        
        # Step 6: Assign phrases to speakers
        print("\\n🎯 Step 6: Assigning phrases to speakers...")
        assigned_phrases = self.assign_phrases_to_speakers_debug(phrase_segments, caption_speakers)
        print(f"✅ Phrases assigned: {len(assigned_phrases)}")
        
        # Step 7: Create speaker switching video
        print("\\n🎬 Step 7: Creating speaker switching video...")
        clip_filename = f"auto_peak_clip_{video_id}_{int(start_time)}s.mp4"
        clip_path = os.path.join('clips', clip_filename)
        temp_video_path = clip_path.replace('.mp4', '_temp_switching.mp4')
        
        if len(video_speakers) >= 2:
            print("🎯 Multiple speakers detected - creating dynamic switching video!")
            video_success = self.create_viral_clip_with_speaker_switching(
                video_path, start_time, duration, temp_video_path, video_speakers
            )
        else:
            print("⚠️  Single/no speakers - using smart crop")
            video_success = self.create_smart_single_speaker_clip(
                video_path, start_time, duration, temp_video_path, video_speakers
            )
        
        if not video_success:
            print("❌ Video creation failed")
            return None
        print(f"✅ Base video created: {os.path.basename(temp_video_path)}")
        
        # Step 8: Generate phrase-by-phrase captions
        print("\\n📝 Step 8: Generating phrase-by-phrase captions...")
        subtitle_path = clip_path.replace('.mp4', '_captions.ass')
        
        subtitle_success = self.generate_fixed_phrase_by_phrase_ass_file(
            assigned_phrases, caption_speakers, subtitle_path
        )
        
        if not subtitle_success:
            print("❌ Subtitle generation failed - using video without captions")
            if os.path.exists(temp_video_path):
                os.rename(temp_video_path, clip_path)
            captions_added = False
        else:
            print(f"✅ Subtitle file created: {os.path.basename(subtitle_path)}")
            
            # Step 9: Burn in captions
            print("\\n🔥 Step 9: Burning in captions with FIXED system...")
            caption_success = self.burn_captions_into_video_debug(temp_video_path, subtitle_path, clip_path)
            
            if not caption_success:
                print("❌ Caption burning failed - using video without captions")
                if os.path.exists(temp_video_path):
                    os.rename(temp_video_path, clip_path)
                captions_added = False
            else:
                print("✅ Captions burned into video successfully!")
                # Keep a backup of the video without captions for future updates
                no_caption_backup = temp_video_path.replace('_temp_switching.mp4', '_no_captions.mp4')
                if os.path.exists(temp_video_path) and not os.path.exists(no_caption_backup):
                    import shutil
                    shutil.copy2(temp_video_path, no_caption_backup)
                    print(f"💾 Saved backup without captions: {os.path.basename(no_caption_backup)}")
                
                # Clean up temp video
                if os.path.exists(temp_video_path) and temp_video_path != no_caption_backup:
                    os.remove(temp_video_path)
                captions_added = True
        
        # Step 10: Report results
        if os.path.exists(clip_path):
            file_size = os.path.getsize(clip_path) / (1024*1024)
            
            print("\\n🎉 AUTO-PEAK VIRAL CLIP CREATED!")
            print(f"✅ Output: {clip_path} ({file_size:.1f} MB)")
            print(f"📊 AUTO-PEAK STATS:")
            print(f"   ⏰ Optimal timestamp: {start_time:.1f}s ({start_time/60:.1f} min)")
            print(f"   🎯 Detection confidence: {confidence:.2f}")
            print(f"   ⏱️  Duration: {duration}s")
            print(f"   👥 Video speakers: {len(video_speakers)} (for cropping)")
            print(f"   💬 Caption speakers: {len(caption_speakers)} (for captions)")
            print(f"   📝 Phrase segments: {len(assigned_phrases)}")
            print(f"   🔄 Speaker switching: {len(video_speakers) >= 2}")
            print(f"   🎨 Captions added: {captions_added}")
            
            if optimal_moment:
                print(f"   🔥 Detection signals: {', '.join(optimal_moment.signals[:3])}")
                print(f"   💡 Peak reason: {optimal_moment.reason[:60]}...")
            
            return {
                'path': clip_path,
                'video_id': video_id,
                'original_title': video_title,
                'optimal_timestamp': start_time,
                'detection_confidence': confidence,
                'duration': duration,
                'video_speakers': len(video_speakers),
                'caption_speakers': len(caption_speakers),
                'speaker_switching': len(video_speakers) >= 2,
                'phrase_segments': len(assigned_phrases),
                'captions_added': captions_added,
                'subtitle_file': subtitle_path if captions_added else None,
                'file_size_mb': file_size,
                'created_at': datetime.now().isoformat(),
                'auto_detected': manual_start_time is None,
                'peak_signals': optimal_moment.signals if optimal_moment else [],
                'peak_reason': optimal_moment.reason if optimal_moment else "Manual selection"
            }
        else:
            print("❌ Output file not created")
            return None
    
    def get_fallback_start_time(self, video_path: str) -> float:
        """Get fallback start time if auto-detection fails"""
        try:
            # Get video duration
            probe = ffmpeg.probe(video_path)
            duration = float(probe['format']['duration'])
            
            # Use simple heuristics
            if duration > 1800:  # 30+ minutes (podcast)
                return 300  # 5 minutes in
            elif duration > 600:  # 10+ minutes
                return 180  # 3 minutes in
            else:  # Short content
                return duration * 0.3  # 30% through
                
        except:
            return 300  # Default fallback
    
    # Include all the caption methods from the working system
    def get_phrase_level_transcription_debug(self, video_path: str, start_time: float, duration: float) -> List[Dict]:
        """Get transcription with debugging"""
        try:
            import whisper
            
            # Extract audio
            audio_filename = f"auto_peak_phrase_{int(start_time)}s_{duration}s.wav"
            audio_path = os.path.join('clips', audio_filename)
            
            (
                ffmpeg
                .input(video_path, ss=start_time, t=duration)
                .output(
                    audio_path,
                    acodec='pcm_s16le',
                    ac=1,
                    ar='16000'
                )
                .overwrite_output()
                .run(quiet=True)
            )
            
            if not os.path.exists(audio_path):
                return []
            
            # Transcribe with word timestamps
            model = whisper.load_model("base")
            result = model.transcribe(audio_path, word_timestamps=True, language='en')
            
            # Convert to phrase segments
            phrase_segments = self.convert_to_phrase_segments(result["segments"])
            
            # Clean up
            if os.path.exists(audio_path):
                os.remove(audio_path)
            
            return phrase_segments
            
        except Exception as e:
            print(f"❌ Phrase-level transcription failed: {e}")
            return []
    
    def convert_to_phrase_segments(self, whisper_segments: List[Dict]) -> List[Dict]:
        """Convert Whisper word segments into readable phrases (2-4 words each)"""
        phrase_segments = []
        
        for segment in whisper_segments:
            if "words" not in segment or not segment["words"]:
                phrase_segments.append({
                    'text': segment["text"].strip(),
                    'start': segment["start"],
                    'end': segment["end"],
                    'segment_start': segment["start"],
                    'segment_end': segment["end"]
                })
                continue
            
            words = segment["words"]
            current_phrase_words = []
            
            for i, word_data in enumerate(words):
                current_phrase_words.append(word_data)
                
                should_break = (
                    len(current_phrase_words) >= 4 or
                    (len(current_phrase_words) >= 2 and self.is_natural_break(word_data["word"])) or
                    i == len(words) - 1
                )
                
                if should_break:
                    phrase_text = "".join(w["word"] for w in current_phrase_words)
                    phrase_start = current_phrase_words[0]["start"]
                    phrase_end = current_phrase_words[-1]["end"]
                    
                    phrase_segments.append({
                        'text': phrase_text.strip(),
                        'start': phrase_start,
                        'end': phrase_end,
                        'segment_start': segment["start"],
                        'segment_end': segment["end"]
                    })
                    
                    current_phrase_words = []
        
        return phrase_segments
    
    def is_natural_break(self, word: str) -> bool:
        """Check if this word is a natural place to break a phrase"""
        word = word.strip()
        return (
            word.endswith((',', '.', '!', '?', ':')) or
            word.lower() in ['and', 'but', 'or', 'so', 'then', 'well', 'yeah', 'ok']
        )
    
    def create_caption_speaker_profiles_debug(self, phrase_segments: List[Dict], video_speakers: List[Speaker]) -> List[SpeakerProfile]:
        """Create speaker profiles"""
        try:
            segment_groups = {}
            for phrase in phrase_segments:
                seg_key = f"{phrase['segment_start']:.2f}-{phrase['segment_end']:.2f}"
                if seg_key not in segment_groups:
                    segment_groups[seg_key] = []
                segment_groups[seg_key].append(phrase)
            
            segments = list(segment_groups.values())
            num_speakers = min(len(self.speaker_names), max(2, len(segments) // 3))
            
            speakers = []
            for i in range(num_speakers):
                speaker = SpeakerProfile(
                    id=i,
                    name=self.speaker_names[i],
                    color=self.speaker_colors[i],
                    word_count=0,
                    speaking_time=0
                )
                speakers.append(speaker)
            
            return speakers
            
        except Exception as e:
            return [SpeakerProfile(0, "Matt", self.speaker_colors[0], 0, 0)]
    
    def assign_phrases_to_speakers_debug(self, phrase_segments: List[Dict], speakers: List[SpeakerProfile]) -> List[PhraseSegment]:
        """Assign phrases to speakers"""
        assigned_phrases = []
        
        segment_groups = {}
        for phrase in phrase_segments:
            seg_key = f"{phrase['segment_start']:.2f}-{phrase['segment_end']:.2f}"
            if seg_key not in segment_groups:
                segment_groups[seg_key] = []
            segment_groups[seg_key].append(phrase)
        
        segments = list(segment_groups.values())
        
        for i, segment_phrases in enumerate(segments):
            main_text = " ".join(p['text'] for p in segment_phrases)
            speaker_id = self.assign_segment_to_speaker_intelligently(main_text, i, len(segments))
            
            speaker = next((s for s in speakers if s.id == speaker_id), speakers[0])
            
            accumulated_text = ""
            
            for phrase in segment_phrases:
                phrase_text = phrase['text'].strip()
                
                if accumulated_text and not phrase_text.startswith((' ', '.', ',', '!', '?', ':')):
                    accumulated_text += " " + phrase_text
                else:
                    accumulated_text += phrase_text
                
                accumulated_text = accumulated_text.strip()
                is_viral = self.has_viral_words(phrase['text'])
                
                phrase_segment = PhraseSegment(
                    phrase=phrase['text'],
                    start_time=phrase['start'],
                    end_time=phrase['end'],
                    speaker_id=speaker.id,
                    speaker_name=speaker.name,
                    speaker_color=speaker.color,
                    is_viral=is_viral,
                    accumulated_text=accumulated_text
                )
                
                assigned_phrases.append(phrase_segment)
        
        return assigned_phrases
    
    def assign_segment_to_speaker_intelligently(self, text: str, segment_index: int, total_segments: int) -> int:
        """Intelligent speaker assignment based on content patterns"""
        text_lower = text.lower()
        
        aggressive_words = ["fucking", "shit", "damn", "crazy", "insane", "ridiculous", "what the hell"]
        if any(word in text_lower for word in aggressive_words):
            return 0  # Matt
        
        if "?" in text or any(text_lower.startswith(start) for start in ["what", "why", "how", "is", "was", "did"]):
            return 0  # Matt
        
        if len(text.split()) > 8:
            return 1  # Shane
        
        if segment_index < total_segments / 2:
            return 1  # Shane
        else:
            return 0  # Matt
    
    def has_viral_words(self, text: str) -> bool:
        """Check if text contains viral words"""
        viral_keywords = [
            'fucking', 'shit', 'damn', 'crazy', 'insane', 'ridiculous',
            'amazing', 'incredible', 'awesome', 'epic', 'legendary'
        ]
        text_lower = text.lower()
        return any(word in text_lower for word in viral_keywords)
    
    def generate_fixed_phrase_by_phrase_ass_file(self, phrase_segments: List[PhraseSegment], speakers: List[SpeakerProfile], output_path: str) -> bool:
        """Generate ASS file with fixed escape sequences"""
        try:
            styles_section = self.generate_dynamic_ass_styles(speakers)
            
            ass_content = f"""[Script Info]
Title: Auto-Peak Viral Captions - Phrase by Phrase
ScriptType: v4.00+

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
{styles_section}

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
            
            current_speaker = None
            speaker_phrases = []
            
            for phrase in phrase_segments:
                if current_speaker != phrase.speaker_name:
                    if speaker_phrases:
                        captions = self.create_fixed_speaker_phrase_captions(speaker_phrases, current_speaker)
                        ass_content += captions
                    
                    speaker_phrases = [phrase]
                    current_speaker = phrase.speaker_name
                else:
                    speaker_phrases.append(phrase)
            
            if speaker_phrases:
                captions = self.create_fixed_speaker_phrase_captions(speaker_phrases, current_speaker)
                ass_content += captions
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(ass_content)
            
            return os.path.exists(output_path)
            
        except Exception as e:
            print(f"❌ Error generating ASS file: {e}")
            return False
    
    def update_captions_ass(self, subtitle_path: str, updated_captions: List[Dict], duration: float = 30.0, 
                          caption_position: str = 'bottom', speaker_colors: Dict = None, end_screen: Dict = None) -> bool:
        """
        🆕 Update ASS captions with edited text and speaker assignments
        Maintains proper speaker colors in pop-out effects and video duration
        """
        try:
            print(f"🔄 Updating ASS captions for {duration:.1f}s video...")
            
            # Update caption system with custom colors if provided
            if speaker_colors:
                for speaker_num, color in speaker_colors.items():
                    speaker_key = f"Speaker {speaker_num}"
                    self.caption_updater.speaker_colors[speaker_key] = color
            
            return self.caption_updater.update_ass_file_with_edits(
                original_ass_path=subtitle_path,
                updated_captions=updated_captions,
                output_path=None,
                video_duration=duration,
                caption_position=caption_position,
                speaker_colors=speaker_colors,
                end_screen=end_screen
            )
        except Exception as e:
            print(f"❌ Error updating ASS captions: {e}")
            return False
    
    def create_fixed_speaker_phrase_captions(self, phrases: List[PhraseSegment], speaker_name: str) -> str:
        """Create phrase captions with NO OVERLAPS - each caption has its own time slot"""
        captions = ""
        
        # Minimum gap between captions to prevent overlap
        MIN_GAP = 0.1
        
        for i, phrase in enumerate(phrases):
            start_time = self.seconds_to_ass_time(phrase.start_time)
            
            # Calculate end time with gap before next caption
            if i + 1 < len(phrases):
                # End just before the next caption starts (with small gap)
                next_start = phrases[i + 1].start_time
                end_seconds = min(phrase.end_time, next_start - MIN_GAP)
            else:
                # Last caption - use actual end time
                end_seconds = phrase.end_time
            
            end_time = self.seconds_to_ass_time(end_seconds)
            
            # Use individual phrase text (not accumulated)
            display_text = phrase.phrase.strip()
            
            if phrase.is_viral:
                display_text = self.format_viral_words_fixed(display_text)
            
            # Pop effect with speaker's color
            speaker_color = phrase.speaker_color
            ass_color = self.hex_to_ass_color(speaker_color)
            pop_effect = r"{\fad(150,100)\t(0,300,\fscx110\fscy110)\t(300,400,\fscx100\fscy100)\c" + ass_color + r"}"
            
            dialogue_line = f"Dialogue: 0,{start_time},{end_time},{speaker_name},,0,0,0,,{pop_effect}{display_text}\n"
            captions += dialogue_line
        
        return captions
    
    def format_viral_words_fixed(self, text: str) -> str:
        """Format viral words with corrected escape sequences"""
        viral_keywords = [
            'fucking', 'shit', 'damn', 'crazy', 'insane', 'ridiculous',
            'amazing', 'incredible', 'awesome', 'epic', 'legendary'
        ]
        
        formatted_text = text
        for word in viral_keywords:
            if word.lower() in text.lower():
                viral_format = "{\\\\c&H0000D7FF&\\\\fs26}" + word.upper() + "{\\\\r}"
                
                import re
                pattern = re.compile(re.escape(word), re.IGNORECASE)
                formatted_text = pattern.sub(viral_format, formatted_text)
        
        return formatted_text
    
    def generate_dynamic_ass_styles(self, speakers: List[SpeakerProfile]) -> str:
        """Generate ASS styles for speakers"""
        styles = []
        
        for speaker in speakers:
            ass_color = self.hex_to_ass_color(speaker.color)
            style_line = f"Style: {speaker.name},Arial Black,20,{ass_color},&H000000FF,&H00000000,&H80000000,1,0,0,0,100,100,0,0,1,3,1,2,30,30,50,1"
            styles.append(style_line)
        
        return "\n".join(styles)
    
    def hex_to_ass_color(self, hex_color: str) -> str:
        """Convert hex color to ASS BGR format"""
        hex_color = hex_color.lstrip('#')
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16) 
        b = int(hex_color[4:6], 16)
        return f"&H00{b:02X}{g:02X}{r:02X}"
    
    def seconds_to_ass_time(self, seconds: float) -> str:
        """Convert seconds to ASS time format"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        centiseconds = int((seconds % 1) * 100)
        return f"{hours}:{minutes:02d}:{secs:02d}.{centiseconds:02d}"
    
    def burn_captions_into_video_debug(self, video_path: str, subtitle_path: str, output_path: str) -> bool:
        """Burn captions into video"""
        try:
            if not os.path.exists(video_path) or not os.path.exists(subtitle_path):
                return False
            
            abs_video_path = os.path.abspath(video_path)
            abs_subtitle_path = os.path.abspath(subtitle_path)
            abs_output_path = os.path.abspath(output_path)
            
            (
                ffmpeg
                .input(abs_video_path)
                .output(
                    abs_output_path,
                    vcodec='libx264',
                    acodec='aac',
                    vf=f"ass={abs_subtitle_path}",
                    **{'b:v': '3M', 'b:a': '128k', 'preset': 'medium', 'crf': '23'}
                )
                .overwrite_output()
                .run(quiet=True)
            )
            
            return os.path.exists(output_path)
            
        except Exception as e:
            print(f"❌ Error burning captions: {e}")
            return False


def main():
    """Test the auto-peak viral clip generator"""
    print("🎯 AUTO-PEAK VIRAL CLIPPER")
    print("Automatic optimal moment detection + viral clip generation")
    print("=" * 80)
    
    VIDEO_URL = "https://www.youtube.com/watch?v=dLCbvgFJphA"
    
    generator = AutoPeakViralClipper()
    
    print("🎬 Testing auto-peak detection...")
    clip_data = generator.generate_auto_peak_viral_clip(
        VIDEO_URL, 
        duration=20  # Short test duration
    )
    
    if clip_data and clip_data.get('captions_added'):
        print("\\n🎉 AUTO-PEAK SUCCESS!")
        print(f"   🎬 Path: {clip_data['path']}")
        print(f"   ⏰ Optimal moment: {clip_data['optimal_timestamp']:.1f}s")
        print(f"   🎯 Confidence: {clip_data['detection_confidence']:.2f}")
        print(f"   💾 Size: {clip_data['file_size_mb']:.1f} MB")
        print(f"   🔄 Auto-detected: {clip_data['auto_detected']}")
        print(f"   🔥 Peak signals: {', '.join(clip_data['peak_signals'][:3])}")
        print(f"   💡 Reason: {clip_data['peak_reason'][:60]}...")
        print("   ✅ CAPTIONS AND SPEAKER SWITCHING WORKING!")
        
    elif clip_data:
        print("\\n⚠️  VIDEO CREATED BUT CAPTIONS FAILED")
        print(f"   🎬 Path: {clip_data['path']}")
        print(f"   ⏰ Optimal moment: {clip_data['optimal_timestamp']:.1f}s")
        
    else:
        print("❌ Auto-peak clip generation failed")
    
    print("\\n🎯 INTEGRATION COMPLETE!")
    print("🚀 You now have:")
    print("   ✅ Automatic optimal moment detection")
    print("   ✅ Speaker switching video")
    print("   ✅ Phrase-by-phrase captions")
    print("   ✅ All as the default behavior!")

if __name__ == "__main__":
    main()
