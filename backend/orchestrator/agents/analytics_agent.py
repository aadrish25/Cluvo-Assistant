import sys
from pathlib import Path
from typing import Any,Literal
from pydantic import BaseModel,Field
from agno.agent import Agent

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.append(str(PROJECT_ROOT))
DATABASE_PATH = BASE_DIR / "database" / "ksp_crime_platform.db"

from backend.database import create_connection
from backend.orchestrator.prompts.analytics_agent_prompt import ANALYTICS_AGENT_SYSTEM_PROMPT
from backend.database import memory_db
from backend.orchestrator.llm import gemma4_31b
import pandas as pd



# define schemas for the agent to return
class ChartData(BaseModel):
    type: Literal["bar","line","pie"] = Field(
        description="Chart type the frontend should render."
    )
    title: str = Field(
        description="Human-readable chart title."
    )
    x: list[Any] | None = Field(
        default=None,
        description="X-axis values for bar or line chart"
    )
    y: list[Any] | None = Field(
        default=None,
        description="Y-axis values for bar or line chart"
    )
    labels: list[Any] | None = Field(
        default=None,
        description="labels for pie charts"
    )
    values: list[Any] | None = Field(
        default=None,
        description="Numeric values for pie charts"
    )
    x_label: str | None = Field(
        default=None,
        description="X-axis label for bar or line chart"
    )
    y_lable: str | None = Field(
        default=None,
        description="Y-axis label for bar or line chart"
    )
    
    
class MapPoint(BaseModel):
    location_name: str = Field(
        description="Location name for the hotspot marker."
    )
    district: str = Field(
        description="District where the hotspot is located."
    )
    city: str | None = Field(
        default=None,
        description="City where the hotspot is located."
    )
    latitude: float = Field(
        description="Latitude coordinate for map rendering."
    )
    longitude: float = Field(
        description="Longitude coordinate for map rendering."
    )
    incident_count: int = Field(
        description="Number of incidents at this location."
    )
    avg_severity: float | None = Field(
        default=None,
        description="Average severity score for incidents at this location."
    )


class MapData(BaseModel):
    type: Literal["circle_markers"] = Field(
        description="Map visualization type for the frontend."
    )
    points: list[MapPoint] = Field(
        description="Hotspot points to render on the map."
    )


class AnalyticsResponse(BaseModel):
    analysis_type: str = Field(
        description="Stable identifier for the analysis, such as crime_count_by_district."
    )
    answer: str = Field(
        description="Short natural-language insight for the user."
    )
    chart: ChartData | None = Field(
        default=None,
        description="Chart-ready data if this analysis should be visualized as a chart."
    )
    map: MapData | None = Field(
        default=None,
        description="Map-ready data if this analysis should be visualized geographically."
    )
    table: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Raw tabular result rows for table display or debugging."
    )
    
    
# =================================================================================================



# define the analytics tools
def crime_count_by_district():
    """
    Return crime incident counts grouped by district.

    Args:
        None.

    Returns:
        list[dict]: Rows with `district` and `incident_count`, sorted highest
        first. Use for district-wise crime distribution or highest-crime district.
    """
    
    try:
        district_query = """
        SELECT
            l.district,
            COUNT(*) AS incident_count
        FROM CrimeIncident ci
        JOIN Location l ON l.location_id = ci.location_id
        GROUP BY l.district
        ORDER BY incident_count DESC;
        """
        
        conn = create_connection()
        cursor = conn.cursor()
        
        cursor.execute(district_query)
        rows = cursor.fetchall()
        
        return [dict(row) for row in rows]
        
    except Exception as e:
        print(f"[ANALYTICS AGENT] Error in generating crime count by district: {e}")
        
        
def monthly_crime_trend():
    """
    Return crime incident counts grouped by month.

    Args:
        None.

    Returns:
        list[dict]: Rows with `month` and `incident_count`, sorted
        chronologically. Use for monthly trends, time-series charts, or
        October/November spike analysis.
    """
    
    try:
        
        monthly_crime_query = """
        SELECT
            strftime('%Y-%m', ci.crime_datetime) AS month,
            COUNT(*) AS incident_count
        FROM CrimeIncident ci
        GROUP BY month
        ORDER BY month;
        """
        
        conn = create_connection()
        cursor = conn.cursor()
        
        cursor.execute(monthly_crime_query)
        rows = cursor.fetchall()
        
        # print(f"[ANALYTICS AGENT] {[dict(row) for row in rows]}")
        
        return [dict(row) for row in rows]
    
    except Exception as e:
        print(f"[ANALYTICS AGENT] Error in generating monthly crime trend: {e}")
        
        
