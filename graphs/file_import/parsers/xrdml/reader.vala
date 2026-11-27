// SPDX-License-Identifier: GPL-3.0-or-later
namespace Graphs {
    private class XrdmlReader : Object {
        public bool has_q { get; private set; default = false; }
        public bool has_counting_time { get; private set; default = false; }
        public int n_scans { get { return scans.length; } }

        private XrdmlScan[] scans = {};

        public XrdmlReader (File file) throws ParseError {
            uint8[] contents;
            try {
                file.load_contents (null, out contents, null);
            } catch (Error e) {
                throw new ParseError.INVALID (_("Failed to open File."));
            }

            int options = Xml.ParserOption.NONET | Xml.ParserOption.NOERROR
                | Xml.ParserOption.NOWARNING | Xml.ParserOption.HUGE;
            Xml.Doc* doc = Xml.Parser.read_memory ((string) contents, contents.length, null, null, options);
            if (doc == null) throw new ParseError.INVALID (_("The file is not a valid XRDML file"));

            try {
                Xml.Node* root = doc->get_root_element ();
                for (Xml.Node* measurement = root->children; measurement != null; measurement = measurement->next) {
                    if (!XrdmlScan.is_element (measurement, "xrdMeasurement")) continue;
                    for (Xml.Node* scan = measurement->children; scan != null; scan = scan->next) {
                        if (XrdmlScan.is_element (scan, "scan")) scans += new XrdmlScan (measurement, scan);
                    }
                }
            } finally {
                delete doc;
            }
            if (scans.length == 0) throw new ParseError.INVALID (_("The file does not contain any data points"));
            describe_scans ();

            foreach (XrdmlScan scan in scans) {
                if (scan.q != null) has_q = true;
                if (scan.counting_time > 0) has_counting_time = true;
            }
        }

        public ItemList parse (ImportSettings settings, StyleParameters style) {
            bool use_q = settings.get_string ("x-axis") == "q-space";
            bool use_cps = settings.get_string ("intensity") == "cps";
            bool[] selected = (bool[]) settings.get_value ("scans");

            var items = new ItemList ();
            for (int i = 0; i < scans.length; i++) {
                if (!selected[i]) continue;
                string name = settings.filename;
                if (scans[i].description != null) {
                    name = "%s (%s)".printf (name, scans[i].description);
                } else if (scans.length > 1) {
                    name = "%s - %d".printf (name, i + 1);
                }
                items.add (scans[i].create_item (style, name, use_q, use_cps));
            }
            return items;
        }

        public unowned string? get_description (int index) {
            return scans[index].description;
        }

        // find proper name for the scans using the varying parameter
        private void describe_scans () {
            if (scans.length < 2) return;

            var descriptions = new string[scans.length];
            foreach (unowned string axis in scans[0].fixed_axes) {
                bool changes = false;
                foreach (XrdmlScan scan in scans) {
                    if (scan.get_fixed (axis) != scans[0].get_fixed (axis)) changes = true;
                }
                if (!changes) continue;

                for (int i = 0; i < scans.length; i++) {
                    string? fixed = scans[i].get_fixed (axis);
                    if (fixed == null) return;
                    descriptions[i] = descriptions[i] == null ? fixed : "%s, %s".printf (descriptions[i], fixed);
                }
            }

            var unique = new GenericSet<string> (str_hash, str_equal);
            foreach (unowned string? description in descriptions) {
                if (description == null || description in unique) return;
                unique.add (description);
            }
            for (int i = 0; i < scans.length; i++) scans[i].description = descriptions[i];
        }
    }

    private class XrdmlScan {
        private const string TWO_THETA_LABEL = "Scattering Angle 2$\\theta$ ($\\degree$)";
        private const string OMEGA_LABEL = "Rocking Angle $\\omega$ ($\\degree$)";
        private const string INCIDENCE_LABEL = "Incidence Angle $\\omega$ ($\\degree$)";
        private const string Q_LABEL = "Scattering vector q (Å$^{-1}$)";
        private const string QZ_LABEL = "Scattering vector q$_z$ (Å$^{-1}$)";
        private const string QX_LABEL = "In-plane scattering vector q$_x$ (Å$^{-1}$)";

        public double[]? q = null;
        public double counting_time = 0;
        public string? description = null;

        public string[] fixed_axes = {};
        private string[] fixed_positions = {};

        private double[] positions;
        private string position_label = "";
        private string q_label = "";
        private double[] intensities;
        private bool in_cps = false;

        public XrdmlScan (Xml.Node* measurement, Xml.Node* scan) throws ParseError {
            Xml.Node* data_points = get_child (scan, "dataPoints");
            if (data_points == null) throw new ParseError.INVALID (_("The file does not contain any data points"));

            read_intensities (data_points);
            read_positions (scan, data_points);
            read_fixed_positions (data_points);
            bool reflection = measurement->get_prop ("sampleMode") != "Transmission";
            calculate_q (data_points, get_wavelength (measurement), reflection);
        }

