// SPDX-License-Identifier: GPL-3.0-or-later
namespace Graphs {
    [Compact]
    private class XryColumn {
        public double[] data;
        public int? first_val = null;
        public int last_val = 0;

        public XryColumn(int size) {
            this.data = new double[size];
        }
    }

    [Compact]
    private class XryText {
        public double x;
        public double y;
        public string text;
    }

    /**
     * Reader class for parsing xry files
     */
    public class XryParser : Object {
        private DataInputStream input;
        private XryColumn[] columns;
        private double[] xdata;
        private XryText[] texts;

        private int item_count;
        private int text_item_count = 0;

        private void skip (int n) throws Error {
            for (int i = 0; i < n; i++) input.read_line ();
        }

        public void parse (File file) throws Error {
            this.input = new DataInputStream (file.read ());

            skip (4);
            string[] b_params = input.read_line ().strip ().split (" ");
            double x_step = evaluate_string (b_params[3]);
            double x_value = evaluate_string (b_params[0]);

            skip(12);
            string[] info = input.read_line ().strip ().split (" ");
            item_count = (int) evaluate_string (info[0]);
            int length = (int) evaluate_string (info[1]);

            columns = new XryColumn[item_count];
            for (int i = 0; i < item_count; i++) {
                columns[i] = new XryColumn (length);
            }
            xdata = new double[length];

            for (int i = 0; i < length; i++) {
                string[] values = input.read_line ().strip ().split (" ");
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
                if (column.first_val != 0)
                    column.data = column.data[column.first_val:];
                if (column.last_val != column.data.length - 1 + column.first_val)
                    column.data.resize (column.last_val - column.first_val);
            }

            skip (9 + item_count);
            text_item_count = (int) evaluate_string (input.read_line ());

            for (int i = 0; i < text_item_count; i++) {
                XryText text = new XryText ();

                string[] values = input.read_line ().strip ().split (" ");
                text.x = evaluate_string (values[5]);
                text.y = evaluate_string (values[6]);
                text.text = string.joinv (" ", values[7:]);

                texts[i] = (owned) text;
            }
        }

        public int get_item_count () {
            return item_count;
        }

        public int get_text_item_count () {
            return text_item_count;
        }

        public double[] get_xdata () {
            return (owned) xdata;
        }

        public double[] get_ydata (int idx) {
            return (owned) columns[idx].data;
        }

        public string get_text_data (int idx, out double x, out double y) {
            unowned XryText text = texts[idx];
            x = text.x;
            y = text.y;
            return text.text;
        }
    }
}
