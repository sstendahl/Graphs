// SPDX-License-Identifier: GPL-3.0-or-later
namespace Graphs {
    public class TextItem : Item {
        public double xanchor { get; set; default = 0; }
        public double yanchor { get; set; default = 0; }
        public string text { get; set; default = ""; }
        public double size { get; set; default = 12; }
        public int rotation { get; set; default = 0; }

        construct {
            typename = _("Label");
        }

        public TextItem (StyleParameters parameters, double xanchor, double yanchor, string text) {
            Object (
                xanchor: xanchor,
                yanchor: yanchor,
                text: text
            );
            override (parameters);
        }

        private static StylePropertyBinding[] bindings = {
            {"size", (s) => (double) s.font.get_size () / Pango.SCALE},
            {"color", (s) => s.text_color}
        };

        protected override unowned StylePropertyBinding[]? get_property_bindings () {
            return bindings;
        }
    }
}
