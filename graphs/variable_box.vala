// SPDX-License-Identifier: GPL-3.0-or-later
namespace Graphs {
    /**
     * Row for a variable, with a slider to change its value.
     */
    [GtkTemplate (ui = "/se/sjoerd/Graphs/ui/variable-box.ui")]
    private class VariableBox : Adw.ActionRow {
        // Time without changes after which a new value ends up in the history
        private const uint HISTORY_DELAY = 500;

        [GtkChild]
        private unowned Gtk.Scale scale { get; }

        [GtkChild]
        private unowned Gtk.ToggleButton play_button { get; }

        public Window window { get; construct set; }
        public VariableItem item { get; construct set; }

        private bool updating = false;
        private uint history_source = 0;

        public VariableBox (Window window, VariableItem item) {
            Object (
                window: window,
                item: item
            );

            item.notify["value"].connect (update);
            item.notify["min"].connect (update);
            item.notify["max"].connect (update);
            item.notify["step"].connect (update);
            item.animation_changed.connect (update_animation);
            update ();
            update_animation ();
        }

        private void update () {
            updating = true;
            set_title (format_title (item));

            double step = item.get_effective_step ();
            scale.adjustment.configure (item.value, item.min, item.max, step, step * 10, 0);
            scale.set_sensitive (item.min < item.max);
            play_button.set_sensitive (item.min < item.max);
            updating = false;
        }

        private void update_animation () {
            updating = true;
            bool animating = item.is_animating ();
            play_button.set_active (animating);
            play_button.set_icon_name (
                animating ? "media-playback-pause-symbolic" : "media-playback-start-symbolic"
            );
            play_button.set_tooltip_text (animating ? _("Stop Animation") : _("Animate"));
            updating = false;
        }

        public static string format_title (VariableItem item) {
            // Translators: The name of a variable followed by its value
            return _("%s = %s").printf (item.variable, MathTools.prettyprint_double (item.value));
        }

        [GtkCallback]
        private void on_scale_changed () {
            if (updating) return;
            item.value = item.snap (scale.get_value ());
            queue_history_state ();
        }

        [GtkCallback]
        private void on_play_toggled () {
            if (updating) return;
            if (play_button.get_active ()) {
                item.start_animation ();
            } else {
                item.stop_animation ();
                window.data.add_history_state ();
            }
        }

        /**
         * Dragging the slider gives many values, only the one it ends up in
         * the end at should be a step in the history.
         */
        private void queue_history_state () {
            if (history_source != 0) Source.remove (history_source);
            history_source = Timeout.add (HISTORY_DELAY, on_history_timeout);
        }

        private bool on_history_timeout () {
            history_source = 0;
            if (!item.is_animating ()) window.data.add_history_state ();
            return Source.REMOVE;
        }

        public override void dispose () {
            if (history_source != 0) {
                Source.remove (history_source);
                history_source = 0;
            }
            base.dispose ();
        }
    }
}
