// SPDX-License-Identifier: GPL-3.0-or-later
namespace Graphs {
    public class ItemFactory : Object {
        public static DataItem new_data_item (StyleParameters parameters, owned double[] xdata, owned double[] ydata, owned double[]? xerr = null, owned double[]? yerr = null) {
            var item = new DataItem () {
                data = new DataHolder ((owned) xdata, (owned) ydata, (owned) xerr, (owned) yerr),
            };
            item.override (parameters);
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
            item.override (parameters);
            return item;
        }

        public static EquationItem new_equation_item (StyleParameters parameters, Ast equation) {
            var item = new EquationItem () {
                equation = equation,
            };
            item.override (parameters);
            return item;
        }

        public static TextItem new_text_item (StyleParameters parameters, double xanchor, double yanchor, string text) {
            var item = new TextItem () {
                xanchor = xanchor,
                yanchor = yanchor,
                text = text,
            };
            item.override (parameters);
            return item;
        }

        public static FillItem new_fill_item (StyleParameters parameters, owned double[] xdata, owned double[] lower, owned double[] upper) {
            var item = new FillItem () {
                data = new FillHolder ((owned) xdata, (owned) lower, (owned) upper),
            };
            item.override (parameters);
            return item;
        }
    }
}
