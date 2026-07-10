from dataclasses import dataclass,field

@dataclass
class Context:
    user_id: str = None
    session_id: str = None
    user_msg: str = None
    
    # fields from SQL agent
    person_ids: list =field(default_factory=list)
    case_ids: list = field(default_factory=list)
    fir_ids: list = field(default_factory=list)
    incident_ids: list = field(default_factory=list)
    account_ids: list = field(default_factory=list)
    vehicle_ids: list = field(default_factory=list)
    location_ids: list = field(default_factory=list)
    organization_ids: list = field(default_factory=list)
    date_range: tuple = None
    district: str = None
    last_sql_query: str = None
    
    
    # fields for graph agent
    person_name: str = None
    graph_list: list = field(default_factory=list)
    graph_html_paths: list = field(default_factory=list)
    graph_count: int = 0
    
    
    # fields for analytics agent
    analysis_type: str = None
    analytics_answer: str = None
    chart_data:dict = field(default_factory=dict)
    map_data: dict = field(default_factory=dict)
    table_data: list = field(default_factory=list)
    
    
    # fields for summary agent
    summary_fir_number: str = None
    fir_summary_context: dict = field(default_factory=dict)
    summary_report_pdf_path: str = None
