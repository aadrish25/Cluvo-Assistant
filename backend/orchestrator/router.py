from agno.team import Team,TeamMode
from agno.run.team import RunCompletedEvent,RunContentEvent,ToolCallStartedEvent,RunErrorEvent
from agno.tools.reasoning import ReasoningTools
from agno.db.sqlite import SqliteDb
import sys
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(PROJECT_ROOT))

from backend.orchestrator.llm import gemma4_31b
from backend.orchestrator.prompts.router_prompt import ROUTER_AGENT_SYSTEM_PROMPT
from backend.orchestrator.context import Context
from backend.orchestrator.agents.sql_agent import create_sql_agent
from backend.orchestrator.agents.graph_agent import create_graph_agent
from backend.orchestrator.agents.analytics_agent import create_analytics_agent,AnalyticsResponse
from backend.orchestrator.agents.summary_agent import create_summary_agent
from backend.orchestrator.agents.general_agent import create_general_agent
from backend.services.sarvam import SarvamTranslationLayer
from backend.config import AGENT_STATUS_LABELS,DELEGATE_TOOL_NAMES,DEBUG_MODE
from dataclasses import asdict
from backend.database import memory_db


SENTENCE_END_RE = re.compile(r'(?<=[.!?।])\s+')  # ।  catches Hindi/Devanagari sentence-enders too


