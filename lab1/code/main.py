import sys
import gi

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib

class ColorConverterWindow(Gtk.ApplicationWindow):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.is_updating = False
        
        self.set_title("Лабораторная работа 1: CMYK-RGB-HLS")
        self.set_default_size(800, 600)
        
        main_grid = Gtk.Grid(column_spacing=10, row_spacing=10, margin=15)
        self.add(main_grid)
        
        self.color_chooser = Gtk.ColorChooserWidget(show_editor=True)
        self.color_chooser.set_use_alpha(False)
        main_grid.attach(self.color_chooser, 0, 0, 1, 1)
        
        models_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        main_grid.attach(models_box, 1, 0, 1, 1)
        
        rgb_frame = self.create_model_frame(
            "RGB",
            [("R", 0, 255), ("G", 0, 255), ("B", 0, 255)],
            self.on_rgb_changed
        )
        models_box.pack_start(rgb_frame, False, False, 0)
        
        cmyk_frame = self.create_model_frame(
            "CMYK",
            [("C", 0, 100), ("M", 0, 100), ("Y", 0, 100), ("K", 0, 100)],
            self.on_cmyk_changed
        )
        models_box.pack_start(cmyk_frame, False, False, 0)
        
        hls_frame = self.create_model_frame(
            "HLS",
            [("H", 0, 360), ("L", 0, 100), ("S", 0, 100)],
            self.on_hls_changed
        )
        models_box.pack_start(hls_frame, False, False, 0)
        
        self.color_chooser.connect("notify::rgba", self.on_chooser_changed)
        
        initial_rgba = Gdk.RGBA(red=0.2, green=0.4, blue=0.8, alpha=1.0)
        self.color_chooser.set_rgba(initial_rgba)
        
        self.show_all()

    def create_model_frame(self, title, components, change_handler):
        frame = Gtk.Frame(label=title, margin_top=10, shadow_type=Gtk.ShadowType.ETCHED_IN)
        grid = Gtk.Grid(column_spacing=10, row_spacing=5, margin=10)
        frame.add(grid)
        
        for i, (name, min_val, max_val) in enumerate(components):
            label = Gtk.Label(label=f"{name}:", xalign=1)
            
            adj = Gtk.Adjustment.new(min_val, min_val, max_val, 1, 10, 0)
            
            scale = Gtk.Scale.new(Gtk.Orientation.HORIZONTAL, adj)
            scale.set_hexpand(True)
            scale.set_digits(0)
            
            spin = Gtk.SpinButton.new(adj, 1, 0)
            if max_val <= 100:
                spin.set_digits(1)
            
            setattr(self, f"adj_{name.lower()}", adj)
            
            grid.attach(label, 0, i, 1, 1)
            grid.attach(scale, 1, i, 1, 1)
            grid.attach(spin, 2, i, 1, 1)
            
            adj.connect("value-changed", change_handler)
            
        return frame

    def on_rgb_changed(self, adjustment):
        if self.is_updating:
            return
            
        r_norm = self.adj_r.get_value() / 255.0
        g_norm = self.adj_g.get_value() / 255.0
        b_norm = self.adj_b.get_value() / 255.0
        
        c, m, y, k = self.convert_rgb_to_cmyk(r_norm, g_norm, b_norm)
        h, l, s = self.convert_rgb_to_hls(r_norm, g_norm, b_norm)
        
        self.update_all_widgets(r_norm, g_norm, b_norm, c, m, y, k, h, l, s)

    def on_cmyk_changed(self, adjustment):
        if self.is_updating:
            return
            
        c_norm = self.adj_c.get_value() / 100.0
        m_norm = self.adj_m.get_value() / 100.0
        y_norm = self.adj_y.get_value() / 100.0
        k_norm = self.adj_k.get_value() / 100.0
        
        r, g, b = self.convert_cmyk_to_rgb(c_norm, m_norm, y_norm, k_norm)
        h, l, s = self.convert_rgb_to_hls(r, g, b)
        
        self.update_all_widgets(r, g, b, c_norm, m_norm, y_norm, k_norm, h, l, s)

    def on_hls_changed(self, adjustment):
        if self.is_updating:
            return
            
        h_val = self.adj_h.get_value()
        l_norm = self.adj_l.get_value() / 100.0
        s_norm = self.adj_s.get_value() / 100.0
        
        r, g, b = self.convert_hls_to_rgb(h_val, l_norm, s_norm)
        c, m, y, k = self.convert_rgb_to_cmyk(r, g, b)
        
        self.update_all_widgets(r, g, b, c, m, y, k, h_val, l_norm, s_norm)

    def on_chooser_changed(self, widget, gparam):
        if self.is_updating:
            return
            
        rgba = self.color_chooser.get_rgba()
        r, g, b = rgba.red, rgba.green, rgba.blue
        
        c, m, y, k = self.convert_rgb_to_cmyk(r, g, b)
        h, l, s = self.convert_rgb_to_hls(r, g, b)
        
        self.update_all_widgets(r, g, b, c, m, y, k, h, l, s)

    def update_all_widgets(self, r, g, b, c, m, y, k, h, l, s):
        self.is_updating = True
        
        try:
            self.adj_r.set_value(r * 255.0)
            self.adj_g.set_value(g * 255.0)
            self.adj_b.set_value(b * 255.0)
            
            self.adj_c.set_value(c * 100.0)
            self.adj_m.set_value(m * 100.0)
            self.adj_y.set_value(y * 100.0)
            self.adj_k.set_value(k * 100.0)
            
            self.adj_h.set_value(h)
            self.adj_l.set_value(l * 100.0)
            self.adj_s.set_value(s * 100.0)
            
            rgba = Gdk.RGBA(red=r, green=g, blue=b, alpha=1.0)
            current_rgba = self.color_chooser.get_rgba()
            if not current_rgba.equal(rgba):
                self.color_chooser.set_rgba(rgba)
                
        except Exception as e:
            print(f"Error during widget update: {e}", file=sys.stderr)
            
        finally:
            GLib.idle_add(self.reset_update_flag)

    def reset_update_flag(self):
        self.is_updating = False
        return GLib.SOURCE_REMOVE

    def convert_cmyk_to_rgb(self, c, m, y, k):
        r = (1 - c) * (1 - k)
        g = (1 - m) * (1 - k)
        b = (1 - y) * (1 - k)
        return r, g, b

    def convert_rgb_to_cmyk(self, r, g, b):
        k = 1 - max(r, g, b)
        if k > 0.99999:
            return 0, 0, 0, 1

        c = (1 - r - k) / (1 - k)
        m = (1 - g - k) / (1 - k)
        y = (1 - b - k) / (1 - k)
        
        return c, m, y, k

    def convert_rgb_to_hls(self, r, g, b):
        max_val = max(r, g, b)
        min_val = min(r, g, b)
        
        l = (max_val + min_val) / 2.0
        
        h = 0.0
        s = 0.0
        
        delta = max_val - min_val
        
        if delta < 0.00001:
            h = 0.0
            s = 0.0
        else:
            if l < 0.5:
                s = delta / (max_val + min_val)
            else:
                s = delta / (2.0 - max_val - min_val)
                
            if max_val == r:
                h = (g - b) / delta
            elif max_val == g:
                h = 2.0 + (b - r) / delta
            else:
                h = 4.0 + (r - g) / delta
                
            h *= 60.0
            
            if h < 0:
                h += 360.0
                
        return h, l, s

    def convert_hls_to_rgb(self, h, l, s):
        if s <= 0.00001:
            return l, l, l
            
        if l < 0.5:
            temp1 = l * (1.0 + s)
        else:
            temp1 = l + s - (l * s)
            
        temp2 = 2.0 * l - temp1
        
        h_norm = h / 360.0
        
        temp_r = h_norm + 1.0 / 3.0
        temp_g = h_norm
        temp_b = h_norm - 1.0 / 3.0
        
        def hue_to_component(t, t1, t2):
            if t < 0: t += 1.0
            if t > 1: t -= 1.0
            
            if 6.0 * t < 1.0:
                return t2 + (t1 - t2) * 6.0 * t
            if 2.0 * t < 1.0:
                return t1
            if 3.0 * t < 2.0:
                return t2 + (t1 - t2) * (2.0 / 3.0 - t) * 6.0
            return t2
            
        r = hue_to_component(temp_r, temp1, temp2)
        g = hue_to_component(temp_g, temp1, temp2)
        b = hue_to_component(temp_b, temp1, temp2)
        
        return r, g, b

class ColorConverterApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="bla.bla.bla.bla")

    def do_activate(self):
        win = ColorConverterWindow(application=self)
        win.present()

if __name__ == "__main__":
    app = ColorConverterApp()
    exit_status = app.run(sys.argv)
    sys.exit(exit_status)