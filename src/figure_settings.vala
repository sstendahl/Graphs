// SPDX-License-Identifier: GPL-3.0-or-later
namespace Graphs {
    public class FigureSettings : Object {

        public string title { get; set; default = ""; }
        public string bottom_label { get; set; default = ""; }
        public string left_label { get; set; default = ""; }
        public string top_label { get; set; default = ""; }
        public string right_label { get; set; default = ""; }

        public int bottom_scale { get; set; default = 0; }
        public int left_scale { get; set; default = 0; }
        public int top_scale { get; set; default = 0; }
        public int right_scale { get; set; default = 0; }

        public bool legend { get; set; default = true; }
        public int legend_position { get; set; default = 0; }
        public bool use_custom_style { get; set; default = false; }
        public string custom_style { get; set; default = "adwaita"; }

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

        public FigureSettings (Settings settings) {
            Object (
                bottom_scale: settings.get_enum("bottom-scale"),
                left_scale: settings.get_enum("left-scale"),
                right_scale: settings.get_enum("right-scale"),
                top_scale: settings.get_enum("top-scale"),
                title: settings.get_string("title"),
                bottom_label: settings.get_string("bottom-label"),
                left_label: settings.get_string("left-label"),
                top_label: settings.get_string("top-label"),
                right_label: settings.get_string("right-label"),
                legend: settings.get_boolean("legend"),
                use_custom_style: settings.get_boolean("use-custom-style"),
                legend_position: settings.get_enum("legend-position"),
                custom_style: settings.get_string("custom-style")
            );
        }

        public double[] get_limits () {
            double[] limits = {};
            foreach (string limit_name in limit_names) {
                double limit;
                get (limit_name, out limit);
                limits += limit;
            }
            return limits;
        }

        public void set_limits (double[] limits)
                requires (limits.length == 8)
        {
            for (int i = 0; i < limit_names.length; i++) {
                set (limit_names[i], limits[i]);
            }
        }
    }
}
