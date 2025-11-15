from time import sleep
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GObject
import numpy as np
import cairo
import math
import random

import logging
logging.getLogger("Gtk").setLevel(logging.ERROR) 

class RasterApp(Gtk.Window):
    def __init__(self):
        super().__init__(title="Лабораторная работа 3: Растровые алгоритмы (Пошаговая отрисовка)")
        self.set_default_size(800, 600)
        self.connect("destroy", Gtk.main_quit)

        self.CANVAS_WIDTH = 50
        self.CANVAS_HEIGHT = 50
        
        self.pixel_scale = 9 
        self.step_delay = 0.005
        self.current_timeout_id = None
        self.drawing_tasks = []
        self.is_real_line_active = False

        self.pixel_data = np.zeros((self.CANVAS_HEIGHT, self.CANVAS_WIDTH, 4), dtype=np.uint8)
        self.clear_canvas()

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.add(vbox)

        self.drawing_area = Gtk.DrawingArea()
        self.drawing_area.set_size_request(500, 500) 
        self.drawing_area.connect("draw", self.on_draw)
        vbox.pack_start(self.drawing_area, True, True, 0)
        
        grid = Gtk.Grid(); grid.set_column_spacing(10); grid.set_row_spacing(5)
        grid.set_border_width(10)
        vbox.pack_start(grid, False, False, 0)

        row = 0
        grid.attach(Gtk.Label(label="X1:"), 0, row, 1, 1); self.x1_entry = Gtk.Entry(); self.x1_entry.set_text("5"); grid.attach(self.x1_entry, 1, row, 1, 1)
        grid.attach(Gtk.Label(label="Y1:"), 2, row, 1, 1); self.y1_entry = Gtk.Entry(); self.y1_entry.set_text("45"); grid.attach(self.y1_entry, 3, row, 1, 1); row += 1
        
        grid.attach(Gtk.Label(label="X2:"), 0, row, 1, 1); self.x2_entry = Gtk.Entry(); self.x2_entry.set_text("20"); grid.attach(self.x2_entry, 1, row, 1, 1)
        grid.attach(Gtk.Label(label="Y2:"), 2, row, 1, 1); self.y2_entry = Gtk.Entry(); self.y2_entry.set_text("15"); grid.attach(self.y2_entry, 3, row, 1, 1); row += 1

        grid.attach(Gtk.Label(label="Центр X:"), 0, row, 1, 1); self.cx_entry = Gtk.Entry(); self.cx_entry.set_text("25"); grid.attach(self.cx_entry, 1, row, 1, 1)
        grid.attach(Gtk.Label(label="Центр Y:"), 2, row, 1, 1); self.cy_entry = Gtk.Entry(); self.cy_entry.set_text("25"); grid.attach(self.cy_entry, 3, row, 1, 1); row += 1

        grid.attach(Gtk.Label(label="Радиус:"), 0, row, 1, 1); self.radius_entry = Gtk.Entry(); self.radius_entry.set_text("20"); grid.attach(self.radius_entry, 1, row, 1, 1); row += 1

        grid.attach(Gtk.Label(label="Ширина поля:"), 0, row, 1, 1)
        self.width_entry = Gtk.Entry(); self.width_entry.set_text(str(self.CANVAS_WIDTH)); grid.attach(self.width_entry, 1, row, 1, 1)
        
        grid.attach(Gtk.Label(label="Высота поля:"), 2, row, 1, 1)
        self.height_entry = Gtk.Entry(); self.height_entry.set_text(str(self.CANVAS_HEIGHT)); grid.attach(self.height_entry, 3, row, 1, 1)
        
        button_resize = Gtk.Button(label="Изменить размер поля")
        button_resize.connect("clicked", self.on_resize_clicked)
        grid.attach(button_resize, 4, row, 2, 1); row += 1 

        grid.attach(Gtk.Label(label="Масштаб:"), 4, 0, 1, 1)
        self.scale_adjustment = Gtk.Adjustment(
            value=self.pixel_scale, lower=2, upper=100, step_increment=1, page_increment=5, page_size=0
        )
        self.scale_spin = Gtk.SpinButton(); self.scale_spin.set_adjustment(self.scale_adjustment)
        self.scale_spin.connect("value-changed", self.on_scale_changed) 
        grid.attach(self.scale_spin, 5, 0, 1, 1)
        
        grid.attach(Gtk.Label(label="Задержка (с):"), 4, 1, 1, 1)
        self.delay_adjustment = Gtk.Adjustment(
            value=self.step_delay, lower=0.001, upper=0.5, step_increment=0.001, page_increment=0.01, page_size=0
        )
        self.delay_spin = Gtk.SpinButton(); self.delay_spin.set_adjustment(self.delay_adjustment)
        self.delay_spin.set_digits(3)
        grid.attach(self.delay_spin, 5, 1, 1, 1)

        row_algo = 0
        self.check_sequential = Gtk.CheckButton(label="Пошаговый (Красный)"); grid.attach(self.check_sequential, 6, row_algo, 1, 1); row_algo += 1
        self.check_dda = Gtk.CheckButton(label="ЦДА (Зеленый)"); grid.attach(self.check_dda, 6, row_algo, 1, 1); row_algo += 1
        
        self.check_bresenham = Gtk.CheckButton(label="Брезенхем (Синий)"); grid.attach(self.check_bresenham, 6, row_algo, 1, 1); row_algo += 1
        self.check_circle = Gtk.CheckButton(label="Окр. Брезенхема (Фиол.)"); grid.attach(self.check_circle, 6, row_algo, 1, 1); row_algo += 1
        
        self.check_antialiased = Gtk.CheckButton(label="Сглаженный (Черный)"); grid.attach(self.check_antialiased, 6, row_algo, 1, 1); row_algo += 1
        
        row_buttons = max(row, row_algo)
        button_draw = Gtk.Button(label="Нарисовать (Пошагово)")
        button_draw.connect("clicked", self.on_draw_clicked)
        grid.attach(button_draw, 0, row_buttons, 3, 1)

        button_clear = Gtk.Button(label="Очистить")
        button_clear.connect("clicked", self.on_clear_clicked)
        grid.attach(button_clear, 3, row_buttons, 3, 1)
        
        self.button_draw_real = Gtk.Button(label="Наложить 'реальную' линию")
        self.button_draw_real.connect("clicked", self.on_draw_real_clicked)
        grid.attach(self.button_draw_real, 6, row_buttons, 1, 1)

    def _process_next_task(self):
        if self.current_timeout_id is not None:
            GObject.source_remove(self.current_timeout_id)
            self.current_timeout_id = None
            
        if not self.drawing_tasks:
            return False

        generator, color, alpha = self.drawing_tasks.pop(0)

        def step():
            try:
                result = next(generator)
                
                if len(result) == 3:
                    x, y, alpha_custom = result
                    self._set_pixel_instant(x, y, color, alpha_custom) 
                else:
                    x, y = result
                    self._set_pixel_instant(x, y, color, alpha) 
                
                self.drawing_area.queue_draw()
                
                return True
            except StopIteration:
                self.current_timeout_id = None
                self.drawing_area.queue_draw()

                GObject.idle_add(self._process_next_task) 
                return False 

        self.step_delay = self.delay_spin.get_value()
        delay_ms = int(self.step_delay * 1000)
        
        self.current_timeout_id = GObject.timeout_add(delay_ms, step)
        return False 

    def clear_canvas(self):
        self.pixel_data[:, :, :] = 255 
        
    def _set_pixel_instant(self, x, y, color=(0, 0, 0), alpha=180):
        x = int(x)
        y = int(y)
        alpha = min(255, max(0, int(alpha)))
        
        if 0 <= x < self.CANVAS_WIDTH and 0 <= y < self.CANVAS_HEIGHT:
            b_new, g_new, r_new = color
            b_current, g_current, r_current, a_current = self.pixel_data[y, x]
            
            alpha_new_norm = alpha / 255.0

            is_white_background = (a_current == 255 and 
                                   b_current == 255 and 
                                   g_current == 255 and 
                                   r_current == 255)
            
            if is_white_background:
                b_out = int(b_new * alpha_new_norm + b_current * (1 - alpha_new_norm))
                g_out = int(g_new * alpha_new_norm + g_current * (1 - alpha_new_norm))
                r_out = int(r_new * alpha_new_norm + r_current * (1 - alpha_new_norm))
                
                a_out = 255 # Фон остается непрозрачным
            else:
                b_out = min(255, b_current + b_new)
                g_out = min(255, g_current + g_new)
                r_out = min(255, r_current + r_new)
                a_out = min(255, a_current + alpha) 

            self.pixel_data[y, x, 0] = b_out # B
            self.pixel_data[y, x, 1] = g_out # G
            self.pixel_data[y, x, 2] = r_out # R
            self.pixel_data[y, x, 3] = a_out # A 


    def draw_gappy_line_generator(self, x1, y1, x2, y2):
        dx = x2 - x1
        dy = y2 - y1
        
        if dx == 0:
            for y in range(min(y1, y2), max(y1, y2) + 1):
                yield x1, y
            return

        k = dy / dx # Угловой коэффициент
        sx = 1 if dx > 0 else -1
        
        y = float(y1)
        y_step = k * sx 
        
        for x in range(x1, x2 + sx, sx):
            yield x, round(y)
            y += y_step 


    def draw_dda_generator(self, x1, y1, x2, y2):
        dx = x2 - x1
        dy = y2 - y1
        steps = max(abs(dx), abs(dy))
        
        if steps == 0:
            yield x1, y1
            return

        x_inc = dx / steps
        y_inc = dy / steps
        
        x = float(x1)
        y = float(y1)
        
        for _ in range(int(steps) + 1):
            yield round(x), round(y)
            x += x_inc
            y += y_inc


    def draw_bresenham_line_generator(self, x1, y1, x2, y2):
        """Алгоритм Брезенхема для линии - Генератор"""
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        sx = 1 if x1 < x2 else -1
        sy = 1 if y1 < y2 else -1
        err = dx - dy
        x = x1
        y = y1

        while True:
            yield x, y
            if x == x2 and y == y2:
                break
            
            e2 = 2 * err
            
            if e2 > -dy:
                err -= dy
                x += sx
            if e2 < dx:
                err += dx
                y += sy

    def draw_circle_points_generator(self, cx, cy, x, y):
        yield cx + x, cy + y
        yield cx - x, cy + y
        yield cx + x, cy - y
        yield cx - x, cy - y
        
        if x != y:
            yield cx + y, cy + x
            yield cx - y, cy + x
            yield cx + y, cy - x
            yield cx - y, cy - x

    def draw_bresenham_circle_generator(self, cx, cy, r):
        x = 0
        y = r
        d = 3 - 2 * r # Начальный параметр решения

        yield from self.draw_circle_points_generator(cx, cy, x, y)

        while x < y:
            if d < 0:
                d = d + 4 * x + 6
            else:
                d = d + 4 * (x - y) + 10
                y -= 1
            x += 1
            yield from self.draw_circle_points_generator(cx, cy, x, y)

    def draw_antialiased_line_generator(self, x1, y1, x2, y2):
        """
        Алгоритм сглаживания Ву (исправленная версия с корректным обменом осей). 
        Генерирует (x, y, alpha) для пикселей с разной прозрачностью.
        """
        
        def fpart(x): return x - math.floor(x) # Дробная часть
        def rfpart(x): return 1 - fpart(x) # 1 - дробная часть (близость к целому)

        steep = abs(y2 - y1) > abs(x2 - x1)
        
        if steep:
            x1, y1 = y1, x1
            x2, y2 = y2, x2 
            
        if x1 > x2:
            x1, x2 = x2, x1
            y1, y2 = y2, y1
            
        dx = x2 - x1
        dy = y2 - y1
        gradient = dy / dx if dx != 0 else 0
        
        y = float(y1)
        for x in range(x1, x2 + 1):
            
            y_int = int(math.floor(y)) 
            
            alpha1 = int(rfpart(y) * 255) 
            
            alpha2 = int(fpart(y) * 255) 

            
            if steep:
                yield y_int, x, alpha1 # y, x
            else:
                yield x, y_int, alpha1 # x, y
            
            if steep:
                yield y_int + 1, x, alpha2 # y+1, x
            else:
                yield x, y_int + 1, alpha2 # x, y+1

            y += gradient

    def on_scale_changed(self, spin_button):
        self.pixel_scale = int(spin_button.get_value())
        self.drawing_area.queue_draw()

    def on_draw_real_clicked(self, widget):
        self.is_real_line_active = not self.is_real_line_active
        
        if self.is_real_line_active:
             self.button_draw_real.set_label("Скрыть 'реальную' линию")
        else:
             self.button_draw_real.set_label("Наложить 'реальную' линию")
             
        self.drawing_area.queue_draw()

    def on_resize_clicked(self, widget):
        """Обработчик изменения размеров поля."""
        try:
            new_width = int(self.width_entry.get_text())
            new_height = int(self.height_entry.get_text())
            
            if new_width < 10 or new_height < 10 or new_width > 200 or new_height > 200:
                print("Ошибка: Размеры поля должны быть от 10 до 200.")
                return

            self.on_clear_clicked(widget=None) 
            
            self.CANVAS_WIDTH = new_width
            self.CANVAS_HEIGHT = new_height
            
            self.pixel_data = np.zeros((self.CANVAS_HEIGHT, self.CANVAS_WIDTH, 4), dtype=np.uint8)
            self.clear_canvas()
            
            self.drawing_area.queue_draw()

        except ValueError:
            print("Ошибка: Введите корректные целые числа для размеров поля.")

    def on_draw_clicked(self, widget):
        self.on_clear_clicked(widget=widget) 
        self.drawing_tasks = [] # Очищаем очередь задач

        try:
            x1 = int(self.x1_entry.get_text()); y1 = int(self.y1_entry.get_text())
            x2 = int(self.x2_entry.get_text()); y2 = int(self.y2_entry.get_text())
            r = int(self.radius_entry.get_text()); cx = int(self.cx_entry.get_text()); cy = int(self.cy_entry.get_text())

            LINE_ALPHA = 180
            RED_COLOR = (0, 0, 100) # Пошаговый
            GREEN_COLOR = (0, 100, 0) # DDA
            BLUE_COLOR = (100, 0, 0) # Bresenham Line
            PURPLE_COLOR = (100, 0, 100) # Bresenham Circle
            BLACK_COLOR = (0, 0, 0) # Antialiased (Черный)
            
            if self.check_sequential.get_active():
                generator = self.draw_gappy_line_generator(x1, y1, x2, y2)
                self.drawing_tasks.append((generator, RED_COLOR, LINE_ALPHA))
            
            if self.check_dda.get_active():
                generator = self.draw_dda_generator(x1, y1, x2, y2)
                self.drawing_tasks.append((generator, GREEN_COLOR, LINE_ALPHA))

            if self.check_bresenham.get_active():
                generator = self.draw_bresenham_line_generator(x1, y1, x2, y2)
                self.drawing_tasks.append((generator, BLUE_COLOR, LINE_ALPHA))

            if self.check_circle.get_active():
                generator = self.draw_bresenham_circle_generator(cx, cy, r)
                self.drawing_tasks.append((generator, PURPLE_COLOR, LINE_ALPHA))

            if self.check_antialiased.get_active():
                generator = self.draw_antialiased_line_generator(x1, y1, x2, y2)
                self.drawing_tasks.append((generator, BLACK_COLOR, 255)) 

            if self.drawing_tasks:
                GObject.idle_add(self._process_next_task)
            else:
                self.drawing_area.queue_draw()

        except ValueError:
            print("Ошибка: Введите корректные числа для координат и радиуса.")

    def on_clear_clicked(self, widget):
        if self.current_timeout_id is not None:
            GObject.source_remove(self.current_timeout_id)
            self.current_timeout_id = None
        
        self.drawing_tasks = [] # Очищаем очередь задач
        self.clear_canvas()
        self.drawing_area.queue_draw()

    def on_draw(self, widget, cr):
        allocated_width = widget.get_allocated_width()
        allocated_height = widget.get_allocated_height()

        scale = self.pixel_scale 
        
        centered_width = self.CANVAS_WIDTH * scale
        centered_height = self.CANVAS_HEIGHT * scale
        
        offset_x = (allocated_width - centered_width) / 2
        offset_y = (allocated_height - centered_height) / 2
        
        cr.save()
        cr.translate(offset_x, offset_y)
        cr.scale(scale, scale)

        cr.rectangle(0, 0, self.CANVAS_WIDTH, self.CANVAS_HEIGHT)
        cr.clip()
        
        
        surface = cairo.ImageSurface.create_for_data(
            self.pixel_data.data,
            cairo.Format.ARGB32, 
            self.CANVAS_WIDTH,
            self.CANVAS_HEIGHT,
            self.CANVAS_WIDTH * 4
        )
        cr.set_source_surface(surface, 0, 0)
        pattern = cr.get_source()
        pattern.set_filter(cairo.FILTER_NEAREST) 
        cr.paint()
        
        cr.set_source_rgb(0.8, 0.8, 0.8)
        cr.set_line_width(1 / scale) 
        
        for i in range(self.CANVAS_WIDTH + 1):
            cr.move_to(i, 0); cr.line_to(i, self.CANVAS_HEIGHT)
        for j in range(self.CANVAS_HEIGHT + 1):
            cr.move_to(0, j); cr.line_to(self.CANVAS_WIDTH, j)
            
        cr.stroke()

        if self.is_real_line_active:
             try:
                x1 = float(self.x1_entry.get_text()); y1 = float(self.y1_entry.get_text())
                x2 = float(self.x2_entry.get_text()); y2 = float(self.y2_entry.get_text())

                cr.set_source_rgb(0.0, 0.0, 1.0) # Синий цвет
                cr.set_line_width(0.2) 
                cr.move_to(x1 + 0.5, y1 + 0.5) 
                cr.line_to(x2 + 0.5, y2 + 0.5)
                cr.stroke()
             except ValueError:
                pass
        
        cr.restore() # Восстанавливаем контекст

        cr.save()
        cr.translate(offset_x, offset_y)
        
        cr.set_source_rgb(1.0, 1.0, 1.0) # Белый
        font_size = max(10, scale * 0.7) 
        cr.set_font_size(font_size)
        label_step = 5 
        
        for i in range(0, self.CANVAS_WIDTH + 1, label_step):
            text = str(i)
            _, _, width, height, _, _ = cr.text_extents(text)
            cr.move_to(i * scale - width / 2, -10) # Увеличенный отступ от верхнего края
            cr.show_text(text)

        for j in range(0, self.CANVAS_HEIGHT + 1, label_step):
            text = str(j)
            _, _, width, height, _, _ = cr.text_extents(text)
            cr.move_to(-width - 10, j * scale + height / 3) # Увеличенный отступ слева
            cr.show_text(text)

        cr.restore() 


if __name__ == '__main__':
    win = RasterApp()
    win.show_all()
    Gtk.main()