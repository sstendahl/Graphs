// SPDX-License-Identifier: GPL-3.0-or-later
namespace Graphs {
    private const string ODS_TABLE_NAMESPACE = "urn:oasis:names:tc:opendocument:xmlns:table:1.0";
    private const string XLSX_MAIN_NAMESPACE = "http://schemas.openxmlformats.org/spreadsheetml/2006/main";

    private abstract class SpreadsheetParserInternal {
        protected Gsf.InfileZip input;

        protected SpreadsheetParserInternal (File file) throws ParseError {
            try {
                this.input = new Gsf.InfileZip (new Gsf.InputGio (file));
            } catch (Error e) {
                throw new ParseError.PARSE_ERROR (_("Failed to open File."));
            }
        }

        public abstract string[] get_sheet_names () throws ParseError;
        public abstract void parse (int sheet_index, uint max_columns, HashTable<uint, Column> columns) throws ParseError;
    }

    private class ODSParser : SpreadsheetParserInternal {
        public ODSParser (File file) throws ParseError {
            base (file);
        }

        public override string[] get_sheet_names () throws ParseError {
            Xml.Doc* doc = null;
            Xml.XPath.Context* ctx = null;
            Xml.XPath.Object* tables = null;

            try {
                var content = input.child_by_name ("content.xml");
                if (content == null)
                    throw new ParseError.PARSE_ERROR ("ODS file does not contain content.xml");

                char* data = content.read ((size_t) content.size, null);
                if (data == null)
                    throw new ParseError.PARSE_ERROR ("Failed to read content.xml");

                doc = Xml.Parser.parse_memory ((string) data, (int) content.size);
                if (doc == null)
                    throw new ParseError.INVALID ("content.xml is not valid xml");

                ctx = new Xml.XPath.Context (doc);
                if (ctx == null)
                    throw new ParseError.INVALID ("failed to parse xml");

                ctx->register_ns ("table", ODS_TABLE_NAMESPACE);

                tables = ctx->eval_expression ("//table:table");
                if (tables == null)
                    throw new ParseError.INVALID ("failed to parse xml");

                var nodes = tables->nodesetval;
                if (nodes == null)
                    throw new ParseError.INVALID ("ODS file does not contain sheets");

                int n_nodes = nodes->length ();
                string[] names = new string[n_nodes];

                for (int i = 0; i < n_nodes; i++) {
                    names[i] = nodes->item (i)->get_ns_prop ("name", ODS_TABLE_NAMESPACE);
                }

                return (owned) names;
            } finally {
                if (tables != null) delete tables;
                if (ctx != null) delete ctx;
                if (doc != null) delete doc;
            }
        }

        private string extract_cell_text (Xml.Node* cell) {
            var result = new StringBuilder ();
            for (Xml.Node* node = cell->children; node != null; node = node->next) {
                if (node->type == Xml.ElementType.TEXT_NODE && node->content != null) {
                    result.append (node->content);
                } else if (node->type == Xml.ElementType.ELEMENT_NODE) {
                    result.append (extract_cell_text (node));
                }
            }
            return result.free_and_steal ();
        }

