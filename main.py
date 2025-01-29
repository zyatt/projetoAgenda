import tkinter as tk
from tkinter import filedialog, messagebox
from datetime import datetime
import locale
from tkcalendar import Calendar
import pyautogui
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import numpy as np
import cv2
import json
from PIL import Image, ImageTk, ImageDraw, ImageFont

# Configura a localidade para português
locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')

# Lista com os dias da semana corrigidos
dias_da_semana = ["segunda-feira", "terça-feira", "quarta-feira", "quinta-feira", "sexta-feira", "sábado", "domingo"]

def create_labeled_input_area(master, label_text, x_label, y_label, width_label, height_label, x_input, y_input, width_input, height_input, num_lines, max_chars):
    # Criar o label
    label = tk.Label(master, text=label_text, bg="white", anchor="center", font=("Arial", 9, "bold"))
    label.place(x=x_label, y=y_label, width=width_label, height=height_label)

    # Criar o Canvas para desenhar as linhas
    canvas = tk.Canvas(master, bg="white", bd=0, highlightthickness=0)
    canvas.place(x=x_input, y=y_input, width=width_input, height=height_input)

    # Calcular o espaçamento das linhas (altura total dividida pelo número de linhas)
    line_height = height_input // num_lines
    margin = 11  # Espaço em branco antes e depois das linhas

    # Função para limitar a entrada considerando o espaço como meio caractere
    def limit_chars_input(char, value):
        count = 0
        for c in value:
            # Considera espaço como meio caractere
            if c == " ":
                count += 0.5
            else:
                count += 1
        
        if count > max_chars:
            return False
        return True

    # Desenhar as linhas no Canvas (com recuo no início e no fim)
    for i in range(1, num_lines + 1):
        canvas.create_line(margin, i * line_height, width_input - margin, i * line_height, fill="black", width=1)
        
        # Adicionar o Entry sobre cada linha (permitindo escrita)
        entry = tk.Entry(master, bd=0, font=("Arial", 10), fg="black", bg="white")
        entry.place(x=x_input + margin, y=y_input + (i - 1) * line_height + 2, width=width_input - 2 * margin, height=line_height - 2)

        # Limitar os caracteres no Entry
        entry.config(validate="key", validatecommand=(master.register(limit_chars_input), '%S', '%P'))

    return canvas

def create_rotated_label(master, text, x, y, width, height, angle=90):
    # Cria uma imagem com fundo transparente
    image = Image.new("RGBA", (width, height), (255, 255, 255, 0))  # Cria uma imagem em RGBA (com transparência)
    draw = ImageDraw.Draw(image)
    
    # Definir a fonte e tamanho para o texto
    font = ImageFont.truetype("ariblk.ttf", 30)  # Fonte e tamanho do texto
    
    # Usar textbbox em vez de textsize
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]  # Largura
    text_height = bbox[3] - bbox[1]  # Altura
    
    # Posicionar o texto no centro da imagem
    text_x = (width - text_width) // 2
    text_y = (height - text_height) // 5
    
    # Desenhar o texto na imagem
    draw.text((text_x, text_y), text, font=font, fill="white")
    
    # Rotacionar a imagem
    rotated_image = image.rotate(angle, expand=True)
    
    # Converter a imagem para o formato do Tkinter
    rotated_image_tk = ImageTk.PhotoImage(rotated_image)
    
    # Exibir a imagem rotacionada em uma label
    label = tk.Label(master, image=rotated_image_tk, bd=0, highlightthickness=0, bg="#6d6e70")
    label.image = rotated_image_tk  # Manter uma referência à imagem
    label.place(x=x, y=y, width=width, height=height)

    return label

# Dicionário para armazenar os dados da agenda
agenda_data = {}

def save_agenda_data():
    try:
        # Obter a data e hora atual para identificar o conjunto de dados
        data_id = datetime.now().strftime("%Y-%m-%d")

        # Criar um dicionário para armazenar os dados da agenda atual
        current_data = {}

        # Iterar sobre todos os widgets no frame da agenda
        for widget in agenda_frame.winfo_children():
            if isinstance(widget, tk.Entry):
                # Obter o índice (linha) do Entry
                entry_index = widget.master.winfo_children().index(widget)  # índice da linha
                label = widget.master.winfo_children()[0].cget("text")  # Obter o texto do label
                value = widget.get().strip()  # Obter o valor do campo e remover espaços

                # Se o valor estiver vazio, substituir por um caractere invisível
                if not value:
                    value = "\u200B"  # Caractere invisível (espaço não quebrável)

                # Salvar o valor no dicionário
                current_data[f"{label}_{entry_index}"] = value

        # Carregar os dados antigos, se existirem
        try:
            with open('agenda_data.json', 'r', encoding='utf-8') as f:
                agenda_data = json.load(f)
        except FileNotFoundError:
            agenda_data = {}

        # Se houver dados antigos para a data atual, vamos removê-los ou atualizar
        if data_id in agenda_data:
            # Atualiza os dados existentes com os novos
            agenda_data[data_id].update(current_data)
        else:
            # Se não existir, cria uma nova entrada para a data
            agenda_data[data_id] = current_data

        # Salvar no arquivo JSON
        with open('agenda_data.json', 'w', encoding='utf-8') as f:
            json.dump(agenda_data, f, ensure_ascii=False, indent=4)

       # messagebox.showinfo("Sucesso", "Agenda salva com sucesso!")

    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao salvar a agenda: {e}")


