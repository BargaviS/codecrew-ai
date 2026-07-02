from pydantic import BaseModel
from typing import List, Optional
from enum import Enum


class Language(str, Enum):
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    SQL = "sql"


class AgentName(str, Enum):
    PLANNER = "Planner"
    CODER = "Coder"
    REVIEWER = "Reviewer"
    TESTER = "Tester"
    DOCUMENTER = "Documenter"


class SessionStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class IssueSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ClarifyingQuestion(BaseModel):
    question: str
    reason: str


class PlanStep(BaseModel):
    step_number: int
    title: str
    description: str
    files_to_create: List[str]


class PlannerOutput(BaseModel):
    understood_requirement: str
    clarifying_questions: List[ClarifyingQuestion]
    plan: List[PlanStep]
    tech_stack: List[str]
    estimated_complexity: str


class CodeFile(BaseModel):
    filename: str
    content: str
    description: str


class CoderOutput(BaseModel):
    files: List[CodeFile]
    explanation: str
    assumptions_made: List[str]


class CodeIssue(BaseModel):
    file: str
    line_hint: str
    severity: IssueSeverity
    category: str
    description: str
    suggestion: str


class ReviewerOutput(BaseModel):
    approved: bool
    overall_quality_score: int
    issues: List[CodeIssue]
    positive_aspects: List[str]
    summary: str
    round_number: int


class TestCase(BaseModel):
    test_name: str
    description: str
    test_code: str


class TesterOutput(BaseModel):
    test_file: str
    test_cases: List[TestCase]
    coverage_areas: List[str]
    edge_cases_covered: List[str]


class DocumenterOutput(BaseModel):
    readme_section: str
    api_docs: str
    usage_examples: str
    setup_instructions: str


class AgentMessage(BaseModel):
    agent: AgentName
    message_type: str
    content: str
    round_number: int = 1


class SessionRequest(BaseModel):
    requirement: str
    language: Language = Language.PYTHON
    framework: Optional[str] = None
    additional_context: Optional[str] = None


class SessionResponse(BaseModel):
    session_id: str
    status: SessionStatus
    message: str


class SessionResult(BaseModel):
    session_id: str
    status: SessionStatus
    requirement: str
    language: str
    planner_output: Optional[PlannerOutput] = None
    coder_output: Optional[CoderOutput] = None
    reviewer_output: Optional[ReviewerOutput] = None
    tester_output: Optional[TesterOutput] = None
    documenter_output: Optional[DocumenterOutput] = None
    agent_messages: List[AgentMessage] = []
    total_review_rounds: int = 0
    initial_quality_score: int = 0
    final_quality_score: int = 0
    error: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    app: str
    env: str
    agents: List[str]
