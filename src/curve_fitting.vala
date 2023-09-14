// SPDX-License-Identifier: GPL-3.0-or-later
using Adw;

namespace Graphs {
    public class FittingParameter : Object {
        public string name { get; construct set; default = ""; }
        public double initial { get; construct set; default = 1; }
        public double lower_bound { get; construct set; default = 0; }
        public double upper_bound { get; construct set; default = 100; }
    }
}