# Função para carregar os dados da agenda
def load_agenda_data(date_selected=None):
    global agenda_data
    try:
        with open('agenda_data.json', 'r', encoding='utf-8') as f:
            agenda_data = json.load(f)

        if date_selected:
            date_id = date_selected.strftime("%Y-%m-%d")
        else:
            date_id = sorted(agenda_data.keys())[-1]  # Pega o último conjunto de dados salvo

        # Preencher os campos da agenda com os dados salvos para a data selecionada
        if date_id in agenda_data:
            for widget in agenda_frame.winfo_children():
                if isinstance(widget, tk.Entry):
                    # Obter o índice (linha) do Entry
                    entry_index = widget.master.winfo_children().index(widget)  # índice da linha
                    label = widget.master.winfo_children()[0].cget("text")  # Obter o texto do label

                    # Tentar encontrar os dados corretos no dicionário
                    key = f"{label}_{entry_index}"
                    if key in agenda_data[date_id]:
                        widget.delete(0, tk.END)  # Limpar o campo antes de preencher
                        widget.insert(0, agenda_data[date_id][key])  # Preencher o campo com os dados salvos

    except FileNotFoundError:
        agenda_data = {}  # Se o arquivo não for encontrado, iniciar com dados vazios
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao carregar os dados da agenda: {e}")

def on_ctrl_s(event):
    # Salvar a agenda quando Ctrl+S for pressionado
    save_agenda_data()

def auto_save():
    save_agenda_data()  # Salva os dados
    root.after(1000, auto_save)  # Agendar para salvar a cada 1 segundos (1000 ms)

def open_calendar():
    global calendar_open
    if calendar_open:
        return  # Se o calendário já foi aberto, não faz nada

    # Cria uma nova janela para o calendário
    top_window = tk.Toplevel(root)
    top_window.title("Calendário")
    top_window.geometry("300x350")

    # Adiciona uma label para mostrar a data selecionada
    global date_label
    date_label = tk.Label(top_window, text="Selecione uma data", font=("Arial", 12))
    date_label.pack(pady=10)

    # Calendário interativo
    global calendar
    calendar = Calendar(top_window, selectmode='day', year=datetime.today().year, month=datetime.today().month, day=datetime.today().day, locale='pt_BR')

    calendar.pack(padx=20, pady=20)

    # Detecta o clique no calendário e atualiza a data selecionada
    calendar.bind("<<CalendarSelected>>", on_calendar_click)

    # Botão de confirmar
    confirm_button = tk.Button(
        top_window, 
        text="Confirmar", 
        command=lambda: confirm_date(top_window), 
        font=("Arial Black", 12),  # Fonte Arial Black, tamanho 12
        bg="#6d6e70",  # Cor de fundo (verde)
        fg="white"  # Cor do texto (branco)
    )
    confirm_button.pack(pady=10)

    calendar_open = True  # Marca que o calendário foi aberto

    # Ação para fechar a janela e marcar o calendário como fechado
    def on_close():
        global calendar_open
        calendar_open = False
        top_window.destroy()

    top_window.protocol("WM_DELETE_WINDOW", on_close)  # Quando a janela for fechada, atualiza a variável

