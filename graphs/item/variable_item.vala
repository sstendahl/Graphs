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
                if (value < min) {
                    min = value;
                } else if (value > max) {
                    max = value;
                }
            }
        }

        public double min { get; set; default = -10; }
        public double max { get; set; default = 10; }
        public int steps { get; set; default = 200; }
        public Scale scale { get; set; default = Scale.LINEAR; }

        private uint _animation_source = 0;
        private int _animation_direction = 1;
        private int64 _animation_time;
        private double _animation_position;

        public signal void animation_changed ();

        construct {
            typename = _("Variable");
        }

        public VariableItem (string variable, double value = DEFAULT_VALUE) {
            Object (variable: variable, name: variable);
            this.value = value;
        }

        /**
         * Whether a value can be on the scale of the slider
         */
        public bool supports_scale (double val) {
            switch (scale) {
                case Scale.LOG:
                case Scale.LOG2:
                case Scale.INVERSE:
                    return val > 0;
                case Scale.SQUAREROOT:
                    return val >= 0;
                default:
                    return true;
            }
        }

        public bool has_range () {
            return min < max && supports_scale (min);
        }

        /**
         * Get the position of the slider the value is closest to in steps
         */
        public int get_position () {
            if (!has_range ()) return 0;
            double fraction = get_fraction_at_value (value, min, max, scale);
            if (scale == Scale.INVERSE) fraction = 1 - fraction;
            return (int) Math.round (fraction.clamp (0, 1) * steps);
        }

        public double get_value_at (int position) {
            if (!has_range ()) return value;
            double fraction = (double) position / steps;
            if (scale == Scale.INVERSE) fraction = 1 - fraction;
            double val = get_value_at_fraction (fraction, min, max, scale);
            return double.parse ("%.12g".printf (val)).clamp (min, max);
        }

        public void fit_value () {
            value = value.clamp (min, max);
        }

        public bool is_animating () {
            return _animation_source != 0;
        }

        public void start_animation () {
            if (is_animating () || !has_range ()) return;
            _animation_time = get_monotonic_time ();
            _animation_position = (double) get_position () / steps;
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

            _animation_position += _animation_direction * elapsed / ANIMATION_DURATION;
            if (_animation_position >= 1) {
                _animation_position = 1;
                _animation_direction = -1;
            } else if (_animation_position <= 0) {
                _animation_position = 0;
                _animation_direction = 1;
            }
            value = get_value_at ((int) Math.round (_animation_position * steps));
            return Source.CONTINUE;
        }
    }
}
