# Working Memory and Chat Schemas
from agno.models.message import Message
from agno.media import Image, Video, File, Audio
from typing import List, Optional, Any, Dict, Union, Sequence
from pydantic import BaseModel
from enum import Enum
import json
from pydantic import BaseModel, Field
from datetime import datetime, timezone
from uuid import UUID, uuid4

node_labels = [
    # Geographic entities
    "Country", "Region", "Port", "Border", "City",
    
    # Economic entities
    "Product", "Commodity", "IndustrySector", "Market", "Currency",
    
    # Supply chain entities
    "Supplier", "Manufacturer", "Distributor", "Retailer", "Customer",
    "Facility", "Warehouse", "Factory", "LogisticsHub",
    
    # Transport and logistics
    "Shipment", "TradeFlow", "TransportMode", "Route", "Carrier",
    "LogisticsScore", "CustomsProcess",
    
    # Risk and performance
    "Incident", "Disruption", "RiskFactor", "PerformanceMetric",
    "ComplianceStandard", "Regulation",
    
    # Time and events
    "TimePeriod", "Season", "Event", "Milestone"
]

# Supply Chain Relationships - Enhanced for better connectivity
rel_types = [
    # Core Trade relationships (weighted by value/volume)
    "EXPORTS_TO", "IMPORTS_FROM", "TRADES_WITH", "SUPPLIES",
    "REPORTED", "WITH_PARTNER", "OF_PRODUCT", "HAS_TRADE_BALANCE",
    
    # Geographic and infrastructure relationships
    "LOCATED_IN", "BORDERS", "CONNECTS_TO", "SHIPS_THROUGH",
    "USES_PORT", "CROSSES_BORDER", "TRANSIT_THROUGH", "NEIGHBORS",
    
    # Supply chain network relationships
    "SOURCES_FROM", "DISTRIBUTES_TO", "MANUFACTURES", "PRODUCES",
    "STORES", "TRANSPORTS", "DELIVERS_TO", "OUTSOURCES_TO",
    "PARTNERS_WITH", "COMPETES_WITH", "SUBSTITUTES_FOR",
    
    # Performance and metrics relationships
    "HAS_LPI_SCORE", "HAS_INDUSTRY_METRIC", "EXPERIENCES_DISRUPTION",
    "AFFECTS_PERFORMANCE", "MEASURES", "BENCHMARKS", "OUTPERFORMS",
    "CORRELATES_PERFORMANCE", "INFLUENCES_METRIC",
    
    # Risk and dependency relationships  
    "EXPOSES_TO_RISK", "MITIGATES_RISK", "DEPENDS_ON", "VULNERABLE_TO",
    "CREATES_BOTTLENECK", "PROVIDES_ALTERNATIVE", "SHARES_RISK",
    "DIVERSIFIES_RISK", "CONCENTRATES_RISK",
    
    # Temporal and trend relationships
    "OCCURS_IN", "PRECEDED_BY", "FOLLOWED_BY", "CORRELATES_WITH",
    "TRENDS_WITH", "SEASONAL_PATTERN", "CYCLICAL_WITH", "PEAKS_IN",
    
    # Regulatory and compliance relationships
    "REGULATED_BY", "COMPLIES_WITH", "CERTIFIED_BY", "INSPECTED_BY",
    "ENFORCES_STANDARD", "VIOLATES_REGULATION", "EXEMPTED_FROM",
    
    # Economic and market relationships
    "PRICED_IN", "DENOMINATED_IN", "AFFECTED_BY_EXCHANGE",
    "MARKET_LEADER_IN", "MARKET_SHARE_IN", "PRICE_SENSITIVE_TO"
]


theoretical_node_labels = [
    "Book",
    "Author",
    "Publisher",
    "Concept",
    "Theory",
    "Topic",
    "Framework",
    "Methodology",
    "Principle",
    "Practice",
    "CaseStudy",
    "ResearchPaper",
    "Standard",
    "Model",
    "SchoolOfThought",
    "Discipline",
    "Hypothesis",
    "Law",
    "Axiom",
    "Paradigm",
    "Field",
    "BestPractice",
    "WhitePaper",
    "GlossaryTerm",
    "Equation",
    "Metric"
]

theoretical_rel_nodes = [
    "COVERS_TOPIC",
    "WRITTEN_BY",
    "PUBLISHED_BY",
    "COVERS_CONCEPT",
    "COVERS_THEORY",
    "REFERENCES",
    "MENTIONS_STANDARD",
    "ILLUSTRATES",
    "HAS_FRAMEWORK",
    "USES_METHOD",
    "BASED_ON_PRINCIPLE",
    "RELATED_TO",
    "PART_OF",
    "APPLIES_TO",
    "HAS_CASE_STUDY",
    "DEFINES_TERM",
    "DERIVED_FROM",
    "PROPOSED_BY",
    "VALIDATED_BY",
    "CHALLENGES",
    "MEASURES",
    "USED_IN",
    "RECOMMENDED_PRACTICE",
    "HAS_EQUATION",
    "HAS_METRIC",
    "BELONGS_TO_SCHOOL",
    "INFLUENCES",
    "IS_PARADIGM_OF"
]