        public string? get_fixed (string axis) {
            for (int i = 0; i < fixed_axes.length; i++) {
                if (fixed_axes[i] == axis) return fixed_positions[i];
            }
            return null;
        }

        public DataItem create_item (StyleParameters style, string name, bool use_q, bool use_cps) {
            use_q = use_q && q != null;
            double[] xdata = use_q ? q : positions;
            double[] ydata = intensities;
            bool ydata_in_cps = in_cps;
            if (counting_time > 0 && use_cps != in_cps) {
                for (int i = 0; i < ydata.length; i++) {
                    ydata[i] = use_cps ? ydata[i] / counting_time : ydata[i] * counting_time;
                }
                ydata_in_cps = use_cps;
            }

            return new DataItem (style, (owned) xdata, (owned) ydata) {
                name = name,
                xlabel = use_q ? q_label : position_label,
                ylabel = ydata_in_cps ? _("Intensity (cps)") : _("Intensity (counts)"),
            };
        }

        private void read_intensities (Xml.Node* data_points) throws ParseError {
            // older files use <intensities>, newer file use <counts>
            Xml.Node* node = get_child (data_points, "intensities");
            if (node != null) {
                intensities = parse_values (node);
                in_cps = node->get_prop ("unit") == "cps";
            } else {
                node = get_child (data_points, "counts");
                if (node == null) throw new ParseError.INVALID (_("The file does not contain any intensities"));
                intensities = parse_values (node);

                double[]? attenuation = get_values (data_points, "beamAttenuationFactors");
                if (attenuation != null && attenuation.length == intensities.length) {
                    for (int i = 0; i < intensities.length; i++) intensities[i] *= attenuation[i];
                }
            }
            if (intensities.length == 0) throw new ParseError.INVALID (_("The file does not contain any intensities"));

            double time = get_number (data_points, "commonCountingTime");
            if (time > 0) counting_time = time;
        }

        private void read_positions (Xml.Node* scan, Xml.Node* data_points) throws ParseError {
            string axis = scan->get_prop ("scanAxis") ?? "";
            string? label = null;
            if (axis.has_prefix ("2Theta") || axis == "Gonio") {
                axis = "2Theta";
                label = TWO_THETA_LABEL;
            } else if (axis == "Omega") {
                label = OMEGA_LABEL;
            } else if (axis.has_prefix ("Omega")) {
                // coupled scan, so not a rocking curve
                axis = "Omega";
                label = INCIDENCE_LABEL;
            }

            Xml.Node* node = get_positions_node (data_points, axis);
            double[]? values = get_positions (node, intensities.length);
            if (values == null) throw new ParseError.INVALID (_("No positions found for the scan axis"));
            positions = values;
            string unit = node->get_prop ("unit") ?? "";
            if (unit == "deg") unit = "$\\degree$";
            position_label = label ?? "%s (%s)".printf (axis, unit);
        }

        private void read_fixed_positions (Xml.Node* data_points) throws ParseError {
            int size = intensities.length;
            for (Xml.Node* node = data_points->children; node != null; node = node->next) {
                if (!is_element (node, "positions")) continue;
                double[]? values = get_positions (node, size);
                if (values == null || varies (values)) continue;

                string axis = node->get_prop ("axis") ?? "";
                string unit = node->get_prop ("unit") ?? "";
                unit = unit == "deg" ? "°" : " " + unit;
                fixed_axes += axis;
                fixed_positions += "%s = %s%s".printf (get_symbol (axis), format_number (values[0]), unit.chomp ());
            }

            // omega offset of a coupled scan, e.g. wobble scans
            double[]? two_theta = get_positions (get_positions_node (data_points, "2Theta"), size);
            double[]? omega = get_positions (get_positions_node (data_points, "Omega"), size);
            if (two_theta == null || omega == null || !varies (two_theta)) return;
            var offsets = new double[size];
            for (int i = 0; i < size; i++) offsets[i] = Math.round ((omega[i] - two_theta[i] / 2) * 1e4);
            if (varies (offsets)) return;
            fixed_axes += "offset";
            fixed_positions += "ω − θ = %s°".printf (format_number (omega[0] - two_theta[0] / 2));
        }

        private void calculate_q (Xml.Node* data_points, double wavelength, bool reflection) throws ParseError {
            int size = intensities.length;
            double[]? two_theta = get_positions (get_positions_node (data_points, "2Theta"), size);
            double[]? omega = get_positions (get_positions_node (data_points, "Omega"), size);
            if (two_theta == null || wavelength.is_nan () || wavelength <= 0) return;

            bool theta_scan = varies (two_theta);
            // without omega, or in transmission, we only get |q|
            bool only_length = omega == null || !reflection;
            if (!theta_scan && (only_length || !varies (omega))) return;

            double k0 = 2 * Math.PI / wavelength;
            q = new double[size];
            for (int i = 0; i < size; i++) {
                double tth = to_radians (two_theta[i]);
                if (only_length) {
                    q[i] = 2 * k0 * Math.sin (tth / 2);
                    continue;
                }
                double alpha_i = to_radians (omega[i]);
                double alpha_f = tth - alpha_i;
                if (theta_scan) {
                    q[i] = k0 * (Math.sin (alpha_i) + Math.sin (alpha_f));
                } else {
                    q[i] = k0 * (Math.cos (alpha_f) - Math.cos (alpha_i));
                }
            }

            if (only_length) {
                q_label = Q_LABEL;
            } else {
                q_label = theta_scan ? QZ_LABEL : QX_LABEL;
            }
        }

