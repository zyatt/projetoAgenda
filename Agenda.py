import tkinter as tk
from tkinter import filedialog, messagebox, PhotoImage
from tkcalendar import Calendar
from PIL import Image, ImageGrab, ImageDraw, ImageFont, ImageTk
from fpdf import FPDF
from datetime import datetime
import json
import locale
import os
import pyautogui

locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')

class App(tk.Tk):
    def __init__(self):
        tk.Tk.__init__(self)
        self.title("Agenda")
        self.canvas = tk.Frame(self, width=800, height=780, bg="#484444")
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
        
        self.create_labeled_input_area(self, "ORÇAMENTOS ENVIADOS:", 25, 80, 271, 20, 25, 100, 271, 140, 7, 27)
        self.create_labeled_input_area(self, "PEDIDO:", 304, 80, 276, 20, 304, 100, 276, 140, 7, 28)
        self.create_labeled_input_area(self, "ARQUIVOS PRODUZIDOS:", 25, 247, 271, 20, 25, 267, 271, 140, 7, 27)
        self.create_labeled_input_area(self, "EM CONTATO:", 304, 247, 276, 20, 304, 267, 276, 315, 16, 28)
        self.create_labeled_input_area(self, "ATEND. BALCÃO:", 25, 415, 132, 25, 25, 435, 132, 60, 3, 12)
        self.create_labeled_input_area(self, "VISITAS:", 25, 502, 132, 20, 25, 522, 132, 60, 3, 12)
        self.create_labeled_input_area(self, "PROSPECÇÃO:", 165, 415, 130, 20, 165, 435, 130, 147, 7, 12)
        self.create_labeled_input_area(self, "PENDÊNCIAS:", 25, 590, 555, 20, 25, 610, 555, 140, 7, 60)

        self.criar_labels_data()

        self.button = tk.Button(self, text="Exportar", command=self.generate_pdf, width=18, height=1)
        self.button.place(x=616, y=140)
        self.calendar_button = tk.Button(self, text="Abrir Calendário", command=self.open_calendar, width=18, height=1)
        self.calendar_button.place(x=616, y=80)

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
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()

        window_width = 800
        window_height = 780

        new_x = max(0, min((screen_width - window_width) // 2, screen_width - window_width))
        new_y = max(0, min((screen_height - window_height) // 2, screen_height - window_height))

        self.geometry(f"{window_width}x{window_height}+{new_x}+{new_y}")

    def open_calendar(self):
        if hasattr(self, 'calendar_window') and self.calendar_window.winfo_exists():
            return

        self.calendar_window = tk.Toplevel(self)
        self.calendar_window.title("Selecione a Data")

        calendar = Calendar(self.calendar_window, selectmode="day", date_pattern="dd/mm/yyyy", locale='pt_BR')
        calendar.pack(pady=20)

        select_button = tk.Button(self.calendar_window, text="Confirmar", command=lambda: self.set_selected_date(calendar.get_date(), self.calendar_window))
        select_button.pack()

        self.calendar_window.protocol("WM_DELETE_WINDOW", self.on_calendar_close)

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

    def move_focus(self, event, entries, current_index, direction):
        new_index = current_index + direction
        if 0 <= new_index < len(entries):
            entries[new_index].focus_set()

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

        self.ano_label = tk.Label(self, text=str(year), bg="#484444", fg="white", font=("Arial Black", 20, "bold"))
        self.ano_label.place(x=644, y=10)

        self.dia_label = tk.Label(self, text=str(day_number), bg="#484444", fg="white", font=("Arial Black", 30, "bold"))
        self.dia_label.place(x=150, y=10, width=80, height=60)

        self.weekday_label = tk.Label(self, text=weekday, bg="#484444", fg="white", font=("Arial Black", 15))
        self.weekday_label.place(x=240, y=20, width=260, height=40)

        self.create_rotated_label(self, month, 540, 0, 65, 100, angle=90)

    def create_labeled_input_area(self, master, label_text, x_label, y_label, width_label, height_label, x_input, y_input, width_input, height_input, num_lines, max_chars):
        label = tk.Label(master, text=label_text, bg="white", anchor="center", font=("Arial", 9, "bold"))
        label.place(x=x_label, y=y_label, width=width_label, height=height_label)

        canvas = tk.Canvas(master, bg="white", bd=0, highlightthickness=0)
        canvas.place(x=x_input, y=y_input, width=width_input, height=height_input)

        line_height = height_input // num_lines
        margin = 11
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
            canvas.create_line(margin, i * line_height, width_input - margin, i * line_height, fill="black", width=1)

            entry = tk.Entry(master, bd=0, font=("Arial", 10), fg="black", bg="white")
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
        
        font = ImageFont.truetype("ariblk.ttf", 28)
        
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0] 
        text_height = bbox[3] - bbox[1]
        
        text_x = (width - text_width) // 2
        text_y = (height - text_height) // 2.8
        
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
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
            initialfile=default_filename
        )
        
        if not pdf_path:
            return

        original_x = self.winfo_rootx()
        original_y = self.winfo_rooty()

        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()

        new_x = (screen_width - self.winfo_width()) // 2
        new_y = (screen_height - self.winfo_height()) // 2

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

        pdf.image(img_path, x=0, y=0, w=new_width, h=new_height + 30)

        pdf.output(pdf_path)

        os.remove(img_path)

        self.geometry(f"+{original_x}+{original_y}")
    
app = App()
app.mainloop()
