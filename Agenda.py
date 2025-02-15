import tkinter as tk
from tkinter import PhotoImage, filedialog
from tkinter import *
from tkcalendar import Calendar
from PIL import Image, ImageGrab, ImageDraw, ImageFont, ImageTk
from fpdf import FPDF
from datetime import datetime
import json
import locale
import os
import pyautogui

locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')

class CEntry(Entry):
    def __init__(self, parent, *args, **kwargs):
        Entry.__init__(self, parent, *args, **kwargs)

        self.undo_stack = [""]
        self.redo_stack = []
        self.steps = 0 

        self.bind("<Control-z>", self.undo)
        self.bind("<Control-y>", self.redo)
        self.bind("<KeyRelease>", self.add_changes)
    
    def undo(self, event=None):
        if self.steps > 0:

            self.redo_stack.append(self.undo_stack[self.steps])
            self.steps -= 1

            self.delete(0, END)
            self.insert(END, self.undo_stack[self.steps])

    def redo(self, event=None):
        if self.redo_stack:
            self.steps += 1
            if self.steps >= len(self.undo_stack):
                self.undo_stack.append(self.redo_stack[-1])
            else:
                self.undo_stack[self.steps] = self.redo_stack[-1]

            self.delete(0, END)
            self.insert(END, self.redo_stack.pop())

    def add_changes(self, event=None):
        current_text = self.get()
        
        if not self.undo_stack or current_text != self.undo_stack[self.steps]:
            if self.steps < len(self.undo_stack) - 1:
                self.undo_stack = self.undo_stack[:self.steps + 1]

            self.undo_stack.append(current_text)
            self.steps += 1

            self.redo_stack.clear()
            
