# To run this code you need to install the following dependencies:
# pip install google-genai youtube-transcript-api fastapi uvicorn

import os
import re
import json
from google import genai
from google.genai import types
from youtube_transcript_api import YouTubeTranscriptApi
from fastapi import FastAPI

app = FastAPI()

# -- Extract YouTube Video ID from URL --
def extract_youtube_id(url):
    if "youtube.com/watch?v=" in url:
        return url.split("v=")[1].split("&")[0]
    elif "youtu.be/" in url:
        return url.split("/")[-1]
    else:
        raise ValueError("Invalid YouTube URL")

# -- Fetch YouTube transcript --
def fetch_youtube_transcript(video_id):
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        return " ".join([entry["text"] for entry in transcript])
    except Exception as e:
        print(f"Error fetching transcript: {e}")
        return None

# -- Analyze with Gemini --
def analyze_with_gemini(transcript_text):
    client = genai.Client(api_key="AIzaSyC-1X30er-HcmwLhAi_Yd7fs9Fc0KwBeg4")  # Secure key usage
    model = "gemini-2.5-pro-exp-03-25"

    prompt = f"""{transcript_text}
    
Based on the above transcription return me a brief summary of the topic in the following JSON format only:
{{
  "topic_name": "name of topic",
  "topic_summary": "summary of topic"
}}"""

    contents = [
        types.Content(role="user", parts=[types.Part.from_text(text=prompt)])
    ]

    response = client.models.generate_content(
        model=model,
        contents=contents,
        config=types.GenerateContentConfig(temperature=0.5),
    )

    return response.text

# -- Clean Gemini string output to dict --
def clean_and_parse_json_response(response_str):
    cleaned = re.sub(r"```json|```", "", response_str).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        print("JSON parsing error:", e)
        return {"error": "Failed to parse Gemini response"}

# -- FastAPI Route --
@app.get("/summarize")
def summarize(url: str):
    try:
        video_id = extract_youtube_id(url)
        transcript = fetch_youtube_transcript(video_id)

        if transcript:
            summary = analyze_with_gemini(transcript)
            return clean_and_parse_json_response(summary)
        else:
            return {"error": "Transcript not found"}
    except Exception as e:
        return {"error": str(e)}
