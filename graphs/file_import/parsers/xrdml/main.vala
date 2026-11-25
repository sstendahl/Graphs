// SPDX-License-Identifier: GPL-3.0-or-later
namespace Graphs {
    public class XrdmlParser : Parser {
        private const string[] XRDML_FILE_SUFFIXES = {"xrdml", null};

        public XrdmlParser () {
            Object (
                name: "xrdml",
                ui_name: C_("import-mode", "xrdml"),
                filetype_name: C_("file-filter", "PANalytical XRDML"),
                file_suffixes: XRDML_FILE_SUFFIXES
            );
        }

        public override void init_import_settings (ImportSettings settings) throws ParseError {
            settings.set_item ("reader", new XrdmlReader (settings.file));
            settings.set_int ("scan", 0);
        }

        public override void append_settings_widgets (ImportSettings settings, Gtk.Box settings_box) throws ParseError {
            var reader = settings.get_item ("reader") as XrdmlReader;
            if (reader == null || !(reader.has_q || reader.has_counting_time || reader.n_scans > 1)) return;

            settings_box.append (new XrdmlGroup (settings));
        }

        public override ItemList parse (ImportSettings settings, StyleParameters style) throws ParseError {
            var reader = (XrdmlReader) settings.get_item ("reader");
            return reader.parse (settings, style);
        }
    }
}