        public override void parse (int sheet_index, uint max_columns, HashTable<uint, Column> columns) throws ParseError {
            Xml.Doc* doc = null;
            Xml.XPath.Context* ctx = null;
            Xml.XPath.Object* tables = null;

            try {
                var content = input.child_by_name ("content.xml");
                if (content == null)
                    throw new ParseError.PARSE_ERROR ("ODS file does not contain content.xml");

                char* data = content.read ((size_t) content.size, null);
                if (data == null)
                    throw new ParseError.PARSE_ERROR ("Failed to read content.xml");

                doc = Xml.Parser.parse_memory ((string) data, (int) content.size);
                if (doc == null)
                    throw new ParseError.INVALID ("content.xml is not valid xml");

                ctx = new Xml.XPath.Context (doc);
                if (ctx == null)
                    throw new ParseError.INVALID ("failed to parse xml");

                ctx->register_ns ("table", ODS_TABLE_NAMESPACE);

                tables = ctx->eval_expression ("//table:table");
                if (tables == null)
                    throw new ParseError.INVALID ("failed to parse xml");

                var sheets = tables->nodesetval;
                if (sheets == null)
                    throw new ParseError.INVALID ("ODS file does not contain sheets");

                if (sheet_index > sheets->length ())
                    throw new ParseError.INVALID ("sheet index out of range");

                Xml.Node* sheet = sheets->item (sheet_index);
                if (sheet == null)
                    throw new ParseError.INVALID ("failed to parse xml");

                int array_size = columns[0].data.length, value_size = 0;
                int current_col, repeat_count;
                unowned Column column;
                string cell_text;

                for (Xml.Node* row = sheet->children; row != null; row = row->next) {
                    if (row->type != Xml.ElementType.ELEMENT_NODE) continue;
                    if (row->name != "table-row") continue;

                    current_col = 0;

                    // if we reach capacity, grow the arrays.
                    if (value_size == array_size) {
                        array_size *= 2;
                        columns.for_each ((key, column) => {
                            column.data.resize (array_size);
                        });
                    }

                    for (Xml.Node* cell = row->children; cell != null; cell = cell->next) {
                        if (cell->type != Xml.ElementType.ELEMENT_NODE) continue;
                        if (cell->name != "table-cell") continue;

                        // Get repeat count
                        string? repeat_str = cell->get_prop ("number-columns-repeated");
                        repeat_count = repeat_str != null ? int.parse (repeat_str) : 1;
                        if (repeat_count <= 0) repeat_count = 1;

                        cell_text = extract_cell_text (cell);

                        // Process repeated cells
                        for (int count = 0; count < repeat_count; count++) {
                            if (current_col > max_columns) break;

                            if (columns.contains (current_col)) {
                                column = columns.lookup (current_col);
                                if (!try_evaluate_string (cell_text, out column.data[value_size])) {
                                    if (value_size == 0) {
                                        column.header = cell_text.strip ();
                                    } else {
                                        break;
                                    }
                                }
                            }
                            current_col++;
                        }
                    }

                    value_size++;
                }

                columns.for_each ((key, column) => {
                    column.data.resize (value_size);
                });
            } finally {
                if (tables != null) delete tables;
                if (ctx != null) delete ctx;
                if (doc != null) delete doc;
            }
        }
    }

    private class XLSXParser : SpreadsheetParserInternal {
        string[] shared_strings;

        public XLSXParser (File file) throws ParseError {
            base (file);
        }

        public override string[] get_sheet_names () throws ParseError {
            Xml.Doc* doc = null;
            Xml.XPath.Context* ctx = null;
            Xml.XPath.Object* result = null;

            try {
                var workbook = input.child_by_aname ({"xl", "workbook.xml"});
                if (workbook == null)
                    throw new ParseError.PARSE_ERROR ("ODS file does not contain xl/workbook.xml");

                char* data = workbook.read ((size_t) workbook.size, null);
                if (data == null)
                    throw new ParseError.PARSE_ERROR ("Failed to read xl/workbook.xml");

                doc = Xml.Parser.parse_memory ((string) data, (int) workbook.size);
                if (doc == null)
                    throw new ParseError.INVALID ("xl/workbook.xml is not valid xml");

                ctx = new Xml.XPath.Context (doc);
                if (ctx == null)
                    throw new ParseError.INVALID ("failed to parse xml");

                ctx->register_ns ("main", XLSX_MAIN_NAMESPACE);

                result = ctx->eval_expression ("//main:sheet");
                if (result == null)
                    throw new ParseError.INVALID ("failed to parse xml");

                var nodes = result->nodesetval;
                if (nodes == null)
                    throw new ParseError.INVALID ("XLSX file does not contain sheets");

                int n_nodes = nodes->length ();
                string[] names = new string[n_nodes];

                for (int i = 0; i < n_nodes; i++) {
                    names[i] = nodes->item (i)->get_prop ("name");
                }

                return (owned) names;
            } finally {
                if (result != null) delete result;
                if (ctx != null) delete ctx;
                if (doc != null) delete doc;
            }
        }

