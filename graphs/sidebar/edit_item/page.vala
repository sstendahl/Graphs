// SPDX-License-Identifier: GPL-3.0-or-later
namespace Graphs {
    [GtkTemplate (ui = "/se/sjoerd/Graphs/ui/sidebar/edit-item/page.ui")]
    public class EditItemPage : Adw.NavigationPage {
        [GtkChild]
        private unowned Gtk.Box edit_item_box { get; }

        public void load_item (Item item) {
            Gtk.Widget widget;
            while ((widget = edit_item_box.get_last_child ()) != null) {
                edit_item_box.remove (widget);
            }

            edit_item_box.append (new EditItemBaseBox (item));

            if (item is GeneratedDataItem) {
                edit_item_box.append (new EditItemGeneratedDataItemBox ((GeneratedDataItem) item));
            }
            if (item is DataItem) {
                DataItem data_item = (DataItem) item;
                edit_item_box.append (new EditItemDataItemBox (data_item));
                if (data_item.has_xerr () || data_item.has_yerr ()) {
                    edit_item_box.append (new EditItemErrorBarGroup (data_item));
                }
            } else if (item is EquationItem) {
                edit_item_box.append (new EditItemEquationItemBox ((EquationItem) item));
            } else if (item is FillItem) {
                var window = (Window) get_root ();
                edit_item_box.append (new EditItemFillItemBox ((FillItem) item, window.data));
            }
        }
    }
}