class InvestigationTeam:
    def __init__(self):
        self.sql_agent = create_sql_agent()
        self.graph_agent = create_graph_agent()
        self.analytics_agent = create_analytics_agent()
        self.summary_agent = create_summary_agent()
        self.general_agent = create_general_agent()
        self.translation_layer = SarvamTranslationLayer()
        self.sqlite_db = memory_db
        
        
        self._agent_status_labels = AGENT_STATUS_LABELS

        self._delegate_tool_names = DELEGATE_TOOL_NAMES
        
        self.team = Team(
                model = gemma4_31b,
                name = "Crime Investigation Team",
                description = "A team of specialized agents for the KSP Crime Intelligence Platform.",
                system_message = ROUTER_AGENT_SYSTEM_PROMPT,
                mode = TeamMode.coordinate,
                members = [self.sql_agent,self.graph_agent,self.analytics_agent,self.summary_agent,self.general_agent],
                tools=[ReasoningTools(add_instructions=True)],
                session_state=asdict(Context()),
                add_session_state_to_context=True,
                update_memory_on_run=True,
                enable_agentic_memory=True,
                enable_agentic_state=True,
                add_history_to_context=True,
                num_history_runs=5,
                db=self.sqlite_db,
                telemetry=DEBUG_MODE,
                debug_mode=DEBUG_MODE,
            )
            
    
    def _safe_get_session_state(self,session_id:str)->dict:
        try:
            return self.team.get_session_state(session_id=session_id) or {}
        except Exception:
            return {}
    
    def initialize_session(self, user_id: str, session_id: str):
        # Agno only creates the session row on the first arun()/run() call —
        # we can't pre-seed state before that exists, so this is now just
        # a safe check rather than a write.
        return self._safe_get_session_state(session_id)
            
    
    def team_run(self,input:str,user_id:str,session_id:str):
        try:
            
            response = self.team.run(
                input=input,
                user_id=user_id,
                session_id=session_id
            )
            
            # update the session state, if analytics response
            for member_response in response.member_responses:
                print(f"[INVESTIGATOR TEAM] Agent name: {member_response.agent_name}, Response type : {type(member_response.content)}")
                if member_response.agent_name == "Analytics Agent":
                    analytics_output : AnalyticsResponse = member_response.content
                    
                    self.team.update_session_state(
                        session_state_updates={
                            "analysis_type":analytics_output.analysis_type,
                            "analytics_answer":analytics_output.answer,
                            "chart_data":analytics_output.chart.model_dump_json() if analytics_output.chart is not None else None,
                            "map_data":analytics_output.map.model_dump_json() if analytics_output.map is not None else None,
                            "table_data":analytics_output.table,
                        },
                        session_id=session_id
                    )
                    
                # after updating the session state, add the updated session state in the response object as well
                response.session_state = self.team.get_session_state(session_id=session_id)
            
            return response
        
        except Exception as e:
            print(f"[INVESTIGATOR TEAM] Error in generating response: {e}")
            
    
    async def team_run_stream_from_text(self,input:str,user_id:str,session_id:str):
        try:
            session_state = self._safe_get_session_state(session_id=session_id) or {}
            user_lang = session_state.get("user_language")
            
            print(f"[INVESTIGATOR TEAM] User lang detected: {user_lang}")
            
            
            # Pure ASCII input is never native-script Indian-language text — only
            # possibly romanized, which we've already decided not to solve. Skip
            # translation entirely: avoids the exact "English sentence with an
            # Indian-origin name auto-detected as the wrong language" failure,
            # and saves a network call for the common English case.
            if input.isascii():
                # Pure ASCII text is often just a proper noun (a name, a case
                # number) typed in Latin script mid-conversation — it does NOT
                # mean the user switched to English. Keep whatever language this
                # session was already using; only default to English if this is
                # a brand-new session with no established language yet.
                english_input = input
                detected_lang = user_lang or "en-IN"
                # session_state["user_language"] = detected_lang
            else:
                translated_text = await self.translation_layer.translate_text(
                    text=input,
                    source_lang="auto",
                    target_lang="en-IN",
                ) or {}
            
            
                english_input = translated_text.get("translated_text",input)
                    
                if not english_input:
                    yield {"type": "error", "message": "Translation failed. Please try again."}
                    return
                detected_lang = translated_text.get("source_language_code") or user_lang or "en-IN"
                session_state["user_language"] = detected_lang
            
            async for chunk in self._run_pipeline(english_input, detected_lang, user_id, session_id):
                yield chunk
    
        except Exception as e:
            print(f"[INVESTIGATOR TEAM] Error in text translation: {e}")
            yield {"type": "error", "message": "Translation failed. Please try again."}
            
    
    async def team_run_stream_from_audio(self,audio_bytes:bytes,session_id:str,user_id:str,mime_type:str = "audio/webm"):
        try:
            session_state = self._safe_get_session_state(session_id=session_id) or {}
            stt_result = await self.translation_layer.speech_to_text_translate(audio_bytes=audio_bytes)
            english_input = (stt_result or {}).get("transcript","")
            detected_lang = (stt_result or {}).get("language_code","") or "en-IN"
            
            # session_state["user_language"] = detected_lang
            
            print(f"[INVESTIGATION TEAM] Detected lang in this run: {detected_lang}")
            
            if not english_input.strip():
                yield {"type": "error", "message": "Couldn't make out what was said — try again?"}
                return
            
            # A short, ASCII-only utterance (a name, a case number) shouldn't flip
            # the whole conversation's language — same reasoning as the text path.
            # Only trust the freshly-detected language when there's enough real
            # content to judge from; otherwise stick with the session's established
            # language.
            
            user_lang = session_state.get("user_language")
            
            print(f"[INVESTIGATOR TEAM] Until now user has been speaking in lang : {user_lang} ")
            
            word_count = len(english_input.split())
            # Only distrust a short/ambiguous utterance when Sarvam falls back to en-IN
            # specifically — that's the direction we've seen misfire on short names/
            # phrases. A confident detection of any OTHER specific language (Tamil,
            # Kannada, etc.) has real phonetic signal behind it and should be trusted,
            # even for a single word — otherwise the user can never actually switch
            # languages mid-conversation.
            if (
                user_lang
                and user_lang != "en-IN"
                and detected_lang == "en-IN"
                and english_input.isascii()
                and word_count <= 3
            ):
                detected_lang = user_lang
            
            # show the recorded output in the frontend-> transcribed+translated
            yield {"type":"transcript","text":english_input}
            
            async for chunk in self._run_pipeline(english_input, detected_lang, user_id, session_id):
                yield chunk
            
        except Exception as e:
            print(f"[INVESTIGATOR TEAM] Error in speech to text transcription: {e}")
            yield {"type": "error", "message": "Voice processing failed. Please try again."}
            
            
    async def _run_pipeline(self,english_input:str,target_lang:str,user_id:str,session_id:str):
        try:
            session_state = self._safe_get_session_state(session_id=session_id) or {"user_id":user_id,"session_id":session_id}
            
            # detect if the user lang has changed mid conversation or not
            if session_state.get("user_language") != target_lang:
                try:
                    self.team.update_session_state(
                        session_state_updates={"user_language":target_lang},
                        session_id=session_id,
                    )
                except Exception:
                    pass
            
            stream = self.team.arun(
                input=english_input,
                user_id=user_id,
                session_id=session_id,
                session_state={
                    "user_id":user_id,
                    "session_id":session_id,
                    "user_language":target_lang,
                },
                stream=True,
                stream_events=True,
            )
            
            # session_state["user_language"] = target_lang
            
            print(f"[INVESTIGATOR TEAM] Session state after team run : {session_state}")
            
            final_response = None
            sentence_buffer = ""
            
            async for event in stream:
                if isinstance(event,RunContentEvent):
                    if not event.content:
                        continue
                    
                    # if the user speaks in english only, no need to go through translation complexity
                    if target_lang == "en-IN":
                        yield {"type":"stream_chunk","content":event.content}
                        continue
                    
                    sentence_buffer += event.content
                    parts = SENTENCE_END_RE.split(sentence_buffer)
                    
                    if len(parts)>1:
                        *complete,sentence_buffer = parts
                        for sentence in complete:
                            translated = await self.translation_layer.translate_text(
                                text=sentence,source_lang="en-IN",target_lang=target_lang,
                            ) or {}
                            
                            translated_sentence = translated.get("translated_text")
                            
                            if not translated_sentence:
                                continue
                            
                            yield {"type": "stream_chunk", "content": translated_sentence + " "}
                            
                            audio = await self.translation_layer.synthesize_speech(text=translated_sentence,target_lang=target_lang,speaker="shubh") or {}
                            if audio and audio.get("audios"):
                                yield {"type": "audio_chunk", "audio": audio["audios"][0], "format": "wav"}
                elif isinstance(event,ToolCallStartedEvent):
                    tool_name = getattr(event.tool,"tool_name","") or ""
                    tool_args = getattr(event.tool,"tool_args",{}) or {}
                    
                    if tool_name in self._delegate_tool_names:
                        member_id = tool_args.get("member_id")
                        task = tool_args.get("task")
                        label = self._agent_status_labels.get(member_id,member_id or "a specialist agent")
                        message = f"{label} — {task}" if task else f"{label}..."
                        yield {"type":"status","message":message}
                    else:
                        yield {
                        "type":"status",
                        "message": f"Running {tool_name or 'a tool'}...",
                        }
                elif isinstance(event, RunErrorEvent):
                    yield {"type": "error", "message": str(getattr(event, "error", "Something went wrong."))}
                elif isinstance(event,RunCompletedEvent):
                    final_response = event
                    
            if final_response is None:
                return
            
            if target_lang != "en-IN" and sentence_buffer.strip():
                translated = await self.translation_layer.translate_text(
                    text=sentence_buffer,source_lang="en-IN",target_lang=target_lang
                ) or {}

                translated_sentence = translated.get("translated_text")
                if translated_sentence:
                    yield {"type":"stream_chunk","content":translated_sentence}
                
                    audio = await self.translation_layer.synthesize_speech(
                    text=translated_sentence, target_lang=target_lang, speaker="shubh",
                    ) or {}
                    if audio and audio.get("audios"):
                        yield {"type": "audio_chunk", "audio": audio["audios"][0], "format": "wav"}
            
            for member_response in getattr(final_response, "member_responses", []) or []:
                if member_response.agent_name == "Analytics Agent":
                    analytics_output: AnalyticsResponse = member_response.content
                    self.team.update_session_state(
                        session_state_updates={
                            "analysis_type": analytics_output.analysis_type,
                            "analytics_answer": analytics_output.answer,
                            "chart_data": analytics_output.chart.model_dump_json() if analytics_output.chart else None,
                            "map_data": analytics_output.map.model_dump_json() if analytics_output.map else None,
                            "table_data": analytics_output.table,
                        },
                        session_id=session_id,
                    )
                    
            print(f"[INVESTIGATOR TEAM] User lang: {self._safe_get_session_state(session_id=session_id).get('user_language')}")
            session_state = self._safe_get_session_state(session_id=session_id)
            yield {
                "type": "assistant_message",
                "message": final_response.content,
                "session_state": session_state,
            }
        except Exception as e:
            print(f"[INVESTIGATOR TEAM] Exception in streaming agent output: {e}")
            
            

if __name__ == "__main__":
    team_obj = InvestigationTeam()
    
    user_id = "test-007"
    session_id = "team-test-001"
    while True:
        user_msg = input("User: ")
        
        if user_msg.strip() in ["bye","exit","quit"]:
            break
        
        response = team_obj.team_run(
            input=user_msg,
            user_id=user_id,
            session_id=session_id
        )
        
        print(f"Cluvo: {response.content}")
        print(f"Session state after current run: {response.session_state}")
        