        private void load_shared_strings (int sheet_index) throws ParseError {
            Xml.Doc* doc = null;
            Xml.XPath.Context* ctx = null;
            Xml.XPath.Object* result = null;

            try {
                var shared_strings_file = input.child_by_aname ({"xl", "sharedStrings.xml"});
                if (shared_strings_file == null)
                    throw new ParseError.PARSE_ERROR ("ODS file does not contain xl/sharedStrings.xml");

                char* data = shared_strings_file.read ((size_t) shared_strings_file.size, null);
                if (data == null)
                    throw new ParseError.PARSE_ERROR ("Failed to read xl/sharedStrings.xml");

                doc = Xml.Parser.parse_memory ((string) data, (int) shared_strings_file.size);
                if (doc == null)
                    throw new ParseError.INVALID ("xl/sharedStrings.xml is not valid xml");

                ctx = new Xml.XPath.Context (doc);
                if (ctx == null)
                    throw new ParseError.INVALID ("failed to parse xml");

                ctx->register_ns ("main", XLSX_MAIN_NAMESPACE);

                result = ctx->eval_expression ("//main:t");
                if (result == null)
                    throw new ParseError.INVALID ("failed to parse xml");

                var nodes = result->nodesetval;
                if (nodes == null)
                    throw new ParseError.INVALID ("XLSX file does not contain shared strings");

                int n_strings = nodes->length ();
                shared_strings = new string[n_strings];

                for (int i = 0; i < n_strings; i++) {
                    shared_strings[i] = nodes->item (i)->children->content;
                }
            } finally {
                if (result != null) delete result;
                if (ctx != null) delete ctx;
                if (doc != null) delete doc;
            }
        }

        public override void parse (int sheet_index, uint max_columns, HashTable<uint, Column> columns) throws ParseError {
            Xml.Doc* doc = null;
            Xml.XPath.Context* ctx = null;
            Xml.XPath.Object* sheet = null;

            try {
                load_shared_strings (sheet_index);

                string sheet_name = "sheet%d.xml".printf (sheet_index + 1);
                var worksheet = input.child_by_aname ({"xl", "worksheets", sheet_name});
                if (worksheet == null)
                    throw new ParseError.PARSE_ERROR ("XLSX file does not contain xl/worksheets/%s".printf (sheet_name));

                char* data = worksheet.read ((size_t) worksheet.size, null);
                if (data == null)
                    throw new ParseError.PARSE_ERROR ("Failed to read xl/worksheets/%s".printf (sheet_name));

                doc = Xml.Parser.parse_memory ((string) data, (int) worksheet.size);
                if (doc == null)
                    throw new ParseError.INVALID ("xl/sharedStrings.xml is not valid xml");

                ctx = new Xml.XPath.Context (doc);
                if (ctx == null)
                    throw new ParseError.INVALID ("failed to parse xml");

                ctx->register_ns ("main", XLSX_MAIN_NAMESPACE);

                sheet = ctx->eval_expression ("//main:row");
                if (sheet == null)
                    throw new ParseError.INVALID ("failed to parse xml");

                int array_size = columns[0].data.length, value_size = 0;
                int current_col;
                unowned Column column;
                string? r;
                unowned string cell_text = "";

                for (int i = 0; i < sheet->nodesetval->length (); i++) {
                    Xml.Node* row = sheet->nodesetval->item (i);

                    // if we reach capacity, grow the arrays.
                    if (value_size == array_size) {
                        array_size *= 2;
                        columns.for_each ((key, column) => {
                            column.data.resize (array_size);
                        });
                    }

                    for (Xml.Node* cell = row->children; cell != null; cell = cell->next) {
                        r = cell->get_prop ("r");

                        StringBuilder builder = new StringBuilder ();
                        for (int j = 0; j < r.length; j++) {
                            if (!r[j].isdigit ()) builder.append_c (r[j]);
                        }
                        current_col = Tools.alpha_to_int (builder.free_and_steal ());

                        if (!columns.contains (current_col)) continue;

                        for (Xml.Node* child = cell->children; child != null; child = child->next) {
                            if (child->name == "v") {
                                cell_text = child->children->content;
                                break;
                            }
                        }

                        string? t = cell->get_prop ("t");
                        if (t != null && t == "s") {
                            cell_text = shared_strings[int.parse (cell_text)];
                        }

                        column = columns.lookup (current_col);
                        if (!try_evaluate_string (cell_text, out column.data[value_size])) {
                            if (value_size == 0) {
                                column.header = cell_text.strip ();
                            } else {
                                break;
                            }
                        }
                    }

                    value_size++;
                }

                columns.for_each ((key, column) => {
                    column.data.resize (value_size);
                });
            } finally {
                if (sheet != null) delete sheet;
                if (ctx != null) delete ctx;
                if (doc != null) delete doc;
            }
        }
    }

