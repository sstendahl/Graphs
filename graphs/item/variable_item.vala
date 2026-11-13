// SPDX-License-Identifier: GPL-3.0-or-later
namespace Graphs {
    /**
     * A variable that can be used in equations.
     */
    public class VariableItem : Item {
        public const double DEFAULT_VALUE = 1;

        private const uint ANIMATION_FPS = 30;
        private const double ANIMATION_DURATION = 5000;

        public string variable { get; construct set; default = ""; }

        private double _value = DEFAULT_VALUE;
        public double value {
            get { return _value; }
            set {
                if (_value == value) return;
                _value = value;
                // Keep the value within reach of the slider
                if (value < double.min (min, max)) {
                    if (min <= max) min = value;
                    else max = value;
                } else if (value > double.max (min, max)) {
                    if (min <= max) max = value;
                    else min = value;
                }
            }
        }

        public double min { get; set; default = -10; }
        public double max { get; set; default = 10; }
        public double step { get; set; default = 0; }

        private uint _animation_source = 0;
        private int _animation_direction = 1;
        private int64 _animation_time;
        private double _animation_position;

        public signal void animation_changed ();

        construct {
            typename = _("Variable");
            if (name == "") name = variable;
        }

        public VariableItem (string variable, double value = DEFAULT_VALUE) {
            Object (variable: variable, name: variable);
            this.value = value;
        }

        public double get_effective_step () {
            if (step > 0) return step;
            double range = (max - min).abs ();
            if (!(range > 0) || !range.is_finite ()) return 1;
            return Math.pow (10, Math.floor (Math.log10 (range / 100)));
        }

        /**
         * Get the value closest to the given one the slider can take.
         */
        public double snap (double val) {
            double low = double.min (min, max);
            double high = double.max (min, max);
            if (step > 0) {
                val = low + Math.round ((val - low) / step) * step;
                val = double.parse ("%.12g".printf (val));
            } else if (low < high) {
                double decimals = -Math.floor (Math.log10 ((high - low) / 100));
                if (decimals >= 0) {
                    double factor = Math.pow (10, decimals);
                    val = Math.round (val * factor) / factor;
                } else {
                    double factor = Math.pow (10, -decimals);
                    val = Math.round (val / factor) * factor;
                }
            }
            return val.clamp (low, high);
        }

        public void fit_value () {
            if (step > 0) {
                value = snap (value);
            } else {
                value = value.clamp (double.min (min, max), double.max (min, max));
            }
        }

        public bool is_animating () {
            return _animation_source != 0;
        }

        public void start_animation () {
            if (is_animating () || min == max) return;
            _animation_time = get_monotonic_time ();
            _animation_position = value;
            _animation_direction = 1;
            _animation_source = Timeout.add (1000 / ANIMATION_FPS, on_animation_tick);
            animation_changed.emit ();
        }

        public void stop_animation () {
            if (!is_animating ()) return;
            Source.remove (_animation_source);
            _animation_source = 0;
            animation_changed.emit ();
        }

        private bool on_animation_tick () {
            int64 now = get_monotonic_time ();
            double elapsed = (now - _animation_time) / 1000d;
            _animation_time = now;

            double low = double.min (min, max);
            double high = double.max (min, max);
            if (low == high) {
                _animation_source = 0;
                animation_changed.emit ();
                return Source.REMOVE;
            }

            double distance = (high - low) * elapsed / ANIMATION_DURATION;
            _animation_position += _animation_direction * distance;
            if (_animation_position >= high) {
                _animation_position = high;
                _animation_direction = -1;
            } else if (!(_animation_position > low)) {
                _animation_position = low;
                _animation_direction = 1;
            }
            value = snap (_animation_position);
            return Source.CONTINUE;
        }

        public override void dispose () {
            if (_animation_source != 0) {
                Source.remove (_animation_source);
                _animation_source = 0;
            }
            base.dispose ();
        }
    }
}