class Role(str, Enum):
    USER = 'user'
    SYSTEM = 'system'
    ASSISTANT = 'assistant'

class MediaContent(str, Enum):
    AUDIO = 'audio'
    VIDEO = 'video'
    IMAGE = 'image'
    FILE = 'file'

class MediaAttachment(BaseModel):
    type: MediaContent
    url: str

class HistoryTuple(BaseModel):
    user_id: str
    session_id: str
    sequence_id: int
    role: Role  # "system", "user", or "assistant"
    text_content: str
    reasoning_content: str | None = None
    attachments: List[MediaAttachment] | None = None

    @classmethod
    def from_db_row(cls, row: Dict[str, Any]) -> "HistoryTuple":
        """Convert database row to HistoryTuple"""
        attachments = None
        if row.get('attachments'):
            # Parse JSONB attachments field
            attachments_data = row['attachments'] if isinstance(row['attachments'], list) else json.loads(row['attachments'])
            attachments = [MediaAttachment(**att) for att in attachments_data]
        
        return cls(
            user_id=str(row['user_id']),
            session_id=str(row['session_id']),
            sequence_id=row['sequence_id'],
            role=Role(row['role']),
            text_content=row['text_content'] or "",
            reasoning_content=row.get('reasoning_content'),
            attachments=attachments
        )

class History(BaseModel):
    history: List[HistoryTuple]

    def to_string(self, last_n: Optional[int] = None) -> str:
        """
        Convert the history object to a string suitable for passing to an agent as content/system_message.
        If last_n is provided, only the latest last_n entries are included.
        """
        sorted_history = sorted(self.history, key=lambda x: x.sequence_id)
        if last_n is not None:
            sorted_history = sorted_history[-last_n:]
        lines = []
        for h in sorted_history:
            line = f"[{h.role.capitalize()}] {h.text_content}"
            if h.reasoning_content:
                line += f"\n  (Reasoning: {h.reasoning_content})"
            if h.attachments:
                for attachment in h.attachments:
                    line += f"\n  (Attachment: [{attachment.type.capitalize()}] {attachment.url})"
            lines.append(line)
        return "\n\n".join(lines)

def history_tuple_to_message(history_tuple: HistoryTuple) -> Message:
    """
    Convert a HistoryTuple object to an Agent Message, handling various media types.
    """
    images: List[Image] = []
    videos: List[Video] = []
    audio: List[Audio] = []
    files: List[File] = []

    if history_tuple.attachments:
        for attachment in history_tuple.attachments:
            if attachment.type == MediaContent.IMAGE:
                images.append(Image(url=attachment.url))
            elif attachment.type == MediaContent.VIDEO:
                videos.append(Video(url=attachment.url))
            elif attachment.type == MediaContent.AUDIO:
                audio.append(Audio(url=attachment.url))
            elif attachment.type == MediaContent.FILE:
                files.append(File(url=attachment.url))

    return Message(
        role=history_tuple.role,
        content=history_tuple.text_content,
        reasoning_content=history_tuple.reasoning_content,
        images=images or None,
        videos=videos or None,
        audio=audio or None,
        files=files or None
    )

def get_latest_history_string(history: History, n_pairs: int = 3) -> str:
    """Get latest n pairs (user-assistant) as string for agent context"""
    # Each pair is 2 entries (user, assistant), so n_pairs*2
    return history.to_string(last_n=n_pairs*2)


class APIResponse(BaseModel):
    task_id: Optional[str] = None
    task_status: Optional[str] = None
    data: dict | list | None = None
    status_code: int = 200
    error: Optional[str | dict] = None
    error_data: Optional[str | dict] = None


class ServiceResponse(BaseModel):
    service_output: Optional[str | dict] = None
    service_error:Optional[str | None] = None
    error_code:int|str|None=None


class ReasoningEvent(BaseModel):
    type: str = 'reasoning'
    data: str

class ResponseEvent(BaseModel):
    type: str = 'response'
    data: str

StreamChatEvent=Union[
    ReasoningEvent,
    ResponseEvent
]

class User(BaseModel):
    user_id: UUID = Field(default_factory=uuid4)
    user_name: str
    user_email: str
    user_password_hash: str
    ph_no: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime | None = None
    last_login: datetime | None = None
    is_active: bool = True
    timezone: str


# Pydantic models
class ChatRequest(BaseModel):
    user_id: Optional[str] = None  # Optional - will generate UUID if not provided
    message: str
    session_id: Optional[str] = None  # Optional - will generate if not provided
    attachments: list = []