        private static double get_wavelength (Xml.Node* measurement) throws ParseError {
            Xml.Node* used = get_child (measurement, "usedWavelength");
            if (used == null) return double.NAN;

            double k_alpha1 = get_line (used, "kAlpha1");
            double k_alpha2 = get_line (used, "kAlpha2");
            double ratio = get_number (used, "ratioKAlpha2KAlpha1");

            string intended = (used->get_prop ("intended") ?? "").down ().replace (" ", "").replace ("-", "");
            double wavelength = double.NAN;
            switch (intended) {
                case "kalpha1": wavelength = k_alpha1; break;
                case "kalpha2": wavelength = k_alpha2; break;
                case "kbeta": wavelength = get_line (used, "kBeta"); break;
            }
            if (!wavelength.is_nan ()) return wavelength;

            // weighted average of both K-alpha lines
            if (!k_alpha2.is_nan () && ratio > 0) return (k_alpha1 + ratio * k_alpha2) / (1 + ratio);
            return k_alpha1;
        }

        private static double get_line (Xml.Node* used_wavelength, string name) throws ParseError {
            Xml.Node* node = get_child (used_wavelength, name);
            if (node == null) return double.NAN;
            double[] values = parse_values (node);
            if (values.length == 0) return double.NAN;
            string? unit = node->get_prop ("unit");
            return unit == "nm" || unit == "nanometer" ? values[0] * 10 : values[0];
        }

        private static Xml.Node* get_positions_node (Xml.Node* data_points, string axis) {
            for (Xml.Node* node = data_points->children; node != null; node = node->next) {
                if (is_element (node, "positions") && node->get_prop ("axis") == axis) return node;
            }
            return null;
        }

        private static double[]? get_positions (Xml.Node* node, int size) throws ParseError {
            if (node == null) return null;

            double[]? values = get_values (node, "listPositions");
            if (values != null) return values.length == size ? values : null;

            double start = get_number (node, "startPosition");
            double end = get_number (node, "endPosition");
            if (start.is_nan () || end.is_nan ()) {
                start = end = get_number (node, "commonPosition");
                if (start.is_nan ()) return null;
            }

            values = new double[size];
            double step = size > 1 ? (end - start) / (size - 1) : 0;
            for (int i = 0; i < size; i++) values[i] = start + i * step;
            return values;
        }

        private static string get_symbol (string axis) {
            switch (axis) {
                case "2Theta": return "2θ";
                case "Omega": return "ω";
                case "Phi": return "φ";
                case "Chi": return "χ";
                case "Psi": return "ψ";
                default: return axis;
            }
        }

        // up to four decimals, without trailing zeros
        private static string format_number (double value) {
            string text = "%.4f".printf (Math.round (value * 1e4) / 1e4 + 0.0);
            if (text.contains (".") || text.contains (",")) {
                while (text.has_suffix ("0")) text = text.substring (0, text.length - 1);
                if (text.has_suffix (".") || text.has_suffix (",")) text = text.substring (0, text.length - 1);
            }
            return text.replace ("-", "−");
        }

        private static bool varies (double[] values) {
            foreach (double value in values) {
                if (value != values[0]) return true;
            }
            return false;
        }

        private static double to_radians (double degrees) {
            return degrees * Math.PI / 180;
        }

        public static bool is_element (Xml.Node* node, string name) {
            return node->type == Xml.ElementType.ELEMENT_NODE && node->name == name;
        }

        private static Xml.Node* get_child (Xml.Node* parent, string name) {
            for (Xml.Node* node = parent->children; node != null; node = node->next) {
                if (is_element (node, name)) return node;
            }
            return null;
        }

        private static double get_number (Xml.Node* parent, string name) throws ParseError {
            double[]? values = get_values (parent, name);
            return values != null && values.length > 0 ? values[0] : double.NAN;
        }

        private static double[]? get_values (Xml.Node* parent, string name) throws ParseError {
            Xml.Node* node = get_child (parent, name);
            return node == null ? null : parse_values (node);
        }

        private static double[] parse_values (Xml.Node* node) throws ParseError {
            string[] words = node->get_content ().split_set (" \t\r\n");
            var values = new double[words.length];
            int n_values = 0;
            foreach (unowned string word in words) {
                if (word == "") continue;
                double value;
                if (!double.try_parse (word, out value)) {
                    throw new ParseError.INVALID (_("The file is not a valid XRDML file"));
                }
                values[n_values++] = value;
            }
            values.resize (n_values);
            return values;
        }
    }
}