    public class SpreadsheetReader : Object {
        private SpreadsheetParserInternal parser;
        private string[] sheet_names;
        private HashTable<uint, Column> columns;
        private uint n_used_indices;

        public SpreadsheetReader (File file) throws ParseError {
            if (file.get_path ().has_suffix (".ods")) {
                this.parser = new ODSParser (file);
            } else {
                this.parser = new XLSXParser (file);
            }

            this.sheet_names = parser.get_sheet_names ();
            columns = new HashTable<uint, Column> (null, null);
        }

        public unowned string[] get_sheet_names () {
            return sheet_names;
        }

        private void request_column (uint index) {
            if (!columns.contains (index)) columns.insert (index, new Column ());

            columns[index].requests++;
            n_used_indices = uint.max (n_used_indices, index);
        }

        public void parse (ImportSettings settings, StyleParameters style, ItemList itemlist) throws ParseError {
            ColumnsItemSettings item_settings = ColumnsItemSettings ();
            var items = settings.get_value ("items");

            var iter = items.iterator ();
            for (int i = 0; i < iter.n_children (); i++) {
                item_settings.load_from_variant (iter.next_value ());

                request_column (item_settings.column_y);
                if (!item_settings.single_column) request_column (item_settings.column_x);
                if (item_settings.use_yerr) request_column (item_settings.yerr_index);
                if (item_settings.use_xerr) request_column (item_settings.xerr_index);
            }

            parser.parse (settings.get_int ("sheet-index"), n_used_indices, columns);

            iter = items.iterator ();
            for (int i = 0; i < iter.n_children (); i++) {
                item_settings.load_from_variant (iter.next_value ());

                unowned string ylabel = columns[item_settings.column_y].header;
                double[] ydata = columns[item_settings.column_y].get_data ();

                double[]? xerr = item_settings.use_xerr ? columns[item_settings.xerr_index].get_data () : null;
                double[]? yerr = item_settings.use_yerr ? columns[item_settings.yerr_index].get_data () : null;

                unowned string xlabel;
                double[] xdata;
                if (item_settings.single_column) {
                    xlabel = "";
                    try {
                        Expression equation = expression_to_ast (item_settings.equation);
                        xdata = MathTools.evaluate_expression (equation, ydata.length, "n");
                    } catch (MathError e) {
                        throw new ParseError.PARSE_ERROR (e.message);
                    }
                } else {
                    xlabel = columns[item_settings.column_x].header;
                    xdata = columns[item_settings.column_x].get_data ();
                }

                Item item = ItemFactory.new_data_item (style, (owned) xdata, (owned) ydata, (owned) xerr, (owned) yerr);
                item.xlabel = xlabel;
                item.ylabel = ylabel;
                item.name = settings.filename;
                itemlist.add (item);
            }
        }
    }
}
