// SPDX-License-Identifier: GPL-3.0-or-later
namespace Graphs {
    [Compact]
    private class XryColumn {
        public double[] data;
        public int? first_val = null;
        public int last_val = 0;

        public XryColumn (int size) {
            this.data = new double[size];
        }
    }

    /**
     * Reader class for parsing xry files
     */
    public class XryParser : Parser {
        private const string[] XRY_FILE_SUFFIXES = {"xry", null};

        public XryParser () {
            Object (
                name: "xry",
                ui_name: C_("import-mode", "xry"),
                filetype_name: C_("file-filter", "Leybold xry"),
                file_suffixes: XRY_FILE_SUFFIXES
            );
        }

        private static void skip (DataInputStream input, int n) throws Error {
            for (int i = 0; i < n; i++) input.read_line ();
        }

        public override ItemList parse (ImportSettings settings, StyleParameters style) throws ParseError {
            ItemList items = new ItemList ();

            try {
                var converter = new CharsetConverter ("UTF-8", "ISO-8859-1");
                var conv_stream = new ConverterInputStream (settings.file.read (), converter);
                DataInputStream input = new DataInputStream (conv_stream);

                skip (input, 4);
                string[] b_params = input.read_line ().strip ().split (" ");
                double x_step = evaluate_string (b_params[3]);
                double x_value = evaluate_string (b_params[0]);

                skip (input, 12);
                string[] info = input.read_line ().strip ().split (" ");
                int item_count = (int) evaluate_string (info[0]);
                int length = (int) evaluate_string (info[1]);

                XryColumn[] columns = new XryColumn[item_count];
                for (int i = 0; i < item_count; i++) {
                    columns[i] = new XryColumn (length);
                }
                double[] xdata = new double[length];

                Regex whitespace = new Regex ("\\s+");

                for (int i = 0; i < length; i++) {
                    string line = input.read_line ().strip ();
                    string[] values = whitespace.split (line);
                    for (int j = 0; j < item_count; j++) {
                        if (!(values[j].down () == "nan")) {
                            columns[j].data[i] = evaluate_string (values[j]);
                            if (columns[j].first_val == null) columns[j].first_val = i;
                            columns[j].last_val = i;
                        }
                    }
                    xdata[i] = x_value;
                    x_value += x_step;
                }

                for (int i = 0; i < item_count; i++) {
                    unowned XryColumn column = columns[i];

                    string name = settings.filename;
                    if (item_count > 1) name = "%s - %d".printf (name, i + 1);

                    double[] item_xdata = xdata[column.first_val:column.last_val + 1];
                    double[] ydata = column.data[column.first_val:column.last_val + 1];
                    DataItem item = ItemFactory.new_data_item (style, (owned) item_xdata, (owned) ydata);
                    item.name = name;
                    item.xlabel = _("β (°)");
                    item.ylabel = _("R (1/s)");
                    items.add (item);
                }

                skip (input, 9 + item_count);
                int text_item_count = (int) evaluate_string (input.read_line ());
                for (int i = 0; i < text_item_count; i++) {
                    string[] values = input.read_line ().strip ().split (" ");

                    double xanchor = evaluate_string (values[5]);
                    double yanchor = evaluate_string (values[6]);
                    string text = string.joinv (" ", values[7:]);

                    TextItem item = ItemFactory.new_text_item (style, xanchor, yanchor, text);
                    item.name = text;
                    items.add (item);
                }

                input.close ();
            } catch (Error e) {
                throw new ParseError.INVALID (_("Import failed"));
            }

            return items;
        }
    }
}
