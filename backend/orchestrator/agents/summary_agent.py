from agno.agent import Agent
from agno.run import RunContext
import re
import sys
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer
from reportlab.lib.styles import getSampleStyleSheet

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.append(str(PROJECT_ROOT))

from backend.database import create_connection
from backend.orchestrator.llm import gemma4_31b
from backend.orchestrator.prompts.summary_agent_prompt import SUMMARY_AGENT_SYSTEM_PROMPT
from backend.database import memory_db

REPORT_DIR = BASE_DIR / "reports"
REPORT_DIR.mkdir(parents=True,exist_ok=True)


# build fir context
def build_fir_context(fir_number:str,run_context:RunContext):
    """
    Fetch all structured database context needed to summarize one FIR.

    Args:
        fir_number (str): Exact FIR number to summarize, such as
        "KSP/2023/0042".

    Returns:
        dict: FIR summary context with these keys:
        - `fir_overview`: FIR, case, complainant, status, and police station data.
        - `incidents_under_fir`: incidents, crime types, MO, severity, and locations.
        - `incident_participants`: accused, victims, and witnesses linked to incidents.
        - `investigation_info`: assigned officers, status, priority, and next actions.
        - `timeline_info`: chronological investigation events.
        - `evidence_info`: evidence, forensic status, storage, and chain of custody.

    Use this tool when the user asks to summarize, brief, report on, or generate
    a narrative for a specific FIR.
    """
    
    try:
        
        conn = create_connection()
        cursor = conn.cursor()
        
        run_context.session_state["summary_fir_number"] = fir_number
        
        # fetch FIR overview
        fir_overview_query = """
        SELECT
            f.fir_id,
            f.fir_number,
            f.filing_date,
            f.complainant_name,
            f.description AS fir_description,
            f.status AS fir_status,
            c.case_number,
            c.title AS case_title,
            c.priority AS case_priority,
            c.status AS case_status,
            ps.station_name,
            ps.district AS station_district,
            ps.city AS station_city
        FROM FIR f
        LEFT JOIN "Case" c ON c.case_id = f.case_id
        LEFT JOIN PoliceStation ps ON ps.station_id = f.police_station_id
        WHERE f.fir_number = ?;
        """
        
        cursor.execute(fir_overview_query,(fir_number,))
        
        fir_overview_rows = cursor.fetchall()
        
        # run_context.session_state["fir"] = [dict(row) for row in fir_overview_rows][0]
        
        fir_overview = [dict(row) for row in fir_overview_rows][0]
        
        print(f"[SUMMARY AGENT] {[dict(row) for row in fir_overview_rows][0]}")
        
        
        # fetch all incidents related to this FIR
        fir_incident_query = """
        SELECT
            ci.incident_id,
            ci.crime_datetime,
            ci.weapon_used,
            ci.severity,
            ci.status AS incident_status,
            ci.description AS incident_description,
            ct.crime_name,
            ct.category,
            mo.mo_name,
            l.location_name,
            l.district,
            l.city,
            l.latitude,
            l.longitude
        FROM CrimeIncident ci
        LEFT JOIN CrimeType ct ON ct.crime_type_id = ci.crime_type_id
        LEFT JOIN ModusOperandi mo ON mo.mo_id = ci.mo_id
        LEFT JOIN Location l ON l.location_id = ci.location_id
        WHERE ci.fir_id = ?;
        """
        
        cursor.execute(fir_incident_query,(fir_overview.get("fir_id"),))
        
        fir_incident_rows = cursor.fetchall()
        
        fir_incidents = [dict(row) for row in fir_incident_rows]
        incident_ids = [incident.get("incident_id") for incident in fir_incidents]
        
        # run_context.session_state["incident"] = [dict(row) for row in fir_incident_rows]
        print(f"[SUMMARY AGENT] {incident_ids}")
        
        
        # fetch all particpants related to each incident
        
        incident_id_placeholders = ",".join(["?"] * len(incident_ids))
        
        participant_query = f"""
        SELECT
            cp.incident_id,
            cp.role,
            cp.injury_status,
            cp.arrest_status,
            cp.remarks,
            p.person_id,
            p.first_name,
            p.last_name,
            p.gender,
            p.date_of_birth,
            p.occupation
        FROM CrimeParticipant cp
        JOIN Person p ON p.person_id = cp.person_id
        WHERE cp.incident_id IN ({incident_id_placeholders})
        ORDER BY cp.role;
        """
        cursor.execute(participant_query,tuple(incident_ids))
        participant_rows = cursor.fetchall()
        
        participant_info = [dict(row) for row in participant_rows]
        
        print(f"[SUMMARY AGENT] Participant rows: {participant_info}")
        
        
        # fetch investigations related to these incidents
        investigation_query = f"""
        SELECT
            i.incident_id,
            i.status,
            i.priority,
            i.assigned_date,
            i.closed_date,
            i.next_action,
            i.remarks,
            o.name AS officer_name,
            o.badge_number,
            o.rank,
            o.specialization
        FROM Investigation i
        LEFT JOIN Officer o ON o.officer_id = i.officer_id
        WHERE i.incident_id IN ({incident_id_placeholders});
        """
        
        cursor.execute(investigation_query,tuple(incident_ids))
        investigation_rows = cursor.fetchall()
        
        investigation_info = [dict(row) for row in investigation_rows]
        
        print(f"[SUMMARY AGENT] Investigation info: {investigation_info}")
        
        
        # fetch timeline of the incidents
        timeline_query = f"""
        SELECT
            te.incident_id,
            te.event_time,
            te.event_type,
            te.description,
            o.name AS officer_name
        FROM TimelineEvent te
        LEFT JOIN Officer o ON o.officer_id = te.officer_id
        WHERE te.incident_id IN ({incident_id_placeholders})
        ORDER BY te.event_time;
        """
        
        cursor.execute(timeline_query,tuple(incident_ids))
        timeline_rows = cursor.fetchall()
        
        timeline_info = [dict(row) for row in timeline_rows]
        
        print(f"[SUMMARY AGENT] Timeline info: {timeline_info}")
        
        
        # fetch evidence for the incidents
        evidence_query = f"""
        SELECT
            ce.incident_id,
            e.evidence_type,
            e.description,
            e.collection_date,
            e.forensic_status,
            e.storage_location,
            e.chain_of_custody
        FROM CrimeEvidence ce
        JOIN Evidence e ON e.evidence_id = ce.evidence_id
        WHERE ce.incident_id IN ({incident_id_placeholders});
        """
        
        cursor.execute(evidence_query,tuple(incident_ids))
        evidence_rows = cursor.fetchall()
        
        evidence_info = [dict(row) for row in evidence_rows]
        
        print(f"[SUMMARY AGENT] Evidence info: {evidence_info}")
        
        fir_context =  {
            "fir_overview":fir_overview,
            "incidents_under_fir":fir_incidents,
            "incident_participants":participant_info,
            "investigation_info":investigation_info,
            "timeline_info":timeline_info,
            "evidence_info":evidence_info,
        } 
        
        run_context.session_state["fir_summary_context"] = fir_context
        
        return fir_context              
        
    except Exception as e:
        print(f"[SUMMARY AGENT] Exception occured: {e}")
        

