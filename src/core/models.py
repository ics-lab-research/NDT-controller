from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, List, Union
from typing_extensions import TypedDict

from ..baml_client.types import (
    ConnectToViTool,
    GetNumericIndicatorTool,
    GetViStatusTool,
    HandleSaveDialogTool,
    PressButtonTool,
    RunOpenViTool,
    SelectComboBoxTool,
    SelectTabTool,
    SetButtonStateTool,
    SetNumericControlTool,
    StopViTool,
    WaitForOperationCompleteTool,
    ExperimentStep,
)


# ============================== Experiment models ===========================
@dataclass
class ExperimentExecutionError(Exception):
    filename: str
    error_message: str


class ExperimentStatus(Enum):
    NOT_APPROVED = "❌ Not Approved"
    APPROVED = "✅ Approved"
    PENDING = "⏳ Pending"
    SCANNING = "⚡ Scanning"
    COMPLETED = "✅ Completed"
    ERROR = "❌ Error"


# Type alias for experiment tools
ExperimentTool = Union[
    ConnectToViTool,
    HandleSaveDialogTool,
    PressButtonTool,
    RunOpenViTool,
    SelectComboBoxTool,
    SelectTabTool,
    SetButtonStateTool,
    SetNumericControlTool,
    StopViTool,
    WaitForOperationCompleteTool,
]

BasicExpTool = Union[
    ConnectToViTool,
    GetViStatusTool,
    GetNumericIndicatorTool,
    HandleSaveDialogTool,
    PressButtonTool,
    RunOpenViTool,
    SelectComboBoxTool,
    SelectTabTool,
    SetButtonStateTool,
    SetNumericControlTool,
    StopViTool,
]


@dataclass
class ExperimentPlan:
    id: str
    filename: str
    experiment: List[ExperimentStep]
    status: ExperimentStatus = ExperimentStatus.NOT_APPROVED


@dataclass
class ExperimentMetadata:
    """Metadata for experiments mode."""

    data_dir_path: Path
    # plots_dir_path: Path
    plans_path: Path
    vi_path: Path


# TODO: metadata should have description of file


# ============================== Idea models ==================================
@dataclass
class IdeaMetadata:
    """Metadata for idea mode."""

    system_spec_path: Path
    idea_output_path: Path
    experiment_plan_path: Path
    data_science_plan_path: Path


# ============================== Data science models ==========================
@dataclass
class DataScienceMetadata:
    """Metadata for data science mode."""

    temp_dir_path: Path


# ============================== Reporting models =============================
@dataclass
class ReportingMetadata:
    """Metadata for reporting mode."""

    latex_dir_path: Path
    output_pdf_path: Path
    main_tex_path: Path
    introduction_tex_path: Path
    abstract_tex_path: Path
    experimental_setup_tex_path: Path
    results_tex_path: Path
    methodology_tex_path: Path
    conclusion_tex_path: Path
    references_bib_path: Path


# Type alias for mode metadata
ModeMetadata = Union[
    IdeaMetadata,
    ExperimentMetadata,
    DataScienceMetadata,
    ReportingMetadata,
]


# ============================== Other models =================================
class ChatMessage(TypedDict):
    role: str
    content: str
    metadata: Dict[str, str] | None


# Type alias for chat history using OpenAI-style message format
ChatHistory = List[ChatMessage]


class MessageType(Enum):
    NORMAL = "normal"
    ACTION = "action"
    STATUS = "status"
    INTERMEDIATE_STEP = "intermediate_step"


@dataclass
class AgentResponse:
    """Unified response structure for all agents."""

    response: str | None = None
    intermediate_step: str | None = None
    status: str | None = None
    action: str | None = None


@dataclass
class MultimodalMessage:
    """Model for multimodal chat input containing text and files."""

    text: str
    files: List[Path]


class Mode(Enum):
    IDEA = "idea"
    EXPERIMENT = "experiments"
    DATA_SCIENCE = "data-science"
    REPORTING = "reporting"

    @classmethod
    def from_string(cls, value: str) -> "Mode":
        """Convert string to Mode enum."""
        for mode in cls:
            if mode.value == value.lower():
                return mode
        raise ValueError(f"Unknown mode: {value}")

    @classmethod
    def get_values(cls) -> List[str]:
        """Get all mode values as strings."""
        return [mode.value for mode in cls]
