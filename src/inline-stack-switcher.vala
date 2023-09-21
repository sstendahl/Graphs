// This file is part of Elastic. License: GPL-3.0+.

// For the most part a direct port of gtkstackswitcher.c

public class Graphs.InlineStackSwitcher : Gtk.Widget {
    private const int TIMEOUT_EXPAND = 500;

    private Gtk.Stack _stack;
    public Gtk.Stack stack {
        get { return _stack; }
        set {
            if (stack == value)
                return;

            if (stack != null)
                disconnect_stack ();

            _stack = value;

            if (stack != null)
                connect_stack ();
        }
    }

    private Gtk.SelectionModel pages;
    private HashTable<Gtk.StackPage, Gtk.ToggleButton> buttons;

    static construct {
        set_css_name ("inline-stack-switcher");
        set_accessible_role (TAB_LIST);
        set_layout_manager_type (typeof (Gtk.BoxLayout));
    }

    construct {
        buttons = new HashTable<Gtk.StackPage, Gtk.ToggleButton> (direct_hash, direct_equal);
    }

    protected override void dispose () {
        if (stack != null)
            disconnect_stack ();

        base.dispose ();
    }

    private void connect_stack () {
        pages = stack.pages;
        pages.items_changed.connect (items_changed_cb);
        pages.selection_changed.connect (selection_changed_cb);

        populate_switcher ();
    }

    private void disconnect_stack () {
        clear_switcher ();

        pages.items_changed.disconnect (items_changed_cb);
        pages.selection_changed.disconnect (selection_changed_cb);
        pages = null;
    }

    private void populate_switcher () {
        for (int i = 0; i < pages.get_n_items (); i++)
            add_child (i);
    }

    private void clear_switcher () {
        buttons.for_each ((page, button) => {
            var separator = button.get_data<Gtk.Widget> ("next-separator");
            button.unparent ();
            separator.unparent ();
            page.notify.disconnect (page_updated_cb);
        });

        buttons.remove_all ();
    }

    private void items_changed_cb () {
        clear_switcher ();
        populate_switcher ();
    }

    private void selection_changed_cb (uint position, uint n_items) {
        for (uint i = position; i < position + n_items; i++) {
            var page = pages.get_item (i) as Gtk.StackPage;
            var button = buttons[page];

            if (button != null) {
                bool selected = pages.is_selected (i);

                button.active = selected;
                button.update_state (Gtk.AccessibleState.SELECTED, selected, -1);
            }
        }
    }

    private void add_child (int index) {
        var button = new Gtk.ToggleButton () {
            accessible_role = TAB,
            hexpand = true,
            vexpand = true,
            focus_on_click = false,
        };

        button.can_shrink = true;

        button.add_css_class ("flat");

        var controller = new Gtk.DropControllerMotion ();
        controller.enter.connect (() => {
            if (button.active)
                return;

            uint switch_timer = Timeout.add (TIMEOUT_EXPAND, () => {
                button.steal_data<uint> ("switch-timer");
                button.active = true;

                return Source.REMOVE;
            });
            button.set_data_full ("switch-timer", (void *) switch_timer, data => {
                if (data != null)
                    Source.remove ((uint) data);
            });
        });
        controller.leave.connect (() => {
            uint switch_timer = button.steal_data<uint> ("switch-timer");

            if (switch_timer > 0)
                Source.remove (switch_timer);
        });
        button.add_controller (controller);

        var page = pages.get_item (index) as Gtk.StackPage;
        update_button (page, button);

        button.set_parent (this);

        bool selected = pages.is_selected (index);
        button.active = selected;
        button.update_state (Gtk.AccessibleState.SELECTED, selected, -1);
        button.update_relation (Gtk.AccessibleRelation.CONTROLS, page, null, -1);

        button.notify["active"].connect (() => {
            if (button.active)
                pages.select_item (index, true);
            else
                button.active = pages.is_selected (index);
        });

        page.notify.connect (page_updated_cb);

        buttons[page] = button;

        var separator = new Gtk.Separator (VERTICAL);
        separator.set_parent (this);

        button.set_data<Gtk.Widget> ("separator", separator);

        button.state_flags_changed.connect (() => {
            var prev_separator = button.get_prev_sibling ();
            var next_separator = button.get_next_sibling ();

            if (prev_separator != null)
                update_separator (prev_separator);

            if (next_separator != null)
                update_separator (next_separator);
        });

        var prev_separator = button.get_prev_sibling ();
        var next_separator = button.get_next_sibling ();

        if (prev_separator != null)
            update_separator (prev_separator);

        if (next_separator != null)
            update_separator (next_separator);
    }

    private void page_updated_cb (Object object, ParamSpec pspec) {
        var page = object as Gtk.StackPage;
        var button = buttons[page];

        update_button (page, button);
    }

    private void update_button (Gtk.StackPage page, Gtk.Button button) {
        if (page.icon_name != null) {
            button.icon_name = page.icon_name;
            button.tooltip_text = page.title;
        } else if (page.title != null) {
            button.label = page.title;
            button.use_underline = page.use_underline;
            button.tooltip_text = null;
        }

        button.update_property (Gtk.AccessibleProperty.LABEL, page.title, -1);

        button.visible = page.visible && (page.title != null || page.icon_name != null);

        if (page.needs_attention)
            button.add_css_class ("needs-attention");
        else
            button.remove_css_class ("needs-attention");
    }

    private bool should_hide_separators (Gtk.Widget? widget) {
        if (widget == null)
            return true;

        var flags = widget.get_state_flags ();

        if ((flags & (Gtk.StateFlags.PRELIGHT |
                      Gtk.StateFlags.ACTIVE |
                      Gtk.StateFlags.CHECKED)) != 0)
            return true;

        if ((flags & Gtk.StateFlags.FOCUSED) != 0 &&
            (flags & Gtk.StateFlags.FOCUS_VISIBLE) != 0)
            return true;

        return false;
    }

    private void update_separator (Gtk.Widget separator) {
        var prev_button = separator.get_prev_sibling ();
        var next_button = separator.get_next_sibling ();

        separator.visible = prev_button != null && next_button != null;

        if (should_hide_separators (prev_button) ||
            should_hide_separators (next_button))
            separator.add_css_class ("hidden");
        else
            separator.remove_css_class ("hidden");
    }
}
