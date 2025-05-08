from fastapi import APIRouter, Request, File, UploadFile, Form, Depends, HTTPException, BackgroundTasks
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
import os
import tempfile
import json
import logging
import subprocess
import shutil
from typing import Optional, List, Dict

from app.core.audio_processor import process_audio
from app.core.text_comparator import compare_text
from app.core.config import get_settings

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Render the main application page"""
    return templates.TemplateResponse("index.html", {"request": request})

@router.get("/api/surahs")
async def get_surahs():
    """Get list of all surahs from index.json"""
    try:
        index_path = os.path.join("app", "static", "index.json")
        with open(index_path, 'r', encoding='utf-8') as f:
            surah_index = json.load(f)
        return surah_index
    except Exception as e:
        logger.error(f"Error loading surah index: {str(e)}")
        raise HTTPException(status_code=500, detail="Error loading surah index")

@router.post("/api/assess")
async def assess_pronunciation(
    request: Request,
    audio_file: UploadFile = File(...),
    surah_number: str = Form(...)
):
    """
    Process audio file and assess pronunciation accuracy for a whole surah
    
    Args:
        audio_file: User's audio recording of Quranic recitation
        surah_number: The chapter number (surah) being recited
    """
    try:
        logger.info(f"Received assessment request - Surah: {surah_number}")
        logger.info(f"Audio file: {audio_file.filename}, Content type: {audio_file.content_type}")
        
        # Create temp directory to work with audio files
        with tempfile.TemporaryDirectory() as temp_dir:
            # Save the uploaded audio file temporarily
            temp_input_path = os.path.join(temp_dir, f"input{os.path.splitext(audio_file.filename)[1] or '.webm'}")
            temp_wav_path = os.path.join(temp_dir, "converted.wav")
            
            with open(temp_input_path, "wb") as f:
                f.write(await audio_file.read())
            
            logger.info(f"Saved uploaded file to {temp_input_path} ({os.path.getsize(temp_input_path)} bytes)")
            
            # Try multiple FFmpeg strategies for audio conversion
            ffmpeg_success = await try_multiple_ffmpeg_strategies(temp_input_path, temp_wav_path)
            
            if not ffmpeg_success:
                return JSONResponse(
                    status_code=500,
                    content={"error": "Failed to process audio file. Please try a different recording format."}
                )
            
            # Process audio to get transcribed text using Groq's Whisper
            logger.info(f"Processing audio with Whisper model")
            transcribed_text = await process_audio(temp_wav_path)
            
            if not transcribed_text or transcribed_text.startswith("خطأ"):
                logger.warning(f"Audio processing error or empty transcription: {transcribed_text}")
                return JSONResponse(
                    status_code=200,
                    content={
                        "transcribed_text": transcribed_text or "لم يتم التعرف على أي كلام",  # No speech recognized
                        "correct_text": "",
                        "assessment": {
                            "accuracy_score": 0,
                            "mispronounced_words": [],
                            "missing_words": [],
                            "additional_words": [],
                            "feedback": {
                                "arabic": "لم يتمكن النظام من التعرف على الكلام.",
                                "english": "The system could not recognize any speech."
                            }
                        }
                    }
                )
        
        # Get the correct text from our Quran text database
        settings = get_settings()
        
        try:
            # Load Quran text data
            quran_data_path = os.path.join("app", "static", "quran_data.json")
            logger.info(f"Loading Quran data from {quran_data_path}")
            
            with open(quran_data_path, 'r', encoding='utf-8') as f:
                quran_data = json.load(f)
            
            # Extract the entire surah
            surah_idx = str(int(surah_number))  # Convert to ensure valid format
            
            if surah_idx not in quran_data:
                logger.error(f"Invalid surah number: {surah_idx}")
                raise HTTPException(status_code=400, detail="Invalid surah number")
            
            surah = quran_data[surah_idx]
            
            # Combine all verses into one text
            combined_text = " ".join([verse["text"] for verse in surah["verses"]])
            
            # Compare transcribed text with correct text using Groq's Llama3
            logger.info(f"Comparing transcribed text with complete Surah text using Llama3-70b")
            assessment_results = await compare_text(transcribed_text, combined_text)
            
            logger.info(f"Assessment completed - Accuracy: {assessment_results.get('accuracy_score')}%")
            
            return {
                "transcribed_text": transcribed_text,
                "correct_text": combined_text,
                "assessment": assessment_results
            }
        
        except Exception as quran_error:
            logger.error(f"Error accessing Quran data: {str(quran_error)}")
            raise quran_error
    
    except Exception as e:
        logger.error(f"Uncaught exception in assessment endpoint: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": f"An error occurred during processing: {str(e)}"}
        )

async def try_multiple_ffmpeg_strategies(input_path: str, output_path: str) -> bool:
    """Try multiple FFmpeg strategies to convert audio file to WAV format"""
    
    ffmpeg_strategies = [
        # Strategy 1: Standard conversion with explicit sample rate and mono audio
        ["ffmpeg", "-i", input_path, "-ar", "16000", "-ac", "1", "-c:a", "pcm_s16le", output_path],
        
        # Strategy 2: Try with aformat filter for more explicit format control
        ["ffmpeg", "-i", input_path, "-af", "aformat=sample_fmts=s16:sample_rates=16000:channel_layouts=mono", 
         "-c:a", "pcm_s16le", output_path],
        
        # Strategy 3: Try forcing format with -f wav
        ["ffmpeg", "-i", input_path, "-ar", "16000", "-ac", "1", "-f", "wav", output_path],
        
        # Strategy 4: Try with libvorbis intermediate conversion for difficult formats
        ["ffmpeg", "-i", input_path, "-c:a", "libvorbis", "-ar", "16000", "-ac", "1", 
         "-f", "wav", "-c:a", "pcm_s16le", output_path],
         
        # Strategy 5: Try with volume normalization for very quiet audio
        ["ffmpeg", "-i", input_path, "-af", "loudnorm=I=-16:LRA=11:TP=-1.5", 
         "-ar", "16000", "-ac", "1", "-c:a", "pcm_s16le", output_path]
    ]
    
    for i, strategy in enumerate(ffmpeg_strategies):
        try:
            logger.info(f"Trying FFmpeg conversion strategy {i+1}/{len(ffmpeg_strategies)}")
            process = subprocess.run(
                strategy,
                capture_output=True,
                text=True
            )
            
            if process.returncode == 0 and os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                logger.info(f"FFmpeg strategy {i+1} succeeded - output size: {os.path.getsize(output_path)} bytes")
                return True
            else:
                logger.warning(f"FFmpeg strategy {i+1} failed: {process.stderr}")
        except Exception as e:
            logger.error(f"Error with FFmpeg strategy {i+1}: {str(e)}")
    
    logger.error("All FFmpeg strategies failed")
    return False