from pathlib import Path
import sys
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.append(str(PROJECT_ROOT))

from pydantic import BaseModel,Field
from typing import Literal,Any



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