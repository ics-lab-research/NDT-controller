MessageContent = Union[str, FileDataDict, FileData, Component]


@dataclass
class ChatMessage:
    content: MessageContent | [MessageContent]
    role: Literal["user", "assistant"]
    metadata: MetadataDict = None
    options: list[OptionDict] = None


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


import gradio as gr

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
