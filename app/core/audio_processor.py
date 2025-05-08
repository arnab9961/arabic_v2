import os
import groq
import json
import asyncio
from typing import Dict, Any
import logging

from app.core.config import get_settings

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def process_audio(audio_path: str) -> str:
    """
    Process audio file using Groq's Whisper Large V3 model
    
    Args:
        audio_path: Path to the audio file
        
    Returns:
        str: Transcribed text in Arabic
    """
    settings = get_settings()
    
    # Check if API key is available
    if not settings.GROQ_API_KEY or settings.GROQ_API_KEY == "your_groq_api_key_here":
        logger.error("Groq API key is missing or invalid")
        return "خطأ في معالجة الصوت. الرجاء التحقق من مفتاح API."  # Error processing audio, please check the API key
    
    # Log audio file details
    logger.info(f"Processing audio file: {audio_path}, size: {os.path.getsize(audio_path)} bytes")
    
    # Initialize Groq client with API key
    client = groq.Client(api_key=settings.GROQ_API_KEY)
    
    # Read the audio file
    try:
        with open(audio_path, "rb") as audio_file:
            # Create a transcription request to Groq API using Whisper model
            try:
                logger.info(f"Sending audio to Groq API using model: {settings.WHISPER_MODEL}")
                
                response = await asyncio.to_thread(
                    client.audio.transcriptions.create,
                    model=settings.WHISPER_MODEL,
                    file=audio_file,
                    language="ar",  # Arabic language
                    response_format="json"
                )
                
                # Extract the transcribed text
                if hasattr(response, 'text'):
                    logger.info(f"Successfully transcribed audio")
                    return response.text
                elif isinstance(response, dict) and 'text' in response:
                    logger.info(f"Successfully transcribed audio")
                    return response['text']
                else:
                    logger.warning(f"Unexpected response format: {type(response)}")
                    return json.dumps(response)
                    
            except Exception as e:
                # Log the error and raise it again
                logger.error(f"Error processing audio with Groq API: {str(e)}")
                if "401" in str(e):
                    return "خطأ في التوثيق: الرجاء التحقق من مفتاح API."  # Authentication error: please check API key
                raise e
    except Exception as file_error:
        logger.error(f"Error reading audio file: {str(file_error)}")
        raise file_error