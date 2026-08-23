from pathlib import Path
import sys
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.append(str(PROJECT_ROOT))

from backend.database import create_connection


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
        return {
            "type":"error",
            "message":"Ran into an unknown error."
        }
        
        
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
        return {
            "type":"error",
            "message":"Ran into an unknown error."
        }
        
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
    try:
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
    except Exception as e:
        print(f"[ANALYTICS AGENT] Exception in crime type breakdown: {e}")
        return {
            "type":"error",
            "message":"Ran into an unknown error."
        }


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

    try:
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
    except Exception as e:
        print(f"[ANALYTICS AGENT] Exception in crime category breakdwon: {e}")
        return {
            "type":"error",
            "message":"Ran into an unknown error."
        }


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

    try:
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
    except Exception as e:
        print(f"[ANALYTICS AGENT] Exception in crime hotspot location: {e}")
        return {
            "type":"error",
            "message":"Ran into an unknown error."
        }


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

    try:
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
    except Exception as e:
        print(f"[ANALYTICS AGENT] Exception in top repeat offenders: {e}")
        return {
            "type":"error",
            "message":"Ran into an unknown error."
        }