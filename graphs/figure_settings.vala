// SPDX-License-Identifier: GPL-3.0-or-later
using Adw;
using Gtk;

namespace Graphs {
    private const string[] LIMIT_NAMES = {
        "min-bottom", "max-bottom", "min-top", "max-top",
        "min-left", "max-left", "min-right", "max-right",
    };

    public class Limits {
        private double[] _values;

        public Limits (double[] values)
            requires (values.length = 8) {
            _values = values;
        }

        public double[] values () {
            return _values;
        }

        public double get (uint i) {
            return _values[i];
        }
    }

    /**
     * Figure settings
     */
    public class FigureSettings : Object {

        public string title { get; set; default = ""; }
        public string bottom_label { get; set; default = ""; }
        public string left_label { get; set; default = ""; }
        public string top_label { get; set; default = ""; }
        public string right_label { get; set; default = ""; }

        public Scale bottom_scale { get; set; default = Scale.LINEAR; }
        public Scale left_scale { get; set; default = Scale.LINEAR; }
        public Scale top_scale { get; set; default = Scale.LINEAR; }
        public Scale right_scale { get; set; default = Scale.LINEAR; }

        public bool legend { get; set; default = true; }
        public LegendPosition legend_position { get; set; default = LegendPosition.BEST; }
        public bool use_custom_style { get; set; default = false; }
        public string custom_style { get; set; default = "Adwaita"; }
        public bool hide_unselected { get; set; default = false; }

        public double min_bottom { get; set; default = 0; }
        public double max_bottom { get; set; default = 1; }
        public double min_left { get; set; default = 0; }
        public double max_left { get; set; default = 10; }
        public double min_top { get; set; default = 0; }
        public double max_top { get; set; default = 1; }
        public double min_right { get; set; default = 0; }
        public double max_right { get; set; default = 10; }

        public double min_selected { get; set; default = 0; }
        public double max_selected { get; set; default = 0; }

        public FigureSettings (GLib.Settings settings) {
            Object (
                bottom_scale: settings.get_enum ("bottom-scale"),
                left_scale: settings.get_enum ("left-scale"),
                right_scale: settings.get_enum ("right-scale"),
                top_scale: settings.get_enum ("top-scale"),
                title: settings.get_string ("title"),
                bottom_label: settings.get_string ("bottom-label"),
                left_label: settings.get_string ("left-label"),
                top_label: settings.get_string ("top-label"),
                right_label: settings.get_string ("right-label"),
                legend: settings.get_boolean ("legend"),
                use_custom_style: settings.get_boolean ("use-custom-style"),
                legend_position: settings.get_enum ("legend-position"),
                custom_style: settings.get_string ("custom-style")
            );
        }

        public Limits get_limits () {
            double[] values = new double[8];
            for (uint i = 0; i < LIMIT_NAMES.length; i++) {
                double limit;
                get (LIMIT_NAMES[i], out limit);
                values[i] = limit;
            }
            return new Limits ((owned) values);
        }

        public void set_limits (Limits limits) {
            for (uint i = 0; i < LIMIT_NAMES.length; i++) {
                set (LIMIT_NAMES[i], limits[i]);
            }
        }

        public void set_selection_range (double minimum, double maximum)
        requires (0 <= minimum <= 1)
        requires (0 <= maximum <= 1)
        requires (minimum <= maximum) {
            this.min_selected = minimum;
            this.max_selected = maximum;
        }
    }
}
