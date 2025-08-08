#!/usr/bin/env python3
"""
AI Audio Vision Lab - Simple Demo
Copyright (c) 2025 Antonio Mainenti

This demo showcases the AI Audio Vision Lab concept using pre-recorded samples.
Core algorithms and real-time processing are proprietary and not included.

For full system access or commercial licensing:
Email: oggettosonoro@gmail.com
"""

import time
import random
import json
from pathlib import Path
from typing import Dict, List, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ObjectToMusicDemo:
    """
    Simplified demo of AI Audio Vision Lab functionality.
    
    This class demonstrates the concept using pre-recorded audio samples
    and simulated object detection. The actual implementation uses:
    - PyTorch object detection models
    - Proprietary semantic-to-musical mapping algorithms
    - Real-time Magenta music generation with TensorFlow Lite
    """
    
    def __init__(self, demo_assets_path: str = "demo/assets"):
        """
        Initialize the demo with pre-recorded assets.
        
        Args:
            demo_assets_path: Path to demo assets directory
        """
        self.assets_path = Path(demo_assets_path)
        self.available_objects = self._load_available_objects()
        self.music_mappings = self._load_music_mappings()
        logger.info(f"Demo initialized with {len(self.available_objects)} object types")
    
    def _load_available_objects(self) -> List[str]:
        """Load list of objects that can be 'detected' in demo mode."""
        return [
            "plant", "book", "cup", "laptop", "guitar", 
            "phone", "bottle", "clock", "lamp", "camera"
        ]
    
    def _load_music_mappings(self) -> Dict[str, Dict]:
        """
        Load predefined object-to-music mappings for demo.
        
        In the real system, this comes from the proprietary
        semantic-musical correlation algorithm.
        """
        return {
            "plant": {
                "style": "Ambient",
                "tempo": 72,
                "key": "C Major",
                "instruments": ["Pad Synth", "Soft Strings"],
                "mood": "Peaceful, Natural",
                "sample_file": "plant_ambient.mp3"
            },
            "book": {
                "style": "Neoclassical",
                "tempo": 60,
                "key": "A Minor",
                "instruments": ["Piano", "String Quartet"],
                "mood": "Contemplative, Intellectual",
                "sample_file": "book_classical.mp3"
            },
            "cup": {
                "style": "Jazz",
                "tempo": 95,
                "key": "F Major",
                "instruments": ["Piano", "Upright Bass", "Brush Drums"],
                "mood": "Cozy, Intimate",
                "sample_file": "cup_jazz.mp3"
            },
            "laptop": {
                "style": "Electronic",
                "tempo": 128,
                "key": "D Minor",
                "instruments": ["Synthesizer", "Digital Drums"],
                "mood": "Modern, Focused",
                "sample_file": "laptop_electronic.mp3"
            },
            "guitar": {
                "style": "Folk",
                "tempo": 85,
                "key": "G Major",
                "instruments": ["Acoustic Guitar", "Light Percussion"],
                "mood": "Warm, Nostalgic",
                "sample_file": "guitar_folk.mp3"
            }
        }
    
    def simulate_object_detection(self) -> str:
        """
        Simulate object detection by randomly selecting an available object.
        
        In the real system, this uses PyTorch models optimized for Raspberry Pi.
        
        Returns:
            str: Detected object name
        """
        detected_object = random.choice(self.available_objects)
        
        # Simulate processing time
        processing_time = random.uniform(0.1, 0.3)
        time.sleep(processing_time)
        
        logger.info(f"🔍 Object detected: {detected_object} (confidence: {random.uniform(0.85, 0.99):.2f})")
        return detected_object
    
    def generate_music_params(self, detected_object: str) -> Dict:
        """
        Generate musical parameters from detected object.
        
        This demonstrates the interface of the proprietary semantic mapping engine.
        The actual algorithm considers object semantics, emotional associations,
        and contextual factors for coherent music generation.
        
        Args:
            detected_object: Object detected by vision system
            
        Returns:
            Dict: Musical parameters for generation
        """
        if detected_object in self.music_mappings:
            params = self.music_mappings[detected_object].copy()
        else:
            # Fallback for unknown objects
            params = {
                "style": "Ambient",
                "tempo": 80,
                "key": "C Major",
                "instruments": ["Synth Pad"],
                "mood": "Neutral",
                "sample_file": "default_ambient.mp3"
            }
        
        # Simulate processing time for semantic analysis
        time.sleep(0.2)
        
        logger.info(f"🎵 Musical mapping: {params['style']} in {params['key']} at {params['tempo']} BPM")
        return params
    
    def simulate_audio_generation(self, music_params: Dict) -> str:
        """
        Simulate real-time audio generation.
        
        The actual system uses quantized Magenta models running on TensorFlow Lite
        for offline music generation with <2 second latency.
        
        Args:
            music_params: Musical parameters from semantic mapping
            
        Returns:
            str: Path to generated audio file (simulated)
        """
        # Simulate generation latency
        generation_time = random.uniform(1.2, 1.8)
        
        print(f"🎼 Generating {music_params['style']} music...")
        print(f"   Instruments: {', '.join(music_params['instruments'])}")
        print(f"   Mood: {music_params['mood']}")
        
        # Simulate processing with progress
        for i in range(3):
            time.sleep(generation_time / 3)
            print(f"   {'█' * (i + 1)}{'░' * (2 - i)} {((i + 1) * 33):2d}%")
        
        audio_file = self.assets_path / "generated_music" / music_params["sample_file"]
        logger.info(f"🔊 Audio generated: {audio_file}")
        
        return str(audio_file)
    
    def play_audio_sample(self, audio_file: str) -> None:
        """
        Simulate audio playback.
        
        In the real system, this streams directly to Raspberry Pi audio output.
        """
        print(f"🎧 Playing: {Path(audio_file).name}")
        print("   [♪♫♪♫♪♫♪♫♪♫] Audio playing... (simulated)")
        
        # Simulate playback time
        time.sleep(2)
        print("   ✓ Playback complete")
    
    def run_single_detection(self) -> None:
        """Run a single object detection → music generation cycle."""
        print("\n" + "="*60)
        print("🎛️  AI AUDIO VISION LAB - Single Detection Demo")
        print("="*60)
        
        # Step 1: Object Detection
        print("\n🔍 Step 1: Object Detection")
        detected_object = self.simulate_object_detection()
        
        # Step 2: Semantic Mapping
        print(f"\n🧠 Step 2: Semantic-Musical Mapping")
        music_params = self.generate_music_params(detected_object)
        
        # Step 3: Music Generation
        print(f"\n🎵 Step 3: Real-time Music Generation")
        audio_file = self.simulate_audio_generation(music_params)
        
        # Step 4: Audio Playback
        print(f"\n🔊 Step 4: Audio Output")
        self.play_audio_sample(audio_file)
        
        print(f"\n✨ Demo cycle complete! Object '{detected_object}' → {music_params['style']} music")
    
    def run_continuous_demo(self, cycles: int = 5, delay: float = 3.0) -> None:
        """
        Run continuous detection demo simulating real-time operation.
        
        Args:
            cycles: Number of detection cycles to run
            delay: Delay between cycles (seconds)
        """
        print("\n" + "="*60)
        print("🎛️  AI AUDIO VISION LAB - Continuous Demo")
        print(f"Running {cycles} detection cycles with {delay}s intervals")
        print("="*60)
        
        for i in range(cycles):
            print(f"\n🔄 Cycle {i + 1}/{cycles}")
            print("-" * 40)
            
            # Simplified continuous flow
            detected_object = self.simulate_object_detection()
            music_params = self.generate_music_params(detected_object)
            
            print(f"🎼 Now playing: {music_params['style']} ({music_params['mood']})")
            print(f"🎹 {', '.join(music_params['instruments'])}")
            
            # Show transition effect
            if i < cycles - 1:
                print(f"⏳ Waiting {delay}s for next detection...")
                time.sleep(delay)
            
        print(f"\n✅ Continuous demo completed!")
    
    def show_system_info(self) -> None:
        """Display system information and capabilities."""
        print("\n" + "="*60)
        print("📊 AI AUDIO VISION LAB - System Information")
        print("="*60)
        
        info = {
            "Version": "Demo v1.0",
            "Platform": "Cross-platform (Optimized for Raspberry Pi 4)",
            "Object Detection": "PyTorch MobileNet V2 (Quantized)",
            "Music Generation": "Google Magenta → TensorFlow Lite",
            "Audio Processing": "Real-time MIDI synthesis",
            "Latency": "< 2 seconds (detection → audio)",
            "Supported Objects": len(self.available_objects),
            "Music Styles": len(set(m["style"] for m in self.music_mappings.values()))
        }
        
        for key, value in info.items():
            print(f"{key:20} : {value}")
        
        print("\n🎯 Available Object Categories:")
        for obj in sorted(self.available_objects):
            style = self.music_mappings.get(obj, {}).get("style", "Default")
            print(f"   • {obj:12} → {style}")
        
        print(f"\n📧 Contact: oggettosonoro@gmail.com")
        print(f"🐙 GitHub: https://github.com/ninuxi/ai-audio-vision-lab")

