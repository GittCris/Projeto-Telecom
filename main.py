import speech_recognition as sr
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk, ImageSequence
import os
import threading
from deepmultilingualpunctuation import PunctuationModel
import unicodedata
import json
import warnings

warnings.filterwarnings("ignore") # Tirando warnings chatos que não interfere na execução

model = PunctuationModel() # Modelo para pontuação automática

# --- Dicionário de sinais (palavra -> GIF) ---
with open("dicionario.json", "r", encoding="utf-8") as f:
    dicionario_libras = json.load(f)

# --- Variáveis globais ---
captando = False
thread_rec = None
texto_final = ""
gif_labels = []  # Para controlar animações

# --- Função para rolar o canvas para o fim ---
def scroll_lento():
    canvas.update_idletasks()  # garante que bbox está atualizado
    scroll_region = canvas.bbox("all")
    if not scroll_region:
        return
    
    canvas.configure(scrollregion=scroll_region)
    inicio = canvas.xview()[0]  # posição atual (0.0 a 1.0)
    fim = 1.0  # queremos ir até o final
    passo = 0.002  # fração do scroll por frame
    intervalo = 20  # ms entre frames
    atraso_inicial = 800  # ms antes de iniciar o scroll


    def mover(pos):
        # se o usuário estiver mexendo no scroll, interrompe o auto-scroll
        if abs(canvas.xview()[0] - pos) > 0.01:
            return
        if pos < fim:
            pos += passo
            if pos > fim:
                pos = fim
            canvas.xview_moveto(pos)
            canvas.after(intervalo, lambda: mover(pos))
    
    canvas.after(atraso_inicial, lambda: mover(inicio))





# --- Função de reconhecimento de fala em tempo real ---
def captura_continua():
    global captando, texto_final
    r = sr.Recognizer()
    mic = sr.Microphone()
    with mic as source:
        r.adjust_for_ambient_noise(source)
        while captando:
            try:
                audio = r.listen(source)
                if not captando:
                    break
                texto = r.recognize_google(audio, language='pt-BR')
                texto_completo = model.restore_punctuation(texto)
                mostrar_sinais(texto, texto_completo)
            except sr.WaitTimeoutError:
                continue
            except sr.UnknownValueError:
                continue
            except sr.RequestError as e:
                messagebox.showerror("Erro", f"Serviço de reconhecimento falhou: {e}")
                break

def remover_acentos(texto):
    # Normaliza o texto para decompor acentos
    texto_normalizado = unicodedata.normalize('NFD', texto)
    # Mantém apenas caracteres que não são acentos
    texto_sem_acentos = ''.join(
        c for c in texto_normalizado if unicodedata.category(c) != 'Mn'
    )
    return texto_sem_acentos


# --- Função para animar GIF ---
def animar_gif(label, frames, index=0, delay=250):
    frame = frames[index]
    label.config(image=frame)
    label.image = frame
    index = (index + 1) % len(frames)
    label.after(delay, lambda: animar_gif(label, frames, index, delay))

# --- Função para mostrar sinais ---
def mostrar_sinais(texto, texto_completo):
    global gif_labels
    # Limpar imagens/gifs anteriores
    for widget in frame_inner.winfo_children():
        widget.destroy()
    gif_labels.clear()

    # Remove acentos do texto
    txt_proc = remover_acentos(texto.lower())
    palavras_exibidas = []

    # Processa o texto mantendo a ordem
    while txt_proc.strip():
        achou = False
        for chave in sorted(dicionario_libras, key=lambda x: -len(x)):
            chave_sem_acentos = chave.lower()
            if txt_proc.startswith(chave_sem_acentos):
                palavras_exibidas.append(chave)  # mantém a ordem
                txt_proc = txt_proc[len(chave_sem_acentos):].lstrip()
                achou = True
                break
        if not achou:
            # pega a primeira palavra não reconhecida
            primeira_palavra = txt_proc.split()[0]
            palavras_exibidas.append(primeira_palavra)
            txt_proc = txt_proc[len(primeira_palavra):].lstrip()

    # Exibe GIFs ou mensagens para cada palavra detectada
    for palavra in palavras_exibidas:
        if palavra in dicionario_libras:
            img_path = dicionario_libras[palavra]
            if os.path.exists(img_path):
                try:
                    pil_img = Image.open(img_path)
                    root.update_idletasks()  # garante medidas atualizadas
                    altura_janela = root.winfo_height() - 150
                    largura_nova = int((pil_img.width / pil_img.height) * altura_janela)
                    altura_nova = altura_janela

                    frames = [ImageTk.PhotoImage(frame.copy().resize((largura_nova, altura_nova))) 
                            for frame in ImageSequence.Iterator(pil_img)]
                    label = tk.Label(frame_inner)
                    label.pack(side="left", padx=5, pady=5)
                    gif_labels.append(label)
                    animar_gif(label, frames, delay=250)
                except Exception as e:
                    tk.Label(frame_inner, text=f"[erro GIF: {palavra}]").pack(side="left")
            else:
                tk.Label(frame_inner, text=f"[arquivo não encontrado: {palavra}]").pack(side="left")
        else:
            tk.Label(frame_inner, 
         text=f"[{palavra}]", 
         font=("Arial", 20, "bold")).pack(side="left")


    # Atualiza o texto reconhecido
    lbl_texto.config(text=texto_completo)

    # Faz o scroll horizontal ir automaticamente para o fim
    scroll_lento()


# --- Função do botão Falar ---
def toggle_captura():
    global captando, thread_rec
    if not captando:
        captando = True
        btn_falar.config(text="⏹️ Parar")
        thread_rec = threading.Thread(target=captura_continua, daemon=True)
        thread_rec.start()
    else:
        captando = False
        btn_falar.config(text="🎤 Falar")

# --- Interface Tkinter ---
root = tk.Tk()
root.title("Tradutor Voz → Libras")
root.geometry("800x500")

# Canvas e scrollbar para permitir scroll horizontal
canvas = tk.Canvas(root, bg="white", height=320)
frame_inner = tk.Frame(canvas, bg="white")
canvas.create_window((0, 0), window=frame_inner, anchor='nw')

scrollbar = tk.Scrollbar(root, orient="horizontal", command=canvas.xview)
canvas.configure(xscrollcommand=scrollbar.set)

canvas.pack(fill="both", expand=True)
scrollbar.pack(side="top", fill="x")

def resize_canvas(event):
    canvas.configure(scrollregion=canvas.bbox("all"))
frame_inner.bind("<Configure>", resize_canvas)

lbl_texto = tk.Label(root, text="", font=("Arial", 16), wraplength=1000)
lbl_texto.pack(pady=10)

btn_falar = tk.Button(root, text="🎤 Falar", font=("Arial", 14), command=toggle_captura)
btn_falar.pack(pady=10)

root.mainloop()
