// SPDX-License-Identifier: GPL-3.0-or-later
namespace Graphs {
    public class Item : Object {
        public string name { get; set; default = ""; }
        public string color { get; set; default = ""; }
        public double alpha { get; set; default = 1; }
        public bool selected { get; set; default = true; }
        public string xlabel { get; set; default = ""; }
        public string ylabel { get; set; default = ""; }
        public int xposition { get; set; default = 0; }
        public int yposition { get; set; default = 0; }

        public string uuid { get; set; default = Uuid.string_random(); }
    }
}
