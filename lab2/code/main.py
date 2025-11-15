import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GdkPixbuf
import numpy as np
from PIL import Image

from numpy.lib.stride_tricks import sliding_window_view 

class ImageProcessorApp(Gtk.Window):
    def __init__(self):
        super(ImageProcessorApp, self).__init__(title="ЛАБА 2")
        self.set_default_size(1000, 700)
        self.original_image_data = None
        self.unscaled_pixbuf = None

        grid = Gtk.Grid()
        grid.set_column_spacing(10)
        grid.set_row_spacing(10)
        grid.set_margin_top(10)
        grid.set_margin_bottom(10)
        grid.set_margin_start(10)
        grid.set_margin_end(10)
        self.add(grid)

        self.image_display = Gtk.Image()
        self.image_display.set_hexpand(True)
        self.image_display.set_vexpand(True)
        self.image_display.connect("size-allocate", self.on_image_resize) 
        grid.attach(self.image_display, 2, 0, 4, 10)

        controls_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        grid.attach(controls_box, 0, 0, 2, 10)

        file_chooser_button = Gtk.FileChooserButton(title="Выберите изображение", action=Gtk.FileChooserAction.OPEN)
        file_chooser_button.connect("file-set", self.on_file_set)
        controls_box.pack_start(file_chooser_button, expand=False, fill=False, padding=0)

        btn_gray = Gtk.Button.new_with_label("Перевести в Оттенки Серого")
        btn_gray.connect("clicked", self.make_gray)
        controls_box.pack_start(btn_gray, expand=False, fill=False, padding=0)

        seg_label = Gtk.Label(label="Пороговая Обработка")
        controls_box.pack_start(seg_label, expand=False, fill=False, padding=0)

        controls_box.pack_start(Gtk.Label(label="T1 (Нижний Порог):"), expand=False, fill=False, padding=0)
        adj_lower = Gtk.Adjustment(value=50, lower=0, upper=255, step_increment=1, page_increment=10, page_size=0)
        self.lower_threshold_input = Gtk.Scale.new(Gtk.Orientation.HORIZONTAL, adj_lower)
        self.lower_threshold_input.set_digits(0)
        self.lower_threshold_input.set_value_pos(Gtk.PositionType.RIGHT)
        self.lower_threshold_input.set_draw_value(True)
        controls_box.pack_start(self.lower_threshold_input, expand=False, fill=True, padding=0)

        controls_box.pack_start(Gtk.Label(label="T2 (Верхний Порог):"), expand=False, fill=False, padding=0)
        adj_upper = Gtk.Adjustment(value=200, lower=0, upper=255, step_increment=1, page_increment=10, page_size=0)
        self.upper_threshold_input = Gtk.Scale.new(Gtk.Orientation.HORIZONTAL, adj_upper)
        self.upper_threshold_input.set_digits(0)
        self.upper_threshold_input.set_value_pos(Gtk.PositionType.RIGHT)
        self.upper_threshold_input.set_draw_value(True)
        controls_box.pack_start(self.upper_threshold_input, expand=False, fill=True, padding=0)

        self.invert_checkbox = Gtk.CheckButton.new_with_label("Инвертировать результат")
        controls_box.pack_start(self.invert_checkbox, expand=False, fill=False, padding=0)

        btn_static_thresh = Gtk.Button.new_with_label("Бинарный Порог (I > T1)")
        btn_static_thresh.connect("clicked", self.apply_thresholding, 'static')
        controls_box.pack_start(btn_static_thresh, expand=False, fill=False, padding=0)

        btn_double_thresh = Gtk.Button.new_with_label("Двойной Порог (T1 < I <= T2)")
        btn_double_thresh.connect("clicked", self.apply_thresholding, 'double')
        controls_box.pack_start(btn_double_thresh, expand=False, fill=False, padding=0)

        seg_label = Gtk.Label(label="Обнаружение Границ")
        controls_box.pack_start(seg_label, expand=False, fill=False, padding=0)

        btn_sobel = Gtk.Button.new_with_label("Перепады Яркости (Собель)")
        btn_sobel.connect("clicked", self.apply_segmentation, 'sobel')
        controls_box.pack_start(btn_sobel, expand=False, fill=False, padding=0)

        btn_laplacian = Gtk.Button.new_with_label("Обнаружение Точек (Лапласиан)")
        btn_laplacian.connect("clicked", self.apply_segmentation, 'laplacian')
        controls_box.pack_start(btn_laplacian, expand=False, fill=False, padding=0)

        btn_line_horiz = Gtk.Button.new_with_label("Обнаружение Горизонтальных Линий")
        btn_line_horiz.connect("clicked", self.apply_segmentation, 'line_h')
        controls_box.pack_start(btn_line_horiz, expand=False, fill=False, padding=0)
        
        btn_reset = Gtk.Button.new_with_label("Сброс Изображения")
        btn_reset.connect("clicked", self.reset_image)
        controls_box.pack_start(btn_reset, expand=False, fill=False, padding=0)

    def get_lower_threshold(self):
        return int(self.lower_threshold_input.get_value())

    def get_upper_threshold(self):
        return int(self.upper_threshold_input.get_value())

    def get_inversion_state(self):
        return self.invert_checkbox.get_active()

    def on_file_set(self, widget):
        filepath = widget.get_filename()
        if filepath:
            try:
                pil_img = Image.open(filepath).convert('RGB')
                self.original_image_data = np.array(pil_img)
                self.display_image_data(self.original_image_data)
            except Exception as e:
                print(f"Ошибка загрузки: {e}")

    def reset_image(self, widget):
        if self.original_image_data is not None:
            self.display_image_data(self.original_image_data)

    def display_image_data(self, np_array):
        if np_array is None:
            return

        if np_array.ndim == 2:
            pil_img = Image.fromarray(np_array.astype(np.uint8), mode='L').convert('RGB')
        else:
            pil_img = Image.fromarray(np_array.astype(np.uint8), mode='RGB')
        
        w, h = pil_img.size
        
        unscaled_pixbuf = GdkPixbuf.Pixbuf.new_from_data(
            pil_img.tobytes(),
            GdkPixbuf.Colorspace.RGB,
            False,
            8,
            w,
            h,
            w * 3,
            None, None
        )
        
        self.unscaled_pixbuf = unscaled_pixbuf
        
        allocation = self.image_display.get_allocation()
        self.scale_and_set_image(allocation.width, allocation.height)

    def scale_and_set_image(self, allocated_width, allocated_height):
        if self.unscaled_pixbuf is None or allocated_width <= 0 or allocated_height <= 0:
            return

        orig_w = self.unscaled_pixbuf.get_width()
        orig_h = self.unscaled_pixbuf.get_height()
        
        if orig_w == 0 or orig_h == 0:
            return

        w_ratio = allocated_width / orig_w
        h_ratio = allocated_height / orig_h
        
        scale_ratio = min(w_ratio, h_ratio)

        new_w = int(orig_w * scale_ratio)
        new_h = int(orig_h * scale_ratio)

        scaled_pixbuf = self.unscaled_pixbuf.scale_simple(
            new_w,
            new_h,
            GdkPixbuf.InterpType.BILINEAR
        )
        self.image_display.set_from_pixbuf(scaled_pixbuf)

    def on_image_resize(self, widget, allocation):
        self.scale_and_set_image(allocation.width, allocation.height)

    def get_gray(self):
        if self.original_image_data is None: return None
        return np.dot(self.original_image_data[...,:3], [0.2989, 0.5870, 0.1140]).astype(np.uint8)
    
    def make_gray(self, widget):
        img_gray = self.get_gray()
        if img_gray is not None:
            self._post_process_and_display(img_gray) 

    def _post_process_and_display(self, processed_data):
        if self.get_inversion_state():
            processed_data = 255 - processed_data.astype(np.uint8) 
        
        self.display_image_data(processed_data)

    def apply_thresholding(self, widget, thresh_type):
        img_gray = self.get_gray()
        if img_gray is None: return

        T_lower = self.get_lower_threshold()
        
        binary_img = np.zeros_like(img_gray, dtype=np.uint8)
        
        if thresh_type == 'static':
            binary_img[img_gray > T_lower] = 255
        
        elif thresh_type == 'double':
            T_upper = self.get_upper_threshold()
            condition = (img_gray > T_lower) & (img_gray <= T_upper)
            binary_img[condition] = 255
            
        self._post_process_and_display(binary_img)

    def apply_segmentation(self, widget, seg_type):
        if self.original_image_data is None: return

        img_gray = np.dot(self.original_image_data[...,:3], [0.2989, 0.5870, 0.1140]).astype(np.float64)
        
        if seg_type == 'sobel':
            kernel_x = np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]])
            kernel_y = np.array([[-1, -2, -1], [0, 0, 0], [1, 2, 1]])
            
            grad_x = self._convolve(img_gray, kernel_x)
            grad_y = self._convolve(img_gray, kernel_y)
            
            processed_data = np.sqrt(grad_x**2 + grad_y**2)
            
        elif seg_type == 'laplacian':
            kernel = np.array([[0, 1, 0], [1, -4, 1], [0, 1, 0]])
            processed_data = self._convolve(img_gray, kernel)
            
        elif seg_type == 'line_h':
            kernel = np.array([[-1, -1, -1], [2, 2, 2], [-1, -1, -1]])
            processed_data = self._convolve(img_gray, kernel)
            
        processed_data = np.clip(processed_data, 0, 255)
        processed_data = processed_data.astype(np.uint8)
        
        self._post_process_and_display(processed_data)

    def _convolve(self, img, kernel):
        k_h, k_w = kernel.shape
        p_h, p_w = k_h // 2, k_w // 2
        
        padded_img = np.pad(img, ((p_h, p_h), (p_w, p_w)), mode='reflect')

        windows = sliding_window_view(padded_img, (k_h, k_w))
        
        output = np.sum(windows * kernel, axis=(2, 3))
        
        return output

if __name__ == '__main__':
    win = ImageProcessorApp()
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()