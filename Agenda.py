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

        self.changes = [""]
        self.steps = int()

        self.context_menu = Menu(self, tearoff=0)
        self.context_menu.add_command(label="Cut")
        self.context_menu.add_command(label="Copy")
        self.context_menu.add_command(label="Paste")

        self.bind("<Button-3>", self.popup)

        self.bind("<Control-z>", self.undo)
        self.bind("<Control-y>", self.redo)

        self.bind("<Key>", self.add_changes)

    def popup(self, event):
        self.context_menu.post(event.x_root, event.y_root)
        self.context_menu.entryconfigure("Cut", command=lambda: self.event_generate("<<Cut>>"))
        self.context_menu.entryconfigure("Copy", command=lambda: self.event_generate("<<Copy>>"))
        self.context_menu.entryconfigure("Paste", command=lambda: self.event_generate("<<Paste>>"))

    def undo(self, event=None):
        if self.steps != 0:
            self.steps -= 1
            self.delete(0, END)
            self.insert(END, self.changes[self.steps])

    def redo(self, event=None):
        if self.steps < len(self.changes):
            self.delete(0, END)
            self.insert(END, self.changes[self.steps])
            self.steps += 1

    def add_changes(self, event=None):
        if self.get() != self.changes[-1]:
            self.changes.append(self.get())
            self.steps += 1

