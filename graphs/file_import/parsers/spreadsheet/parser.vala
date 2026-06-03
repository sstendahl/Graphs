// SPDX-License-Identifier: GPL-3.0-or-later
namespace Graphs {
    private const string ODS_TABLE_NAMESPACE = "urn:oasis:names:tc:opendocument:xmlns:table:1.0";

    private abstract class SpreadsheetParserInternal {
        protected Gsf.InfileZip input;
    }

    private class ODSParser : SpreadsheetParserInternal {
        public ODSParser (File file) throws Error {
            this.input = new Gsf.InfileZip (new Gsf.InputGio (file));
        }

        public string[] get_sheet_names () throws Error {
            var content = input.child_by_name ("content.xml");

            return {};
        }
    }

    public class SpreadsheetParser : Object {
        private ImportSettings settings;
        private SpreadsheetParserInternal parser;

        public SpreadsheetParser (ImportSettings settings) throws Error {
            this.settings = settings;

            if (settings.file.get_path ().has_suffix (".ods")) {
                parser = new ODSParser (settings.file);
            }
        }

    }
}