def generate_agenda_for_date(date):
    global agenda_frame

    # Limpar a aba anterior, se existir
    for widget in agenda_frame.winfo_children():
        widget.destroy()

    # Cabeçalho dinâmico
    day_number = date.day
    weekday = dias_da_semana[date.weekday()].capitalize()   # Usando a lista de dias da semana
    month = date.strftime("%b").upper()  # Mês abreviado em português

    # Obter o ano atual
    year = datetime.now().year

    # Exibir o ano no canto superior direito
    year_label = tk.Label(root, text=str(year), bg="#484444", fg="white", font=("Arial Black", 20, "bold"))
    year_label.place(x=644, y=10)  # Ajuste as coordenadas x e y conforme necessário

     # Cabeçalho dinâmico
    tk.Label(agenda_frame, text=str(day_number), bg="#484444", fg="white", font=("Arial Black", 30, "bold")).place(x=150, y=10, width=80, height=60)

    weekday_label = tk.Label(agenda_frame, text=weekday, bg="#484444", fg="white", font=("Arial Black", 15))
    weekday_label.place(x=240, y=20, width=260, height=40)

    # master, label_text, x_label, y_label, width_label, height_label, x_input, y_input, width_input, height_input, num_lines
    create_labeled_input_area(agenda_frame, "ORÇAMENTOS ENVIADOS:", 25, 80, 271, 20, 25, 100, 271, 140, 7, 28)
    create_labeled_input_area(agenda_frame, "PEDIDO:", 304, 80, 276, 20, 304, 100, 276, 140, 7, 28)
    create_labeled_input_area(agenda_frame, "ARQUIVOS PRODUZIDOS:", 25, 247, 271, 20, 25, 267, 271, 140, 7, 28)
    create_labeled_input_area(agenda_frame, "EM CONTATO:", 304, 247, 276, 20, 304, 267, 276, 315, 16, 28)
    create_labeled_input_area(agenda_frame, "ATEND. BALCÃO:", 25, 415, 132, 25, 25, 435, 132, 60, 3, 12)
    create_labeled_input_area(agenda_frame, "VISITAS:", 25, 502, 132, 20, 25, 522, 132, 60, 3, 12)
    create_labeled_input_area(agenda_frame, "PROSPECÇÃO:", 165, 415, 130, 20, 165, 435, 130, 147, 7, 12)
    create_labeled_input_area(agenda_frame, "PENDÊNCIAS:", 25, 590, 555, 20, 25, 610, 555, 140, 7, 60)
    
    # Rotacionar a label do mês
    create_rotated_label(agenda_frame, month, 530, 10, 90, 90)

    # Carregar os dados salvos
    load_agenda_data()

def on_calendar_click(event):
    # Detecta a data selecionada e atualiza o campo de data
    selected_date = calendar.get_date()  # Exemplo: '24/01/2025'
    date_label.config(text=f"Data Selecionada: {selected_date}")

def confirm_date(top_window):
    global calendar_open
    # Pega a data selecionada
    selected_date = calendar.get_date()
    
    # Ajustar o formato para 'dd/mm/yyyy'
    selected_date_obj = datetime.strptime(selected_date, "%d/%m/%Y")

    # Gera a agenda para a data selecionada
    generate_agenda_for_date(selected_date_obj)

    # Carregar os dados para essa data específica
    load_agenda_data(selected_date_obj)

    # Fecha a janela do calendário
    top_window.destroy()

    # Marca calendar_open como False para permitir abrir novamente
    calendar_open = False

calendar_open = False  # Variável para rastrear se o calendário foi aberto

def export_agenda_to_pdf():
    try:
        # Carregar a imagem da agenda
        agenda_template = cv2.imread('agenda_template.png', cv2.IMREAD_GRAYSCALE)
        agenda_height, agenda_width = agenda_template.shape
        
        # Tirar um screenshot da tela inteira
        screenshot = pyautogui.screenshot()
        screenshot_np = np.array(screenshot)
        screenshot_gray = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2GRAY)

        # Aplicar a correspondência de template (template matching)
        result = cv2.matchTemplate(screenshot_gray, agenda_template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

        # Se a correspondência for forte o suficiente, encontrar a posição da agenda
        if max_val >= 0.6:
            agenda_region_tuple = (max_loc[0], max_loc[1], agenda_width, agenda_height)
        else:
            messagebox.showerror("Erro", "Não foi possível localizar a agenda na tela. Verifique se ela está visível.")
            return

        # Capturar a região da agenda
        screenshot = pyautogui.screenshot(region=agenda_region_tuple)

        # Salvar a captura como uma imagem temporária
        image_path = "agenda_screenshot.png"
        screenshot.save(image_path)

        # Pedir ao usuário para escolher o nome e diretório do arquivo
        file_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF Files", "*.pdf")],
            title="Escolha o nome e o diretório para salvar o PDF"
        )

        if not file_path:
            return

        # Criar o arquivo PDF usando o ReportLab
        pdf_canvas = canvas.Canvas(file_path, pagesize=letter)
        pdf_canvas.drawImage(image_path, 0, 0, width=620, height=800)  # Ajuste as dimensões conforme necessário
        pdf_canvas.save()

        messagebox.showinfo("Sucesso", f"Agenda exportada para {file_path} com sucesso!")

    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao exportar a agenda: {e}")

# Função para carregar e redimensionar a imagem
def carregar_imagem():
    try:
        # Abre a imagem original
        original_image = Image.open("logo.png")
        # Redimensiona a imagem
        nova_largura, nova_altura = 110, 60
        resized_image = original_image.resize((nova_largura, nova_altura), Image.LANCZOS)
        # Converte a imagem para o formato do Tkinter
        logo_image = ImageTk.PhotoImage(resized_image)
        return logo_image
    except Exception as e:
        print(f"Erro ao carregar a imagem: {e}")
        return None

