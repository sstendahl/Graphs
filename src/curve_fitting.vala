// SPDX-License-Identifier: GPL-3.0-or-later
namespace Graphs {
    public class FittingParameter : Object {
        public string name { get; construct set; default = ""; }
        public double initial { get; construct set; default = 1; }
        public string lower_bound { get; construct set; default = "-inf"; }
        public string upper_bound { get; construct set; default = "inf"; }
    }
}
