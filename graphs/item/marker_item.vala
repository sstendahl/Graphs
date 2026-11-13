// SPDX-License-Identifier: GPL-3.0-or-later
namespace Graphs {
    public enum MarkerDirection {
        HORIZONTAL,
        VERTICAL
    }

    public class MarkerItem : Item {
        public MarkerDirection direction { get; set; default = HORIZONTAL; }
        public double anchor { get; set; default = 0; }
        public double linewidth { get; set; default = 3; }
        public EquationLinestyle linestyle { get; set; default = SOLID; }

        construct {
            typename = _("Marker");
        }

        public MarkerItem (StyleParameters parameters, MarkerDirection direction, double anchor) {
            Object (
                direction: direction,
                anchor: anchor
            );
            override (parameters);
        }

        private static StylePropertyBinding[] bindings = {
            {"color", (s) => s.axis_color}
        };

        protected override unowned StylePropertyBinding[]? get_property_bindings () {
            return bindings;
        }
    }
}
