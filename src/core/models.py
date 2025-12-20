from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, List, Union

from ..baml_client.types import (
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
)


@dataclass
class ExperimentExecutionError:
    filename: str
    error_message: str | None


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


@dataclass
class ExperimentPlan:
    filename: str
    experiment: List[ExperimentTool]
    status: ExperimentStatus = ExperimentStatus.NOT_APPROVED


# TODO: metadata should have description of file


@dataclass
class OrchestratorMetadata:
    """Metadata for orchestrator mode."""

    pass


@dataclass
class IdeaMetadata:
    """Metadata for idea mode."""

    system_spec_path: Path
    idea_output_path: Path
    experiment_plan_path: Path
    data_science_plan_path: Path


@dataclass
class ExperimentsMetadata:
    """Metadata for experiments mode."""

    data_dir_path: Path
    plans_path: Path
    vi_path: Path


@dataclass
class DataScienceMetadata:
    """Metadata for data science mode."""

    temp_dir_path: Path


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
    OrchestratorMetadata,
    IdeaMetadata,
    ExperimentsMetadata,
    DataScienceMetadata,
    ReportingMetadata,
]


@dataclass
class AgentResponse:
    """Unified response structure for all agents."""

    response: str | None = None
    status: str | None = None
    action: str | None = None


# Type alias for chat history using OpenAI-style message format
ChatMessage = Dict[
    str, Union[str, Dict[str, str]]
]  # Contains 'role' (str), 'content' (str), and optional 'metadata' (dict) keys
ChatMessageWithMetadata = Dict[str, Union[str, Dict[str, str]]]
ChatHistory = List[ChatMessage]


class Mode(Enum):
    IDEA = "idea"
    EXPERIMENTS = "experiments"
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
