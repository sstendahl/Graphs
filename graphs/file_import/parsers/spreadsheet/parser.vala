// SPDX-License-Identifier: GPL-3.0-or-later
namespace Graphs {
    private const string ODS_TABLE_NAMESPACE = "urn:oasis:names:tc:opendocument:xmlns:table:1.0";
    private const string XLSX_MAIN_NAMESPACE = "http://schemas.openxmlformats.org/spreadsheetml/2006/main";

    private abstract class SpreadsheetParserInternal {
        protected Gsf.InfileZip input;

        protected SpreadsheetParserInternal (File file) throws Error {
            this.input = new Gsf.InfileZip (new Gsf.InputGio (file));
        }

        public abstract string[] get_sheet_names () throws Error;
        public abstract void parse () throws Error;
    }

    private class ODSParser : SpreadsheetParserInternal {
        public ODSParser (File file) throws Error {
            base (file);
        }

        public override string[] get_sheet_names () throws Error {
            var content = input.child_by_name ("content.xml");

            char* data = content.read ((size_t) content.size, null);
            Xml.Doc* doc = Xml.Parser.parse_memory ((string) data, (int) content.size);

            var names = new Gee.HashSet<string> ();

            Xml.XPath.Context* ctx = new Xml.XPath.Context (doc);
            ctx->register_ns ("table", ODS_TABLE_NAMESPACE);

            Xml.XPath.Object* result = ctx->eval_expression ("//table:table");

            if (result != null && result->nodesetval != null) {
                var nodes = result->nodesetval;

                for (int i = 0; i < nodes->length (); i++) {
                    names.add (nodes->item (i)->get_ns_prop ("name", ODS_TABLE_NAMESPACE));
                }
            }

            delete result;
            delete ctx;
            delete doc;

            return names.to_array ();
        }

        public override void parse () {
        }
    }

    private class XLSXParser : SpreadsheetParserInternal {
        public XLSXParser (File file) throws Error {
            base (file);
        }

        public override string[] get_sheet_names () throws Error {
            var workbook = input.child_by_aname ({"xl", "workbook.xml"});

            char* data = workbook.read ((size_t) workbook.size, null);
            Xml.Doc* doc = Xml.Parser.parse_memory ((string) data, (int) workbook.size);

            var names = new Gee.HashSet<string> ();

            Xml.XPath.Context* ctx = new Xml.XPath.Context (doc);
            ctx->register_ns ("main", XLSX_MAIN_NAMESPACE);

            Xml.XPath.Object* result = ctx->eval_expression ("//main:sheet");

            if (result != null && result->nodesetval != null) {
                var nodes = result->nodesetval;

                for (int i = 0; i < nodes->length (); i++) {
                    names.add (nodes->item (i)->get_prop ("name"));
                }
            }

            delete result;
            delete ctx;
            delete doc;

            return names.to_array ();
        }

        public override void parse () {
        }
    }

    public class SpreadsheetParser : Object {
        private SpreadsheetParserInternal parser;
        private string[] sheet_names;

        public SpreadsheetParser (File file) throws Error {
            if (file.get_path ().has_suffix (".ods")) {
                this.parser = new ODSParser (file);
            } else {
                this.parser = new XLSXParser (file);
            }

            this.sheet_names = parser.get_sheet_names ();
        }

        public unowned string[] get_sheet_names () {
            return sheet_names;
        }

    }
}
