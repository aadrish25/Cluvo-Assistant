import httpx
import os
import asyncio
from sarvamai import AsyncSarvamAI,SarvamAI
from backend.config import SARVAM_API_KEY,SARVAM_STT_ENDPOINT,SARVAM_TTS_ENDPOINT
from dotenv import load_dotenv

load_dotenv()


class SarvamTranslationLayer:
    def __init__(self):
        self.sarvam_client = AsyncSarvamAI(
            api_subscription_key=SARVAM_API_KEY,
            follow_redirects=True
        )
        
        self.stt_endpoint = SARVAM_STT_ENDPOINT
        self.tts_endpoint = SARVAM_TTS_ENDPOINT
        self.headers = {"api-subscription-key":SARVAM_API_KEY}
        
        
    async def translate_text(self,text:str,target_lang:str,source_lang:str = "auto"):
        try:
            response = await self.sarvam_client.text.translate(
                input=text,
                source_language_code=source_lang,
                target_language_code=target_lang,
                speaker_gender="Male",
                model="mayura:v1",
            )
            
            print(f"[SARVAM] Translated text: {response.translated_text}")
            
            return {
            "translated_text": response.translated_text,
            "source_language_code": response.source_language_code,
        }
        
        except Exception as e:
            print(f"[SARVAM] Error in text translation: {e}")
            
            
    async def speech_to_text_translate(self,audio_bytes:bytes,filename:str = "audio.webm"):
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(
                    url=str(self.stt_endpoint),
                    headers=self.headers,
                    files= {"file":(filename,audio_bytes,"audio/webm")},
                    data={
                        "model":"saaras:v3",
                        "mode":"translate",
                    }
                )
                
                print(f"[SARVAM] Speech to text translate: {response.content}")
                
                response.raise_for_status()
                return response.json()
        
        except Exception as e:
            print(f"[SARVAM] Error in speech to text conversion: {e}")
            
    
    async def synthesize_speech(self,text:str,target_lang:str,speaker:str):
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(
                    url=self.tts_endpoint,
                    headers={**self.headers,"Content-Type":"application/json"},
                    json={
                        "text":text,
                        "target_language_code":target_lang,
                        "speaker":speaker,
                        "model":"bulbul:v3",
                    }
                )
                
                print(f"[SARVAM] Speech synthesis status code: {response.status_code}")
                
                response.raise_for_status()
                
                return response.json()
        except Exception as e:
            print(f"[SARVAM] Error in text to speech conversion: {e}")
                
        
        
async def main():
    translation = SarvamTranslationLayer()
    response = await translation.translate_text(text="Amar nam Aadrish.",target_lang="bn-IN")
    print(response)
                
                
                
if __name__ == "__main__":
    asyncio.run(main())