def main():
    """Main demo function with interactive menu."""
    demo = ObjectToMusicDemo()
    
    while True:
        print("\n" + "="*60)
        print("🎛️  AI AUDIO VISION LAB - Demo Menu")
        print("="*60)
        print("1. 🎯 Single Object Detection Demo")
        print("2. 🔄 Continuous Detection Demo (5 cycles)")
        print("3. 📊 System Information")
        print("4. 🚪 Exit Demo")
        
        try:
            choice = input("\nSelect option (1-4): ").strip()
            
            if choice == "1":
                demo.run_single_detection()
            elif choice == "2":
                demo.run_continuous_demo()
            elif choice == "3":
                demo.show_system_info()
            elif choice == "4":
                print("\n👋 Thank you for trying AI Audio Vision Lab!")
                print("📧 For collaborations: oggettosonoro@gmail.com")
                break
            else:
                print("❌ Invalid option. Please select 1-4.")
                
        except KeyboardInterrupt:
            print("\n\n👋 Demo interrupted. Goodbye!")
            break
        except Exception as e:
            logger.error(f"Demo error: {e}")
            print("❌ An error occurred. Please try again.")

if __name__ == "__main__":
    print("🎛️ AI Audio Vision Lab - Simple Demo")
    print("This is a demonstration version using pre-recorded samples.")
    print("The full system runs real-time on Raspberry Pi 4.\n")
    
    main()