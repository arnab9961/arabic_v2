import os
import json
import logging
import asyncio
from typing import Dict, List, Any
import groq

from app.core.config import get_settings

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def compare_text(transcribed_text: str, correct_text: str) -> Dict[str, Any]:
    """
    Compare transcribed text with correct text using Groq's Llama3-70b-8192 model
    
    Args:
        transcribed_text: The transcribed text from audio
        correct_text: The correct Quranic text
        
    Returns:
        Dict: Assessment results including errors and accuracy score
    """
    settings = get_settings()
    
    # Check if API key is available
    if not settings.GROQ_API_KEY or settings.GROQ_API_KEY == "your_groq_api_key_here":
        logger.error("Groq API key is missing or invalid")
        raise ValueError("Groq API key is required for pronunciation assessment")

    # Initialize Groq client with API key
    client = groq.Client(api_key=settings.GROQ_API_KEY)
    
    try:
        # Create prompt for Llama3
        prompt = f"""
        You are an Arabic pronunciation expert specialized in Quranic recitation. Compare the transcribed text with the correct text and identify any mispronunciations, errors, or omissions.
        
        Correct Quranic Text: {correct_text}
        Transcribed User Speech: {transcribed_text}
        
        Provide a detailed analysis in JSON format with the following structure exactly:
        {{
            "accuracy_score": <number between 0 and 100>,
            "mispronounced_words": [
                {{
                    "transcribed": "<mispronounced word>",
                    "correct": "<correct word>"
                }},
                ...
            ],
            "missing_words": ["<word1>", "<word2>", ...],
            "additional_words": ["<word1>", "<word2>", ...],
            "feedback": {{
                "arabic": "<feedback in Arabic>",
                "english": "<feedback in English>"
            }}
        }}
        """
        
        # Generate response using Groq's Llama3-70b-8192
        logger.info("Generating pronunciation assessment with Groq's Llama3-70b-8192")
        
        response = await asyncio.to_thread(
            client.chat.completions.create,
            model="llama3-70b-8192",
            messages=[
                {"role": "system", "content": "You are an Arabic pronunciation expert specializing in Quranic recitation analysis."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=1024,
            response_format={"type": "json_object"}
        )
        
        # Extract the response text
        result_text = response.choices[0].message.content
        
        # Parse the JSON response
        try:
            result = json.loads(result_text)
            
            # Validate required fields
            required_fields = ["accuracy_score", "mispronounced_words", "feedback"]
            for field in required_fields:
                if field not in result:
                    logger.warning(f"Required field '{field}' missing from response")
                    result[field] = [] if field != "accuracy_score" else estimate_accuracy(transcribed_text, correct_text)
                    
            if "feedback" in result and isinstance(result["feedback"], dict):
                if "arabic" not in result["feedback"]:
                    result["feedback"]["arabic"] = ""
                if "english" not in result["feedback"]:
                    result["feedback"]["english"] = ""
            else:
                result["feedback"] = {
                    "arabic": "",
                    "english": ""
                }
                
            logger.info(f"Successfully generated assessment with accuracy score: {result.get('accuracy_score')}%")
            
        except (json.JSONDecodeError, ValueError) as json_error:
            logger.error(f"Failed to parse Llama3 response as JSON: {str(json_error)}")
            raise ValueError(f"Failed to parse model response: {str(json_error)}")
            
    except Exception as model_error:
        logger.error(f"Error with Groq Llama3 model: {str(model_error)}")
        raise model_error
    
    return result

def estimate_accuracy(transcribed_text: str, correct_text: str) -> float:
    """Estimate the accuracy score based on simple text comparison"""
    # If either text is empty, handle the edge case
    if not transcribed_text or not correct_text:
        return 0
        
    # Simple character-level comparison
    transcribed_chars = set(transcribed_text)
    correct_chars = set(correct_text)
    
    # Calculate Jaccard similarity
    intersection = len(transcribed_chars.intersection(correct_chars))
    union = len(transcribed_chars.union(correct_chars))
    
    if union == 0:
        return 0
    
    similarity = intersection / union
    return round(similarity * 100, 2)

def find_differences(transcribed_text: str, correct_text: str) -> List[Dict[str, str]]:
    """Find differences between transcribed and correct text"""
    transcribed_words = transcribed_text.split()
    correct_words = correct_text.split()
    
    differences = []
    
    # Simple difference detection
    for i, word in enumerate(transcribed_words):
        if i < len(correct_words) and word != correct_words[i]:
            differences.append({
                "transcribed": word,
                "correct": correct_words[i]
            })
    
    return differences

def find_missing_words(transcribed_text: str, correct_text: str) -> List[str]:
    """Find words that are in the correct text but missing from transcription"""
    transcribed_words = set(transcribed_text.split())
    correct_words = set(correct_text.split())
    
    # Words in correct text but not in transcribed text
    missing = [word for word in correct_words if word not in transcribed_words]
    return missing[:5]  # Limit to top 5 for simplicity

def find_additional_words(transcribed_text: str, correct_text: str) -> List[str]:
    """Find words that are in the transcription but not in correct text"""
    transcribed_words = set(transcribed_text.split())
    correct_words = set(correct_text.split())
    
    # Words in transcribed text but not in correct text
    additional = [word for word in transcribed_words if word not in correct_words]
    return additional[:5]  # Limit to top 5 for simplicity