class App(tk.Tk):
    def __init__(self):
        tk.Tk.__init__(self)
        self.title("Agenda")
        self.canvas = tk.Frame(self, width=900, height=980, bg="#282a36")
        self.resizable(False, False)
        self.focus()
        self.centralizar_janela()
        self.saved_geometry = None

        try:
            self.icon_image = PhotoImage(file="assets/agenda_icon.png")
            self.iconphoto(True, self.icon_image)
        except Exception as e:
            print("Erro ao carregar ícone:", e)

        self.data_selecionada = None
        self.dia_label = None
        self.mes_label = None
        self.ano_label = None

        # self, master, label_text, x_label, y_label, width_label, height_label, x_input, y_input, width_input, height_input, num_lines, max_chars
        self.create_labeled_input_area(self, "ORÇAMENTOS ENVIADOS:", 30, 80, 320, 28, 30, 100, 320, 200, 10, 32)
        self.create_labeled_input_area(self, "PEDIDO:", 360, 80, 320, 28, 360, 100, 320, 200, 10, 32)
        self.create_labeled_input_area(self, "ARQUIVOS PRODUZIDOS:", 30, 310, 320, 28, 30, 330, 320, 200, 10, 32)
        self.create_labeled_input_area(self, "EM CONTATO:", 360, 310, 320, 28, 360, 330, 320, 380, 19, 32)
        self.create_labeled_input_area(self, "ATEND. BALCÃO:", 30, 540, 140, 28, 30, 560, 140, 60, 3, 12)
        self.create_labeled_input_area(self, "VISITAS:", 30, 630, 140, 28, 30, 650, 140, 60, 3, 12)
        self.create_labeled_input_area(self, "PROSPECÇÃO:", 180, 540, 170, 28, 180, 560, 170, 150, 6, 16)
        self.create_labeled_input_area(self, "PENDÊNCIAS:", 30, 720, 650, 28, 30, 740, 650, 220, 10, 69)

        self.current_color = "#282a36"
        self.current_color_label = "#6d6e70"
        self.screenInformation()

        self.calendar_button = tk.Button(self, text="Abrir Calendário", command=self.open_calendar, width=15, height=2, font=("Arial", 10, "bold"), cursor='hand2')
        self.calendar_button.place(x=712, y=80)

        self.buttonPDF = tk.Button(self, text="Exportar como PDF", command=self.generate_pdf, width=15, height=2, font=("Arial", 10, "bold"), cursor='hand2')
        self.buttonPDF.place(x=712, y=140)

        self.buttonPNG = tk.Button(self, text="Exportar como PNG", command=self.generate_png, width=15, height=2, font=("Arial", 10, "bold"), cursor='hand2')
        self.buttonPNG.place(x=712, y=200)

        self.suggested_colors = ["#282a36", "#484444", "#959595", "#c8c8c8"]
        self.create_color_buttons()
        self.color_change_cooldown = False

        self.bind("<Control-s>", self.save_data)
        
        self.canvas.pack()
        self.after(100, self.focus_set) 

        self.carregar_dados()
        self.auto_save_data()

    def create_color_buttons(self):
        for i, color in enumerate(self.suggested_colors):
            color_button = tk.Button(self, bg=color, width=3, height=1, command=lambda color=color: self.change_canvas_color_to(color), cursor='hand2')
            color_button.place(x=715 + (i % 5) * 40, y=925 + (i // 5) * 40)
            
    def change_canvas_color_to(self, color_code):
        if self.color_change_cooldown or self.current_color == color_code:
            return
        
        if hasattr(self, 'calendar_window') and self.calendar_window and self.calendar_window.winfo_exists():
            self.on_calendar_close()

        self.color_change_cooldown = True
        self.after(200, self.reset_color_cooldown)

        self.current_color = color_code
        self.canvas.config(bg=color_code)
        
        button_fg = "#FFFFFF" if color_code in ["#959595", "#c8c8c8"] else "#000000"
        button_bg = "#7a7a7a" if color_code in ["#959595", "#c8c8c8"] else "#E0E0E0"

        self.calendar_button.config(bg=button_bg, fg=button_fg)
        self.buttonPDF.config(bg=button_bg, fg=button_fg)
        self.buttonPNG.config(bg=button_bg, fg=button_fg)

        if color_code == "#282a36":
            self.current_color_label = "#6d6e70" 
        elif color_code == "#484444":
            self.current_color_label = "#282a36"
        elif color_code == "#959595":
            self.current_color_label = "#c8c8c8"
        elif color_code == "#c8c8c8":
            self.current_color_label = "#959595"
        
        if self.dia_label:
            self.dia_label.config(bg=color_code)
        if self.weekday_label:
            self.weekday_label.config(bg=color_code)
        if self.ano_label:
            self.ano_label.config(bg=color_code)

        self.screenInformation()

    def reset_color_cooldown(self):
        self.color_change_cooldown = False

    def auto_save_data(self):
        self.salvar_dados()
        self.after(1000, self.auto_save_data)

    def save_data(self, event=None):
        self.salvar_dados()   

    def salvar_dados(self):
        if not self.data_selecionada:
            return

        dados = {}
        for label, entries in self.dados_entries.items():
            dados[label] = [entry.get() for entry in entries]

        arquivo_json = 'dados.json'

        if os.path.exists(arquivo_json):
            with open(arquivo_json, 'r', encoding='utf-8') as f:
                dados_existentes = json.load(f)
        else:
            dados_existentes = {}

        dados_existentes[self.data_selecionada.strftime('%d%m%Y')] = dados

        with open(arquivo_json, 'w', encoding='utf-8') as f:
            json.dump(dados_existentes, f, ensure_ascii=False, indent=4)

    def carregar_dados(self):
        if not self.data_selecionada:
            self.data_selecionada = datetime.today()

        arquivo_json = 'dados.json'

        if not os.path.exists(arquivo_json):
            return

        with open(arquivo_json, 'r', encoding='utf-8') as f:
            dados_existentes = json.load(f)

        data_str = self.data_selecionada.strftime('%d%m%Y')
        if data_str not in dados_existentes:
            for label, entries in self.dados_entries.items():
                for entry in entries:
                    entry.delete(0, tk.END)

            return

        dados = dados_existentes[data_str]

        for label, values in dados.items():
            entries = self.dados_entries.get(label, [])
            for entry, value in zip(entries, values):
                entry.delete(0, tk.END)
                entry.insert(0, value)
    
    def load_logo(self, logo_path):
        try:
            self.logo_image = Image.open(logo_path)
            self.logo_image = self.logo_image.resize((110, 60))
            self.logo_image_tk = ImageTk.PhotoImage(self.logo_image)
            
            self.logo_label = tk.Label(self, image=self.logo_image_tk, bg=self.current_color)
            self.logo_label.image = self.logo_image_tk 
            self.logo_label.place(x=16, y=10) 
        except Exception as e:
            print("Erro ao carregar a imagem:", e)

    def screenInformation(self):
        if self.current_color in ["#282a36", "#484444"]:
            self.load_logo("assets/logo1.png")
        elif self.current_color in ["#959595", "#c8c8c8"]:
            self.load_logo("assets/logo2.png")

        self.criar_labels_data()

    def centralizar_janela(self):
        screen_width = self.winfo_screenwidth() + 1000
        screen_height = self.winfo_screenheight() - 200

        window_width = 900
        window_height = 980

        new_x = max(0, min((screen_width - window_width) // 2, screen_width - window_width))
        new_y = max(0, min((screen_height - window_height) // 2, screen_height - window_height))

        self.geometry(f"{window_width}x{window_height}+{new_x}+{new_y}")

    def open_calendar(self):
        if hasattr(self, 'calendar_window') and self.calendar_window and self.calendar_window.winfo_exists():
            self.calendar_window.lift()
            return

        self.calendar_window = tk.Toplevel(self)
        self.calendar_window.title("Calendário")
        self.calendar_window.resizable(False, False)

        if self.current_color in ["#282a36", "#484444"]:
            self.calendar_window.config(bg=self.current_color)
            calendar = Calendar(self.calendar_window, selectmode="day", date_pattern="dd/mm/yyyy", locale='pt_BR', background=self.current_color)
            calendar.pack(pady=(10, 5))

            calendar.bind("<Enter>", lambda e: calendar.config(cursor="hand2"))
            calendar.bind("<Leave>", lambda e: calendar.config(cursor=""))

            select_button = tk.Button(
                self.calendar_window, 
                text="Confirmar", 
                command=lambda: self.set_selected_date(calendar.get_date(), self.calendar_window), 
                cursor='hand2',
                font=("Arial", 10, "bold"),
                bg="#E0E0E0",
                fg="#000000"
            )

        elif self.current_color in ["#959595", "#c8c8c8"]:
            self.calendar_window.config(bg=self.current_color)
            calendar = Calendar(self.calendar_window, selectmode="day", date_pattern="dd/mm/yyyy", locale='pt_BR', background=self.current_color)
            calendar.pack(pady=(10, 5))

            calendar.bind("<Enter>", lambda e: calendar.config(cursor="hand2"))
            calendar.bind("<Leave>", lambda e: calendar.config(cursor=""))

            select_button = tk.Button(
                self.calendar_window, 
                text="Confirmar", 
                command=lambda: self.set_selected_date(calendar.get_date(), self.calendar_window), 
                cursor='hand2',
                font=("Arial", 10, "bold"),
                bg="#484444",
                fg="#FFFFFF"
            )

        select_button.pack(pady=2)

        self.calendar_window.protocol("WM_DELETE_WINDOW", self.on_calendar_close)

        x_pos = self.winfo_x() + self.winfo_width() - self.calendar_window.winfo_reqwidth() - 80
        y_pos = self.winfo_y()

        self.calendar_window.geometry(f"+{x_pos}+{y_pos}")

    def on_calendar_close(self):
        self.calendar_window.destroy()
        self.calendar_window = None

    def set_selected_date(self, selected_date, calendar_window):
        self.data_selecionada = datetime.strptime(selected_date, "%d/%m/%Y")
        self.criar_labels_data()
        self.carregar_dados()
        calendar_window.destroy()
        self.change_canvas_color_to(self.current_color)

    def criar_labels_data(self):
        self.dias_da_semana = ["segunda-feira", "terça-feira", "quarta-feira", "quinta-feira", "sexta-feira", "sábado", "domingo"]
        
        if self.dia_label:
            self.dia_label.destroy()
        if self.mes_label:
            self.mes_label.destroy()
        if self.ano_label:
            self.ano_label.destroy()

        today = datetime.today() if not self.data_selecionada else self.data_selecionada
        day_number = today.day
        weekday = self.dias_da_semana[today.weekday()].capitalize()
        month = today.strftime("%b").upper()
        year = today.year

        self.ano_label = self.create_text_with_border(str(year), font=("Arial Black", 35, "bold"), x=745, y=14)

        self.dia_label = self.create_text_with_border(str(day_number), font=("Arial Black", 50, "bold"), x=140, y=-30, width=80, height=100)

        self.weekday_label = self.create_text_with_border(weekday, font=("Arial Black", 30), x=270, y=-10, width=260, height=80)

        self.create_rotated_label(self, month, 630, 0, 69, 100, bg_color=self.current_color_label, angle=90)

    def create_text_with_border(self, text, font, x, y, width=None, height=None, border_thickness=1):
        image = Image.new("RGBA", (width if width else 200, height if height else 50), (255, 255, 255, 0))
        draw = ImageDraw.Draw(image)

        font = ImageFont.truetype("ariblk.ttf", 28) if not font else ImageFont.truetype("ariblk.ttf", font[1])

        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        text_x = (width - text_width) // 2 if width else 0
        text_y = (height - text_height) // 2 if height else 0

        if self.current_color == "#282a36":
            text_color = "white"
            border_color = "#282a36"
        elif self.current_color == "#484444":
            text_color = "white"
            border_color = "#484444"
        elif self.current_color == "#959595":
            text_color = "#282a36"
            border_color = "#959595"                
        elif self.current_color == "#c8c8c8":
            text_color = "#282a36"
            border_color = "#c8c8c8"

        for dx in range(-border_thickness, border_thickness + 1):
            for dy in range(-border_thickness, border_thickness + 1):
                if dx != 0 or dy != 0:
                    draw.text((text_x + dx, text_y + dy), text, font=font, fill=border_color)

        draw.text((text_x, text_y), text, font=font, fill=text_color)
        
        image_tk = ImageTk.PhotoImage(image)
        
        label = tk.Label(self, image=image_tk, bd=0, highlightthickness=0, bg=self.current_color)
        label.image = image_tk
        label.place(x=x, y=y, width=width, height=height)

        return label

    def move_focus(self, event, entries, current_index, direction):
        new_index = current_index + direction
        if 0 <= new_index < len(entries):
            entries[new_index].focus_set()
            
    def create_labeled_input_area(self, master, label_text, x_label, y_label, width_label, height_label, x_input, y_input, width_input, height_input, num_lines, max_chars):
        label = tk.Label(master, text=label_text, bg="white", anchor="center", font=("Arial", 9, "bold"))
        label.place(x=x_label, y=y_label, width=width_label, height=height_label)

        canvas = tk.Canvas(master, bg="white", bd=0, highlightthickness=0)
        canvas.place(x=x_input, y=y_input, width=width_input, height=height_input)

        line_height = height_input // num_lines
        margin = 14
        entries = []

        def limit_chars_input(char, value):
            count = 0
            for c in value:
                if c == " ":
                    count += 0.5
                else:
                    count += 1
            if count > max_chars:
                return False
            return True
        
        for i in range(1, num_lines + 1):
            canvas.create_line(margin, i * line_height, width_input - margin, i * line_height, fill="black", width=2)

            entry = CEntry(master, bd=0, font=("Arial", 10), fg="black", bg="white")
            entry.place(x=x_input + margin, y=y_input + (i - 1) * line_height + 2, width=width_input - 2 * margin, height=line_height - 2)
            
            entry.config(validate="key", validatecommand=(master.register(limit_chars_input), '%S', '%P'))
            entries.append(entry)

            entry.bind("<Up>", lambda event, idx=i-1: self.move_focus(event, entries, idx, -1))
            entry.bind("<Down>", lambda event, idx=i-1: self.move_focus(event, entries, idx, 1))
            entry.bind("<Return>", lambda event, idx=i-1: self.move_focus(event, entries, idx, 1))

        if entries:
            entries[0].focus_set()

        if not hasattr(self, 'dados_entries'):
            self.dados_entries = {}

        self.dados_entries[label_text] = entries

        return canvas

    def create_rotated_label(self, master, text, x, y, width, height, bg_color, angle=90):
        image = Image.new("RGBA", (width, height), bg_color)
        draw = ImageDraw.Draw(image)

        font = ImageFont.truetype("ariblk.ttf", 30)
        
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        text_x = (width - text_width) // 2
        text_y = (height - text_height - 25) // 2

        outline_offset = 1
        for offset_x in [-outline_offset, 0, outline_offset]:
            for offset_y in [-outline_offset, 0, outline_offset]:
                if offset_x != 0 or offset_y != 0:
                    draw.text((text_x + offset_x, text_y + offset_y), text, font=font, fill=self.current_color_label)

        
        if self.current_color in ["#282a36", "#484444"]:
            draw.text((text_x, text_y), text, font=font, fill="white")
        
        elif self.current_color in ["#959595", "#c8c8c8"]:
            draw.text((text_x, text_y), text, font=font, fill="#282a36")

        rotated_image = image.rotate(angle, expand=True)

        rotated_image_tk = ImageTk.PhotoImage(rotated_image)

        label = tk.Label(master, image=rotated_image_tk, bd=0, highlightthickness=0, bg=bg_color)
        label.image = rotated_image_tk
        label.place(x=x, y=y, width=width, height=height)

        return label
    
    def save_window_position(self):
        self.saved_geometry = self.geometry()

    def restore_window_position(self):
        if self.saved_geometry:
            self.geometry(self.saved_geometry)

    def generate_pdf(self):
        self.save_window_position()
        if self.data_selecionada:
            default_filename = self.data_selecionada.strftime("%d%m%Y") + ".pdf"
        else:
            default_filename = datetime.today().strftime("%d%m%Y") + ".pdf"
        
        pdf_path = filedialog.asksaveasfilename(
            initialfile=default_filename,
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
            title="Select Destination for PDF"
        )
        
        if not pdf_path:
            return
        
        screen_width = self.winfo_screenwidth() 
        screen_height = self.winfo_screenheight() 

        new_x = (screen_width - self.winfo_width()) // 2
        new_y = (screen_height - self.winfo_height()) - 200 // 2

        self.geometry(f"+{new_x}+{new_y}")
        self.focus_set()
        self.update()

        x = self.winfo_rootx()
        y = self.winfo_rooty()
        width = self.winfo_width()
        height = self.winfo_height()

        img = ImageGrab.grab(bbox=(x, y, x + width - 198, y + height))

        img_path = "tmp_image.png"
        img.save(img_path)

        pdf = FPDF()
        pdf.add_page()
        
        img_width, img_height = img.size
        aspect_ratio = img_width / img_height
        pdf_width = 210
        pdf_height = 297
        new_width = pdf_width
        new_height = new_width / aspect_ratio
        if new_height > pdf_height:
            new_height = pdf_height
            new_width = new_height * aspect_ratio

        pdf.image(img_path, x=0, y=0, w=new_width, h=new_height + 5)

        pdf.output(pdf_path)

        os.remove(img_path)

        self.restore_window_position()

    def generate_png(self):
        self.save_window_position()
        if self.data_selecionada:
            default_filename = self.data_selecionada.strftime("%d%m%Y") + ".png"
        else:
            default_filename = datetime.today().strftime("%d%m%Y") + ".png"
        
        png_path = filedialog.asksaveasfilename(
            initialfile=default_filename,
            defaultextension=".png",
            filetypes=[("PNG files", "*.png")],
            title="Select Destination for PNG"
        )
        
        if not png_path:
            return
        
        screen_width = self.winfo_screenwidth() 
        screen_height = self.winfo_screenheight() 

        new_x = (screen_width - self.winfo_width()) // 2
        new_y = (screen_height - self.winfo_height()) - 200 // 2

        self.geometry(f"+{new_x}+{new_y}")
        self.focus_set()
        self.update()

        x = self.winfo_rootx()
        y = self.winfo_rooty()
        width = self.winfo_width()
        height = self.winfo_height()

        img = ImageGrab.grab(bbox=(x + 10, y, x + width - 200, y + height))

        img.save(png_path)

        self.restore_window_position()

app = App()
app.mainloop()
