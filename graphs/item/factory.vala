// SPDX-License-Identifier: GPL-3.0-or-later
namespace Graphs {
    public class ItemFactory : Object {
        private static ItemFactory instance;

        construct {
            instance = this;
        }

        protected signal void reset_request (Item item, StyleParameters old_style, StyleParameters new_style);
        protected signal void override_request (Item item, StyleParameters parameters);

        public static void reset_item (Item item, StyleParameters old_style, StyleParameters new_style) {
            instance.reset_request.emit (item, old_style, new_style);
        }

        public static void override_item (Item item, StyleParameters parameters) {
            instance.override_request.emit (item, parameters);
        }

        public static DataItem new_data_item (StyleParameters parameters, owned double[] xdata, owned double[] ydata, owned double[]? xerr = null, owned double[]? yerr = null) {
            var item = new DataItem () {
                data = new DataHolder ((owned) xdata, (owned) ydata, (owned) xerr, (owned) yerr),
            };
            instance.override_request.emit (item, parameters);
            return item;
        }

        public static GeneratedDataItem new_generated_data_item (StyleParameters parameters, Ast equation, string xstart, string xstop, int steps, Scale scale) {
            var item = new GeneratedDataItem () {
                equation = equation,
                xstart = xstart,
                xstop = xstop,
                steps = steps,
                scale = scale,
            };
            instance.override_request.emit (item, parameters);
            return item;
        }

        public static EquationItem new_equation_item (StyleParameters parameters, Ast equation) {
            var item = new EquationItem () {
                equation = equation,
            };
            instance.override_request.emit (item, parameters);
            return item;
        }

        public static TextItem new_text_item (StyleParameters parameters, double xanchor, double yanchor, string text) {
            var item = new TextItem () {
                xanchor = xanchor,
                yanchor = yanchor,
                text = text,
            };
            instance.override_request.emit (item, parameters);
            return item;
        }

        public static FillItem new_fill_item (StyleParameters parameters, owned double[] xdata, owned double[] lower, owned double[] upper) {
            var item = new FillItem () {
                data = new FillHolder ((owned) xdata, (owned) lower, (owned) upper),
            };
            instance.override_request.emit (item, parameters);
            return item;
        }
    }
}
