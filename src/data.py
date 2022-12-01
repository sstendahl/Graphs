from dataclasses import dataclass, field


@dataclass
class Data:
    filename: str = ""
    clipboard_pos: int = 0
    xdata: list = field(default_factory=list)
    ydata: list = field(default_factory=list)
    xdata_selected: list = field(default_factory=list)
    ydata_selected: list = field(default_factory=list)
    xdata_clipboard: list = field(default_factory=list)
    ydata_clipboard: list = field(default_factory=list)

