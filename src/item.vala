namespace Graphs {
    public interface Item : Object {
        public abstract string name { get; set; default = ""; }
        public abstract string color { get; set; default = ""; }
        public abstract double alpha { get; set; default = 1; }
        public abstract bool selected { get; set; default = true; }
        public abstract string xlabel { get; set; default = ""; }
        public abstract string ylabel { get; set; default = ""; }
        public abstract int xposition { get; set; default = 0; }
        public abstract int yposition { get; set; default = 0; }
    }
}