class App(tk.Tk):
    def __init__(self):
        tk.Tk.__init__(self)
        self.title("Agenda")
        self.canvas = tk.Frame(self, width=900, height=980, bg="#484444")
        self.resizable(False, False)
        self.focus()
        self.centralizar_janela()

        try:
            self.icon_image = PhotoImage(file="assets/agenda_icon.png")
            self.iconphoto(True, self.icon_image)
        except Exception as e:
            print("Erro ao carregar ícone:", e)

        self.data_selecionada = None
        self.dia_label = None
        self.mes_label = None
        self.ano_label = None

        logo_image = self.carregar_imagem()
        if logo_image:
            logo_label = tk.Label(self, image=logo_image, bd=0, highlightthickness=0)
            logo_label.place(x=10, y=10)
            logo_label.image = logo_image
        
        # self, master, label_text, x_label, y_label, width_label, height_label, x_input, y_input, width_input, height_input, num_lines, max_chars
        self.create_labeled_input_area(self, "ORÇAMENTOS ENVIADOS:", 30, 80, 320, 28, 30, 100, 320, 200, 10, 32)
        self.create_labeled_input_area(self, "PEDIDO:", 360, 80, 320, 28, 360, 100, 320, 200, 10, 32)
        self.create_labeled_input_area(self, "ARQUIVOS PRODUZIDOS:", 30, 310, 320, 28, 30, 330, 320, 200, 10, 32)
        self.create_labeled_input_area(self, "EM CONTATO:", 360, 310, 320, 28, 360, 330, 320, 380, 19, 32)
        self.create_labeled_input_area(self, "ATEND. BALCÃO:", 30, 540, 140, 28, 30, 560, 140, 60, 3, 12)
        self.create_labeled_input_area(self, "VISITAS:", 30, 630, 140, 28, 30, 650, 140, 60, 3, 12)
        self.create_labeled_input_area(self, "PROSPECÇÃO:", 180, 540, 170, 28, 180, 560, 170, 150, 6, 16)
        self.create_labeled_input_area(self, "PENDÊNCIAS:", 30, 720, 650, 28, 30, 740, 650, 220, 10, 69)
    
        self.undo_stack = []
        self.redo_stack = []
        
        self.criar_labels_data()

        self.calendar_button = tk.Button(self, text="Abrir Calendário", command=self.open_calendar, width=15, height=1, font=("Arial", 10, "bold"))
        self.calendar_button.place(x=715, y=80)

        self.buttonPDF = tk.Button(self, text="Exportar como PDF", command=self.generate_pdf, width=15, height=1, font=("Arial", 10, "bold"))
        self.buttonPDF.place(x=715, y=140)

        self.buttonPNG = tk.Button(self, text="Exportar como PNG", command=self.generate_png, width=15, height=1, font=("Arial", 10, "bold"))
        self.buttonPNG.place(x=715, y=200)

        self.bind("<Control-s>", self.save_data)
        
        self.canvas.pack()
        self.after(100, self.focus_set) 

        self.carregar_dados()
        self.auto_save_data()

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
        self.calendar_window.resizable(False,False)

        calendar = Calendar(self.calendar_window, selectmode="day", date_pattern="dd/mm/yyyy", locale='pt_BR')
        calendar.pack(pady=20)

        select_button = tk.Button(self.calendar_window, text="Confirmar", command=lambda: self.set_selected_date(calendar.get_date(), self.calendar_window))
        select_button.pack()

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

    def carregar_imagem(self):
        try:
            original_image = Image.open("assets/logo.png")
            nova_largura, nova_altura = 110, 60
            resized_image = original_image.resize((nova_largura, nova_altura), Image.LANCZOS)
            logo_image = ImageTk.PhotoImage(resized_image)
            return logo_image
        except Exception as e:
            return None

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

        self.ano_label = self.create_text_with_border(str(year), font=("Arial Black", 35, "bold"), x=752, y=10)

        self.dia_label = self.create_text_with_border(str(day_number), font=("Arial Black", 50, "bold"), x=200, y=-30, width=80, height=100)

        self.weekday_label = self.create_text_with_border(weekday, font=("Arial Black", 30), x=315, y=-10, width=260, height=80)

        self.create_rotated_label(self, month, 630, 0, 80, 100, angle=90)

    def create_text_with_border(self, text, font, x, y, width=None, height=None):
        image = Image.new("RGBA", (width if width else 200, height if height else 50), (255, 255, 255, 0))
        draw = ImageDraw.Draw(image)
        
        font = ImageFont.truetype("ariblk.ttf", 28) if not font else ImageFont.truetype("ariblk.ttf", font[1])

        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        text_x = (width - text_width) // 2 if width else 0
        text_y = (height - text_height) // 2 if height else 0
        
        draw.text((text_x - 2, text_y - 2), text, font=font, fill="black")
        draw.text((text_x + 2, text_y - 2), text, font=font, fill="black")
        draw.text((text_x - 2, text_y + 2), text, font=font, fill="black")
        draw.text((text_x + 2, text_y + 2), text, font=font, fill="black")
        
        draw.text((text_x, text_y), text, font=font, fill="white")
        
        image_tk = ImageTk.PhotoImage(image)
        
        label = tk.Label(self, image=image_tk, bd=0, highlightthickness=0, bg="#484444")
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
        margin = 12
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

            entry = tk.CEntry(master, bd=0, font=("Arial", 10), fg="black", bg="white")
            entry.place(x=x_input + margin, y=y_input + (i - 1) * line_height + 2, width=width_input - 2 * margin, height=line_height - 2)

            entry.config(validate="key", validatecommand=(master.register(limit_chars_input), '%S', '%P'))
            entries.append(entry)

            entry.bind("<Up>", lambda event, idx=i-1: self.move_focus(event, entries, idx, -1))
            entry.bind("<Down>", lambda event, idx=i-1: self.move_focus(event, entries, idx, 1))

        if entries:
            entries[0].focus_set()

        if not hasattr(self, 'dados_entries'):
            self.dados_entries = {}

        self.dados_entries[label_text] = entries

        return canvas
    
    def create_rotated_label(self, master, text, x, y, width, height, angle=90):
        image = Image.new("RGBA", (width, height), (255, 255, 255, 0))
        draw = ImageDraw.Draw(image)
        
        font = ImageFont.truetype("ariblk.ttf", 30)
        
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        text_x = (width - text_width) // 2
        text_y = (height - text_height - 30) // 2

        outline_offset = 2 
        for offset_x in [-outline_offset, 0, outline_offset]:
            for offset_y in [-outline_offset, 0, outline_offset]:
                if offset_x != 0 or offset_y != 0:
                    draw.text((text_x + offset_x, text_y + offset_y), text, font=font, fill="black")
        
        draw.text((text_x, text_y), text, font=font, fill="white")
        
        rotated_image = image.rotate(angle, expand=True)
        
        rotated_image_tk = ImageTk.PhotoImage(rotated_image)
        
        label = tk.Label(master, image=rotated_image_tk, bd=0, highlightthickness=0, bg="#6d6e70")
        label.image = rotated_image_tk
        label.place(x=x, y=y, width=width, height=height)

        return label
    
    def generate_pdf(self):
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

        self.centralizar_janela()

    def generate_png(self):
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

        img = ImageGrab.grab(bbox=(x, y, x + width - 198, y + height))

        img.save(png_path)

        self.centralizar_janela()

app = App()
app.mainloop()
