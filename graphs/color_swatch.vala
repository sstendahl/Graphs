// SPDX-License-Identifier: GPL-3.0-or-later
namespace Graphs {
    public class ColorSwatch : Gtk.Widget {
        private Gdk.RGBA _color = { 1f, 0f, 0f, 1f };

        public Gdk.RGBA color {
            get { return _color; }
            set {
                _color = value;
                queue_draw ();
            }
        }

        construct {
            set_size_request (20, 20);
        }

        protected override void snapshot (Gtk.Snapshot snapshot) {
            int width = get_width ();
            int height = get_height ();

            float radius = float.min (width, height) / 2.0f;
            Graphene.Rect bounds = Graphene.Rect ();
            bounds.init (0, 0, width, height);

            var cr = snapshot.append_cairo (bounds);

            cr.set_source_rgba (
                _color.red,
                _color.green,
                _color.blue,
                _color.alpha
            );

            cr.arc (
                width / 2.0,
                height / 2.0,
                radius,
                0,
                2 * Math.PI
            );

            cr.fill ();
        }
    }
}
