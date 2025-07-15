# SPDX-License-Identifier: GPL-3.0-or-later
"""
Module for importing data from files.

    Functions:
        import_from_files
        import_from_sql
"""
import sqlite3
from pathlib import Path

from gi.repository import Adw, GObject, Gio, Graphs, Gtk

from graphs import parse_file
from graphs.misc import ParseError

_IMPORT_MODES = {
    # name: suffix
    "project": ".graphs",
    "sql": ".db",
    "xrdml": ".xrdml",
    "xry": ".xry",
    "columns": None,
}


@Gtk.Template(resource_path="/se/sjoerd/Graphs/ui/import-sql.ui")
class ImportSqlDialog(Adw.Dialog):
    """The dialog for importing SQL files."""

    __gtype_name__ = "GraphsImportSqlDialog"
    __gsignals__ = {
        "accept": (GObject.SIGNAL_RUN_FIRST, None, ()),
    }
    table_list = Gtk.Template.Child()
    column_x = Gtk.Template.Child()
    column_y = Gtk.Template.Child()

    def __init__(self, window: Graphs.Window, file):
        super().__init__()
        self.database = sqlite_to_dict(file)
        self.filename = Graphs.tools_get_filename(file)
        table_list = Gtk.StringList.new(list(self.database.keys()))
        self.table_list.set_model(table_list)
        self.table_list.connect("notify::selected", self.populate_entries)
        self.populate_entries(None, None)
        self.present(window)

    @Gtk.Template.Callback()
    def on_accept(self, _button):
        """Emit an accept signal when pressing the import data."""
        self.emit("accept")
        self.close()

    def populate_entries(self, _comborow, _) -> None:
        """Populate the column x and column y entries."""
        table = self.table_list.get_selected_item().get_string()
        columns = self.database[table]
        column_list = Gtk.StringList.new(list(columns.keys()))
        self.column_x.set_model(column_list)
        self.column_y.set_model(column_list)

    @property
    def selected_data(self) -> dict:
        """Get the data from the database as selected by the dialog."""
        table = self.table_list.get_selected_item().get_string()
        x_column = self.column_x.get_selected_item().get_string()
        y_column = self.column_y.get_selected_item().get_string()
        xdata = [x_column]
        ydata = [y_column]
        xdata.extend(self.database[table][x_column])
        ydata.extend(self.database[table][y_column])
        return {"name": self.filename, "xdata": xdata, "ydata": ydata}


def import_from_files(
    window: Graphs.Window,
    files: list[Gio.File],
) -> None:
    """
    Import from a list of files.

    Automatically guesses, which mode to use. If configurable settings are
    present at /se/sjoerd/Graphs/import-params, a Window will be shown,
    giving the option to configure them.
    """
    application = window.get_application()
    settings = application.get_settings_child("import-params")

    import_dict = {mode: [] for mode in _IMPORT_MODES}
    for file in files:
        mode = _guess_import_mode(file)
        import_dict[mode].append(file)

    modes = [mode for mode in settings.list_children()
             if import_dict.get(mode) and mode != "sql"]
    sql_files = import_dict.pop("sql")

    def _do_import(dialog):
        items = []
        data = window.get_data()
        style = data.get_selected_style_params()

        if isinstance(dialog, ImportSqlDialog):
            in_data = dialog.selected_data
            try:
                items.extend(parse_file.import_from_sql(None, style, in_data))
            except ParseError as error:
                application.get_active_window().add_toast_string(error.message)
        else:
            for mode, files in import_dict.items():
                callback = getattr(parse_file, "import_from_" + mode)
                params = settings.get_child(mode) if mode in modes else None

                for file in files:
                    try:
                        items.extend(callback(params, style, file))
                    except ParseError as error:
                        application.get_active_window().add_toast_string(
                            error.message,
                        )
                        continue
        data.add_items(items)

    for file in sql_files:
        sql_dialog = ImportSqlDialog(window, file)
        sql_dialog.connect("accept", _do_import)

    if modes:
        dialog = Graphs.ImportDialog.new(window, modes)
        dialog.connect("accept", _do_import)
    elif not sql_files:
        _do_import(None)


def _guess_import_mode(file: Gio.File) -> str:
    try:
        filename = Graphs.tools_get_filename(file)
        file_suffix = Path(filename).suffixes[-1]
    except IndexError:
        file_suffix = None
    for mode, suffix in _IMPORT_MODES.items():
        if suffix is not None and file_suffix == suffix:
            return mode
    return "columns"


def sqlite_to_dict(file: Gio.File) -> dict:
    """Read a SQLite .db file and returns db as dictionary."""
    result = {}

    with sqlite3.connect(file) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row["name"] for row in cur.fetchall()]

        for table in tables:
            cur.execute(f"SELECT * FROM {table}")
            rows = cur.fetchall()
            columns = [desc[0] for desc in cur.description]
            result[table] = {
                col: [row[index] for row in rows]
                for index, col in enumerate(columns)
            }

    return result
