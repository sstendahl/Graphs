// SPDX-License-Identifier: GPL-3.0-or-later
using Adw;
using Gtk;

namespace Graphs {
    [GtkTemplate (ui = "/se/sjoerd/Graphs/ui/sidebar/main.ui")]
    public class MainSidebarPage : Adw.NavigationPage {
        [GtkChild]
        private unowned ScrolledWindow scrollwindow_itemlist { get; }

        [GtkChild]
        private unowned ToggleButton pan_button { get; }

        [GtkChild]
        private unowned ToggleButton zoom_button { get; }

        [GtkChild]
        private unowned ToggleButton select_button { get; }

        [GtkChild]
        private unowned Adw.Bin operations_bin { get; }

        [GtkChild]
        private unowned Stack itemlist_stack { get; }

        [GtkChild]
        public unowned ListBox item_list { get; }

        public bool height_limited {
            set {
                scrollwindow_itemlist.set_policy (
                    PolicyType.AUTOMATIC, value ? PolicyType.NEVER : PolicyType.AUTOMATIC
                );
            }
            get { return false; } // needed to be registered as valid property
        }

        public Mode mode {
            set {
                pan_button.set_active (value == Mode.PAN);
                zoom_button.set_active (value == Mode.ZOOM);
                select_button.set_active (value == Mode.SELECT);
            }
            get {
                if (pan_button.get_active ()) return Mode.PAN;
                if (zoom_button.get_active ()) return Mode.ZOOM;
                if (select_button.get_active ()) return Mode.SELECT;
                return -1;
            }
        }

        public Operations operations {
            get { return (Operations) operations_bin.get_child (); }
            set { operations_bin.set_child (value); }
        }

        public MainSidebarPage () {}

        public void set_show_empty_data_page (bool val) {
            itemlist_stack.get_pages ().select_item (val ? 0 : 1, true);
        }
    }
}