# saving to pdf
def save_summary_report_pdf(run_context:RunContext,report_text:str) -> str:
    try:
        fir_number = run_context.session_state["summary_fir_number"]
        safe_fir = fir_number.replace("/","_")
        output_path = REPORT_DIR / f"{safe_fir}_summary_report.pdf"
        
        doc = SimpleDocTemplate(str(output_path),pagesize=A4)
        styles = getSampleStyleSheet()
        
        story = []
        
        for line in report_text.splitlines():
            if not line.strip():
                story.append(Spacer(1,10))
                continue
            
            if line.startswith("# "):
                story.append(Paragraph(line[2:],styles["Title"]))
            if line.startswith("## "):
                story.append(Paragraph(line[3:],styles["Heading2"]))
            if line.startswith("### "):
                story.append(Paragraph(line[4:],styles["Heading3"]))
            elif line.startswith("- "):
                story.append(Paragraph(f"• {line[2:]}",styles["BodyText"]))
            else:
                story.append(Paragraph(line,styles["BodyText"]))
                
                
            story.append(Spacer(1,6))
            
        doc.build(story)
        run_context.session_state["summary_report_pdf_path"] = str(output_path)

        return "Report PDF saved successfully!"
    
    except Exception as e:
        print(f"[SUMMARY AGENT] Error in report pdf generation: {e}")


# create the FIR summary agent
def create_summary_agent():
    try:
        return Agent(
          model = gemma4_31b,
          name = "Summary Agent",
          description = "An agent that summarizes and generates a report for a FIR on the KSP Crime Database.",
          system_message = SUMMARY_AGENT_SYSTEM_PROMPT,
          tools = [
              build_fir_context,
              save_summary_report_pdf
          ],
          reasoning = True,
          db=memory_db,
          reasoning_min_steps = 3,
          reasoning_max_steps = 7,
          add_history_to_context=False,
          add_session_state_to_context=True,
          telemetry=True,
          debug_mode = True
        )
    except Exception as e:
        print(f"[SUMMARY AGENT] Error in creating summary agent: {e}")
        
if __name__ == "__main__":
    agent = create_summary_agent()
    
    agent.print_response("Generate me a summary for fir number KSP/2023/0040")
