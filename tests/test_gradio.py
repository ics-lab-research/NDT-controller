from typing import Union, Literal, Optional, List, NotRequired, TypedDict
from dataclasses import dataclass
import gradio as gr

MessageContent = Union[str, gr.FileDataDict, gr.FileData, gr.Component]


@dataclass
class ChatMessage:
    content: MessageContent | list[MessageContent]
    role: Literal["user", "assistant"]
    metadata: Optional[MetadataDict] = None
    options: Optional[list[OptionDict]] = None


class MetadataDict(TypedDict):
    title: NotRequired[str]
    id: NotRequired[int | str]
    parent_id: NotRequired[int | str]
    log: NotRequired[str]
    duration: NotRequired[float]
    status: NotRequired[Literal["pending", "done"]]


class OptionDict(TypedDict):
    label: NotRequired[str]
    value: str


with gr.Blocks() as demo:
    chatbot = gr.Chatbot(
        value=[
            gr.ChatMessage(
                role="user", content="What is the weather in San Francisco?"
            ),
            gr.ChatMessage(
                role="assistant",
                content="I need to use the weather API tool?",
                metadata={"title": "🧠 Thinking"},
            ),
        ]
    )

demo.launch()
