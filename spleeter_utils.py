import os
import traceback
from spleeter.separator import Separator
from spleeter.audio.adapter import AudioAdapter
import subprocess
import logging

# Configure logging
logging.basicConfig(filename='spleeter_debug.log', level=logging.DEBUG, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

def separate_music(input_path, output_dir, stems=2):
    """
    Separate audio file into stems with robust path handling
    """
    try:
        # Sanitize paths
        input_path = os.path.normpath(input_path)
        output_dir = os.path.normpath(output_dir)
        
        # Validate input file exists
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"Input file not found: {input_path}")
        
        logging.info(f"Starting separation: {input_path}")
        logging.info(f"Output directory: {output_dir}")
        logging.info(f"Stems: {stems}")
        
        # Create output directory if missing
        os.makedirs(output_dir, exist_ok=True)
        logging.info(f"Created output dir: {output_dir}")
        
        # Test write permissions
        test_file = os.path.join(output_dir, "write_test.tmp")
        with open(test_file, 'w') as f:
            f.write("test")
        os.remove(test_file)
        logging.info("Write test successful")

        # Initialize separator
        separator = Separator(f'spleeter:{stems}stems')
        audio_loader = AudioAdapter.default()
        sample_rate = 44100
        
        # Load audio
        logging.info("Loading audio...")
        waveform, _ = audio_loader.load(input_path, sample_rate=sample_rate)
        logging.info(f"Audio loaded, shape: {waveform.shape}")
        
        # Perform separation
        logging.info("Separating audio...")
        prediction = separator.separate(waveform)
        logging.info("Separation complete")
        
        # Save each instrument
        for instrument, data in prediction.items():
            output_path = os.path.join(output_dir, f"{instrument}.wav")
            logging.info(f"Saving: {output_path}")
            audio_loader.save(output_path, data, sample_rate, 'wav')
        
        logging.info("Separation successful")
        return True
        
    except Exception as e:
        error_msg = f"Separation failed: {str(e)}"
        logging.error(error_msg)
        logging.error(traceback.format_exc())
        
        # FFmpeg check
        try:
            result = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True)
            logging.info(f"FFmpeg version: {result.stdout.splitlines()[0] if result.stdout else 'No output'}")
        except Exception as ffmpeg_err:
            logging.error(f"FFmpeg check failed: {str(ffmpeg_err)}")
        
        raise RuntimeError(error_msg)