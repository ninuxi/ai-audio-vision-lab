"""
AI Audio Vision Lab - Audio Generation Interface
Copyright (c) 2025 Antonio Mainenti

Abstract interfaces for the audio generation subsystem.
Defines contracts for music generation, MIDI processing, and audio synthesis.

The actual implementations use proprietary algorithms for semantic-to-musical
mapping and optimized Magenta models converted to TensorFlow Lite.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Union, Callable, Any
from dataclasses import dataclass
from enum import Enum
import numpy as np


class MusicStyle(Enum):
    """Supported music styles for generation."""
    AMBIENT = "ambient"
    CLASSICAL = "classical"
    JAZZ = "jazz"
    ELECTRONIC = "electronic"
    FOLK = "folk"
    ROCK = "rock"
    WORLD = "world"
    EXPERIMENTAL = "experimental"


class InstrumentFamily(Enum):
    """Instrument families for music generation."""
    PIANO = "piano"
    STRINGS = "strings"
    BRASS = "brass"
    WOODWINDS = "woodwinds"
    PERCUSSION = "percussion"
    SYNTHESIZER = "synthesizer"
    GUITAR = "guitar"
    BASS = "bass"


@dataclass
class MusicalKey:
    """Represents a musical key with tonic and mode."""
    tonic: str  # C, D, E, F, G, A, B
    mode: str   # major, minor, dorian, etc.
    
    def __str__(self) -> str:
        return f"{self.tonic} {self.mode.title()}"


@dataclass
class TimeSignature:
    """Represents a time signature."""
    numerator: int    # beats per measure
    denominator: int  # note value for each beat
    
    def __str__(self) -> str:
        return f"{self.numerator}/{self.denominator}"


@dataclass
class MusicalParameters:
    """
    Comprehensive musical parameters for generation.
    
    This structure encapsulates all the musical elements that can be
    controlled during generation, derived from semantic analysis of
    detected objects.
    """
    # Core musical elements
    tempo: int  # BPM
    key: MusicalKey
    time_signature: TimeSignature
    style: MusicStyle
    
    # Instrumentation
    primary_instruments: List[InstrumentFamily]
    secondary_instruments: Optional[List[InstrumentFamily]] = None
    
    # Emotional and semantic properties
    energy_level: float = 0.5      # 0.0 = very calm, 1.0 = very energetic
    complexity: float = 0.5        # 0.0 = simple, 1.0 = complex
    brightness: float = 0.5        # 0.0 = dark, 1.0 = bright
    tension: float = 0.5           # 0.0 = relaxed, 1.0 = tense
    
    # Generation parameters
    duration: float = 30.0         # seconds
    fade_in: float = 2.0          # seconds
    fade_out: float = 2.0         # seconds
    
    # Advanced parameters
    harmonic_richness: float = 0.5  # 0.0 = simple, 1.0 = rich harmonies
    rhythmic_complexity: float = 0.5  # 0.0 = simple, 1.0 = complex rhythms
    melodic_range: str = "medium"   # low, medium, high, wide
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "tempo": self.tempo,
            "key": str(self.key),
            "time_signature": str(self.time_signature),
            "style": self.style.value,
            "primary_instruments": [inst.value for inst in self.primary_instruments],
            "secondary_instruments": [inst.value for inst in self.secondary_instruments] if self.secondary_instruments else [],
            "energy_level": self.energy_level,
            "complexity": self.complexity,
            "brightness": self.brightness,
            "tension": self.tension,
            "duration": self.duration,
            "harmonic_richness": self.harmonic_richness,
            "rhythmic_complexity": self.rhythmic_complexity,
            "melodic_range": self.melodic_range
        }


@dataclass
class GeneratedAudio:
    """Represents generated audio with metadata."""
    audio_data: np.ndarray     # Audio samples
    sample_rate: int           # Sample rate (Hz)
    duration: float            # Duration in seconds
    parameters: MusicalParameters  # Generation parameters used
    midi_data: Optional[bytes] = None  # Optional MIDI representation
    generation_time: Optional[float] = None  # Time taken to generate
    
    @property
    def num_samples(self) -> int:
        """Number of audio samples."""
        return len(self.audio_data)
    
    @property
    def channels(self) -> int:
        """Number of audio channels."""
        return 1 if self.audio_data.ndim == 1 else self.audio_data.shape[1]


class MusicGeneratorInterface(ABC):
    """
    Abstract interface for music generation systems.
    
    This interface defines the contract for AI music generation,
    supporting both real-time and batch generation modes.
    """
    
    @abstractmethod
    def initialize(self, config: Dict) -> bool:
        """
        Initialize the music generator with configuration.
        
        Args:
            config: Configuration dictionary containing model paths,
                   generation settings, and optimization parameters
        
        Returns:
            bool: True if initialization successful
        """
        pass
    
    @abstractmethod
    def generate_music(self, parameters: MusicalParameters) -> GeneratedAudio:
        """
        Generate music based on musical parameters.
        
        Args:
            parameters: Musical parameters defining the desired output
        
        Returns:
            Generated audio with metadata
        """
        pass
    
    @abstractmethod
    def generate_transition(self, from_params: MusicalParameters,
                          to_params: MusicalParameters,
                          transition_duration: float = 4.0) -> GeneratedAudio:
        """
        Generate smooth transition between two musical states.
        
        Args:
            from_params: Current musical parameters
            to_params: Target musical parameters
            transition_duration: Duration of transition in seconds
        
        Returns:
            Generated transition audio
        """
        pass
    
    @abstractmethod
    def get_supported_styles(self) -> List[MusicStyle]:
        """
        Get list of supported music styles.
        
        Returns:
            List of supported music styles
        """
        pass
    
    @abstractmethod
    def get_supported_instruments(self) -> List[InstrumentFamily]:
        """
        Get list of supported instrument families.
        
        Returns:
            List of supported instrument families
        """
        pass
    
    @abstractmethod
    def estimate_generation_time(self, parameters: MusicalParameters) -> float:
        """
        Estimate time required for generation.
        
        Args:
            parameters: Musical parameters for generation
        
        Returns:
            Estimated generation time in seconds
        """
        pass
    
    @abstractmethod
    def cleanup(self) -> None:
        """Clean up resources used by the generator."""
        pass


class SemanticMusicMapperInterface(ABC):
    """
    Interface for mapping semantic features to musical parameters.
    
    This is the core of the AI Audio Vision Lab innovation - the ability
    to translate visual semantic information into coherent musical expressions.
    The actual implementation contains proprietary algorithms based on
    cognitive science research and machine learning.
    """
    
    @abstractmethod
    def map_object_to_music(self, object_name: str,
                          semantic_features: Dict[str, float],
                          context: Optional[Dict] = None) -> MusicalParameters:
        """
        Map object semantic features to musical parameters.
        
        Args:
            object_name: Name of the detected object
            semantic_features: Semantic features extracted from object
            context: Optional contextual information (time, environment, etc.)
        
        Returns:
            Musical parameters for generation
        """
        pass
    
    @abstractmethod
    def update_mapping_weights(self, feedback: Dict[str, float]) -> None:
        """
        Update mapping algorithm weights based on user feedback.
        
        Args:
            feedback: User feedback on generated music quality and relevance
        """
        pass
    
    @abstractmethod
    def get_mapping_explanation(self, object_name: str) -> Dict[str, str]:
        """
        Get human-readable explanation of object-to-music mapping.
        
        Args:
            object_name: Object to explain mapping for
        
        Returns:
            Dictionary explaining the mapping rationale
        """
        pass
    
    @abstractmethod
    def load_custom_mappings(self, mappings_file: str) -> bool:
        """
        Load custom object-to-music mappings.
        
        Args:
            mappings_file: Path to custom mappings configuration
        
        Returns:
            bool: True if mappings loaded successfully
        """
        pass


class AudioSynthesizerInterface(ABC):
    """
    Interface for real-time audio synthesis.
    
    Handles conversion from MIDI/musical parameters to actual audio output,
    optimized for low-latency performance on Raspberry Pi.
    """
    
    @abstractmethod
    def initialize_audio_system(self, config: Dict) -> bool:
        """
        Initialize audio output system.
        
        Args:
            config: Audio system configuration (sample rate, buffer size, etc.)
        
        Returns:
            bool: True if audio system initialized successfully
        """
        pass
    
    @abstractmethod
    def synthesize_midi(self, midi_data: bytes,
                       soundfont: Optional[str] = None) -> np.ndarray:
        """
        Synthesize MIDI data to audio.
        
        Args:
            midi_data: MIDI data to synthesize
            soundfont: Optional custom soundfont file
        
        Returns:
            Synthesized audio as numpy array
        """
        pass
    
    @abstractmethod
    def play_audio(self, audio_data: np.ndarray,
                  sample_rate: int = 44100,
                  blocking: bool = False) -> bool:
        """
        Play audio through system output.
        
        Args:
            audio_data: Audio samples to play
            sample_rate: Sample rate of audio data
            blocking: Whether to block until playback complete
        
        Returns:
            bool: True if playback started successfully
        """
        pass
    
    @abstractmethod
    def stop_playback(self) -> None:
        """Stop current audio playback."""
        pass
    
    @abstractmethod
    def set_volume(self, volume: float) -> None:
        """
        Set output volume.
        
        Args:
            volume: Volume level (0.0 to 1.0)
        """
        pass
    
    @abstractmethod
    def get_audio_devices(self) -> List[Dict]:
        """
        Get available audio output devices.
        
        Returns:
            List of audio device information dictionaries
        """
        pass


class RealTimeMusicProcessorInterface(ABC):
    """
    Interface for real-time music processing pipeline.
    
    Coordinates the entire flow from object detection to audio output,
    managing latency, buffering, and smooth transitions.
    """
    
    @abstractmethod
    def start_processing(self) -> bool:
        """
        Start real-time processing pipeline.
        
        Returns:
            bool: True if processing started successfully
        """
        pass
    
    @abstractmethod
    def stop_processing(self) -> None:
        """Stop real-time processing pipeline."""
        pass
    
    @abstractmethod
    def process_objects(self, detected_objects: List[Dict]) -> None:
        """
        Process newly detected objects and update music generation.
        
        Args:
            detected_objects: List of objects detected in current frame
        """
        pass
    
    @abstractmethod
    def set_transition_mode(self, mode: str) -> None:
        """
        Set transition mode between different musical states.
        
        Args:
            mode: Transition mode ('instant', 'smooth', 'fade', 'crossfade')
        """
        pass
    
    @abstractmethod
    def get_processing_stats(self) -> Dict[str, float]:
        """
        Get real-time processing statistics.
        
        Returns:
            Dictionary with processing metrics (latency, CPU usage, etc.)
        """
        pass
    
    @abstractmethod
    def register_callback(self, event: str, callback: Callable) -> None:
        """
        Register callback for processing events.
        
        Args:
            event: Event name ('object_detected', 'music_generated', etc.)
            callback: Callback function to execute
        """
        pass


# Factory functions
def create_music_generator(generator_type: str, config: Dict) -> MusicGeneratorInterface:
    """
    Factory function for creating music generators.
    
    Args:
        generator_type: Type of generator ('magenta_tflite', 'pytorch', etc.)
        config: Generator configuration
    
    Returns:
        Initialized music generator instance
    """
    raise NotImplementedError("Music generator factory is proprietary")


def create_semantic_mapper(config: Dict) -> SemanticMusicMapperInterface:
    """
    Factory function for creating semantic mappers.
    
    Args:
        config: Mapper configuration
    
    Returns:
        Initialized semantic mapper instance
    """
    raise NotImplementedError("Semantic mapper factory is proprietary")


def create_audio_synthesizer(synth_type: str, config: Dict) -> AudioSynthesizerInterface:
    """
    Factory function for creating audio synthesizers.
    
    Args:
        synth_type: Type of synthesizer ('fluidsynth', 'pygame', etc.)
        config: Synthesizer configuration
    
    Returns:
        Initialized audio synthesizer instance
    """
    raise NotImplementedError("Audio synthesizer factory is proprietary")


# Mock implementations for testing
class MockMusicGenerator(MusicGeneratorInterface):
    """Mock music generator for testing and demonstration."""
    
    def __init__(self):
        self.initialized = False
    
    def initialize(self, config: Dict) -> bool:
        self.initialized = True
        return True
    
    def generate_music(self, parameters: MusicalParameters) -> GeneratedAudio:
        """Generate mock audio data."""
        import time
        
        # Simulate generation time
        time.sleep(min(2.0, parameters.duration * 0.1))
        
        # Generate simple sine wave as placeholder
        sample_rate = 44100
        duration = min(parameters.duration, 10.0)  # Limit for demo
        samples = int(sample_rate * duration)
        
        # Simple sine wave at frequency based on key
        key_frequencies = {
            "C": 261.63, "D": 293.66, "E": 329.63,
            "F": 349.23, "G": 392.00, "A": 440.00, "B": 493.88
        }
        
        freq = key_frequencies.get(parameters.key.tonic, 440.0)
        t = np.linspace(0, duration, samples)
        audio_data = 0.3 * np.sin(2 * np.pi * freq * t)
        
        return GeneratedAudio(
            audio_data=audio_data,
            sample_rate=sample_rate,
            duration=duration,
            parameters=parameters,
            generation_time=time.time()
        )
    
    def generate_transition(self, from_params: MusicalParameters,
                          to_params: MusicalParameters,
                          transition_duration: float = 4.0) -> GeneratedAudio:
        """Generate mock transition."""
        # Simple implementation - just generate audio for to_params
        to_params.duration = transition_duration
        return self.generate_music(to_params)
    
    def get_supported_styles(self) -> List[MusicStyle]:
        return list(MusicStyle)
    
    def get_supported_instruments(self) -> List[InstrumentFamily]:
        return list(InstrumentFamily)
    
    def estimate_generation_time(self, parameters: MusicalParameters) -> float:
        return min(2.0, parameters.duration * 0.1)
    
    def cleanup(self) -> None:
        self.initialized = False


# Export public interface
__all__ = [
    'MusicGeneratorInterface',
    'SemanticMusicMapperInterface',
    'AudioSynthesizerInterface',
    'RealTimeMusicProcessorInterface',
    'MusicalParameters',
    'GeneratedAudio',
    'MusicalKey',
    'TimeSignature',
    'MusicStyle',
    'InstrumentFamily',
    'create_music_generator',
    'create_semantic_mapper',
    'create_audio_synthesizer',
    'MockMusicGenerator'
]