def crime_type_breakdown():
    """
    Return incident counts grouped by specific crime type.

    Args:
        None.

    Returns:
        list[dict]: Rows with `crime_name`, `category`, and `incident_count`,
        sorted highest first. Use for crime-type distribution and most common
        crime type questions.
    """

    crime_type_query = """
        SELECT
            ct.crime_name,
            ct.category,
            COUNT(*) AS incident_count
        FROM CrimeIncident ci
        JOIN CrimeType ct ON ct.crime_type_id = ci.crime_type_id
        GROUP BY ct.crime_type_id, ct.crime_name, ct.category
        ORDER BY incident_count DESC;
        """
        
    conn = create_connection()
    cursor = conn.cursor()
    
    cursor.execute(crime_type_query)
    rows = cursor.fetchall()
    
    # print(f"[ANALYTICS AGENT] {[dict(row) for row in rows]}")
        
    return [dict(row) for row in rows]



def crime_category_breakdown():
    """
    Return incident counts grouped by broad crime category.

    Args:
        None.

    Returns:
        list[dict]: Rows with `category` and `incident_count`, sorted highest
        first. Use for property vs violent vs economic vs organized crime
        breakdowns.
    """

    crime_category_query = """
    SELECT
        ct.category,
        COUNT(*) AS incident_count
    FROM CrimeIncident ci
    JOIN CrimeType ct ON ct.crime_type_id = ci.crime_type_id
    GROUP BY ct.category
    ORDER BY incident_count DESC;
    """
    
    conn = create_connection()
    cursor = conn.cursor()
    
    cursor.execute(crime_category_query)
    rows = cursor.fetchall()
    
    # print(f"[ANALYTICS AGENT] {[dict(row) for row in rows]}")
    
    return [dict(row) for row in rows]



def crime_hotspots():
    """
    Return map-ready crime hotspot data grouped by location.

    Args:
        None.

    Returns:
        list[dict]: Rows with location name, district, city, latitude,
        longitude, `incident_count`, and `avg_severity`, sorted by incident
        count. Use for hotspot maps and high-crime location analysis.
    """

    crime_hotspot_query = """
    SELECT
        l.location_id,
        l.location_name,
        l.district,
        l.city,
        l.latitude,
        l.longitude,
        COUNT(*) AS incident_count,
        ROUND(AVG(ci.severity), 2) AS avg_severity
    FROM CrimeIncident ci
    JOIN Location l ON l.location_id = ci.location_id
    GROUP BY
        l.location_id,
        l.location_name,
        l.district,
        l.city,
        l.latitude,
        l.longitude
    ORDER BY incident_count DESC;
    """
    
    conn = create_connection()
    cursor = conn.cursor()
    
    cursor.execute(crime_hotspot_query)
    
    rows = cursor.fetchall()
    
    print(f"[ANALYTICS AGENT] {[dict(row) for row in rows]}")   
    
    return [dict(row) for row in rows] 



def top_repeat_offenders(limit: int = 10):
    """
    Return accused persons ranked by accused-linked incident count.

    Args:
        limit (int): Maximum number of ranked offenders to return. Defaults to
        10.

    Returns:
        list[dict]: Rows with `person_id`, `person_name`, and
        `accused_incident_count`, sorted highest first. Use for repeat offender
        and most frequent accused questions.
    """

    repeat_offenders_query = """
    SELECT
        p.person_id,
        p.first_name || ' ' || p.last_name AS person_name,
        COUNT(DISTINCT cp.incident_id) AS accused_incident_count
    FROM CrimeParticipant cp
    JOIN Person p ON p.person_id = cp.person_id
    WHERE cp.role = 'Accused'
    GROUP BY p.person_id, person_name
    ORDER BY accused_incident_count DESC
    LIMIT ?;
    """
    
    conn = create_connection()
    cursor = conn.cursor()
    
    cursor.execute(repeat_offenders_query,(limit,))
    rows = cursor.fetchall()
    
    # print(f"[ANALYTICS AGENT] {[dict(row) for row in rows]}")
    
    return [dict(row) for row in rows]


# define the analytics agent finally
def create_analytics_agent():
    try:
        return Agent(
          model = gemma4_31b,
          name = "Analytics Agent",
          description = "Computes crime trends, rankings, breakdowns, and hotspot analytics from the KSP crime database.",
          system_message = ANALYTICS_AGENT_SYSTEM_PROMPT,
          tools = [
              crime_count_by_district,
              monthly_crime_trend,
              crime_type_breakdown,
              crime_category_breakdown,
              crime_hotspots,
              top_repeat_offenders,
          ],
          output_schema=AnalyticsResponse,
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
        print(f"[ANALYTICS AGENT] Error in creating analytics agent: {e}")
        
if __name__ == "__main__":
    agent = create_analytics_agent()
    
    response = agent.run("What are the top districts in terms of crime count?")
    print(response.content)
    
    