def main():
    global root, agenda_frame
    root = tk.Tk()
    root.title("Agenda")
    root.geometry("800x800")
    root.configure(bg="#484444")
    root.focus()  # Garantir que o foco está no root

    # Impedir que a janela seja redimensionada
    root.resizable(False, False)

    # Criar um frame para a agenda
    agenda_frame = tk.Frame(root, bg="#484444")
    agenda_frame.place(x=0, y=0, width=600, height=800)
    
    # Carregar e exibir a imagem
    logo_image = carregar_imagem()
    if logo_image:
        logo_label = tk.Label(root, image=logo_image, bd=0, highlightthickness=0)  # Remover bordas
        logo_label.place(x=10, y=10)  # Altere x e y conforme necessário

    # Obter data atual
    today = datetime.today()
    day_number = today.day
    weekday = dias_da_semana[today.weekday()].capitalize()  # Usando a lista de dias da semana
    month = today.strftime("%b").upper()  # Mês abreviado em português

    # Obter o ano atual
    year = datetime.now().year

    # Exibir o ano no canto superior direito
    year_label = tk.Label(root, text=str(year), bg="#484444", fg="white", font=("Arial Black", 20, "bold"))
    year_label.place(x=644, y=10)  # Ajuste as coordenadas x e y conforme necessário

    # Cabeçalho dinâmico
    tk.Label(agenda_frame, text=str(day_number), bg="#484444", fg="white", font=("Arial Black", 30, "bold")).place(x=150, y=10, width=80, height=60)

    weekday_label = tk.Label(agenda_frame, text=weekday, bg="#484444", fg="white", font=("Arial Black", 15))
    weekday_label.place(x=240, y=20, width=260, height=40)

    # master, label_text, x_label, y_label, width_label, height_label, x_input, y_input, width_input, height_input, num_lines
    create_labeled_input_area(agenda_frame, "ORÇAMENTOS ENVIADOS:", 25, 80, 271, 20, 25, 100, 271, 140, 7, 28)
    create_labeled_input_area(agenda_frame, "PEDIDO:", 304, 80, 276, 20, 304, 100, 276, 140, 7, 28)
    create_labeled_input_area(agenda_frame, "ARQUIVOS PRODUZIDOS:", 25, 247, 271, 20, 25, 267, 271, 140, 7, 28)
    create_labeled_input_area(agenda_frame, "EM CONTATO:", 304, 247, 276, 20, 304, 267, 276, 315, 16, 28)
    create_labeled_input_area(agenda_frame, "ATEND. BALCÃO:", 25, 415, 132, 25, 25, 435, 132, 60, 3, 12)
    create_labeled_input_area(agenda_frame, "VISITAS:", 25, 502, 132, 20, 25, 522, 132, 60, 3, 12)
    create_labeled_input_area(agenda_frame, "PROSPECÇÃO:", 165, 415, 130, 20, 165, 435, 130, 147, 7, 12)
    create_labeled_input_area(agenda_frame, "PENDÊNCIAS:", 25, 590, 555, 20, 25, 610, 555, 140, 7, 60)
    
    # Rotacionar a label do mês
    create_rotated_label(agenda_frame, month, 530, 10, 90, 90)

    # Carregar os dados salvos ou gerar agenda com data atual  
    load_agenda_data()  # Carrega dados salvos, se existirem
    
    # Iniciar o salvamento automático
    auto_save()  # Iniciar o salvamento periódico    
    
    # Botão para abrir o calendário em outra janela
    open_calendar_button = tk.Button(
        root, 
        text="Alterar Data", 
        command=open_calendar, 
        font=("Arial Black", 12),  # Fonte Arial Black, tamanho 12
        bg="#6d6e70",  # Cor de fundo
        fg="white"  # Cor do texto (branca)
    )
    open_calendar_button.place(x=616, y=80, width=150, height=40)

    # Botão Exportar
    export_button = tk.Button(
        root, 
        text="Exportar", 
        command=export_agenda_to_pdf, 
        font=("Arial Black", 12), 
        bg="#6d6e70",  # Cor de fundo
        fg="white"
    )
    export_button.place(x=616, y=140, width=150, height=40)

    # Botão Salvar
    save_button = tk.Button(
        root, 
        text="Salvar", 
        command=save_agenda_data, 
        font=("Arial Black", 12), 
        bg="#6d6e70",  # Cor de fundo
        fg="white"
    )
    save_button.place(x=616, y=200, width=150, height=40)


    # Capturar o evento Ctrl+S para salvar
    root.bind("<Control-s>", on_ctrl_s)

    root.mainloop()

if __name__ == "__main__":
    main()