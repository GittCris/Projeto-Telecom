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



# Dicionário de verbos irregulares que mudam a raiz
irregulares = {
    # TER
    "tenho": "ter", "tem": "ter", "têm": "ter", "tinha": "ter", "tivemos": "ter", "tiveram": "ter", "tive": "ter", "teve": "ter",
    # SER
    "sou": "ser", "és": "ser", "é": "ser", "são": "ser", "fui": "ser", "foi": "ser", "fomos": "ser", "foram": "ser",
    # IR
    "vou": "ir", "vais": "ir", "vai": "ir", "vamos": "ir", "vão": "ir", "fui": "ir", "foi": "ir", "foram": "ir",
    # VIR
    "venho": "vir", "vem": "vir", "vêm": "vir", "viemos": "vir", "vieram": "vir",
    # ESTAR
    "estou": "estar", "está": "estar", "estão": "estar", "estivemos": "estar", "esteve": "estar",
    # FAZER
    "faço": "fazer", "faz": "fazer", "fazem": "fazer", "fiz": "fazer", "fez": "fazer", "fizeram": "fazer",
    # DIZER
    "digo": "dizer", "diz": "dizer", "disse": "dizer", "disseram": "dizer",
    # PODER
    "posso": "poder", "pode": "poder", "pudemos": "poder", "pude": "poder", "pôde": "poder", "puderam": "poder",
    # SABER
    "sei": "saber", "sabe": "saber", "soube": "saber", "souberam": "saber",
    # VER
    "vejo": "ver", "vê": "ver", "vemos": "ver", "viram": "ver",
    # CABER
    "caibo": "caber", "cabe": "caber", "cabem": "caber", "coube": "caber",
    # TRAZER
    "trago": "trazer", "traz": "trazer", "trouxemos": "trazer", "trouxe": "trazer", "trouxeram": "trazer",
    # PÔR
}

def reduzir_verbos(palavra):
    """
    Reduz verbos regulares e irregulares à forma infinitiva.
    """
    # Primeiro, checa se é um verbo irregular
    if palavra in irregulares:
        yield irregulares[palavra]
        return
    
    # Lista de sufixos para verbos regulares
    sufixos = ["arias", "aria", "ariamos", "arieis", "ariam",
               "eria", "erias", "eriamos", "erieis", "eriam",
               "iria", "irias", "iriamos", "irieis", "iriam",
               "ei", "aste", "ou", "astes", "aram",
               "i", "iste", "iu", "imos", "istes", "iram",
               "arei", "aras", "ara", "aremos", "areis", "arao",
               "erei", "eras", "era", "eremos", "ereis", "erao",
               "irei", "iras", "ira", "iremos", "ireis", "irao",
               "o", "as", "a", "amos", "ais", "am",
                "es", "e", "emos", "eis", "em", "is",
               "ram", "eram","avam","ia", "ias", "iamos", "ieis", "iam"]
    
    # Tenta reduzir palavra com sufixos regulares
    for suf in sorted(sufixos, key=len):
        if palavra.endswith(suf):
            raiz = palavra[:-len(suf)]
            for term in ["ar", "er", "ir"]:
                yield raiz + term

# Função para pegar valor do dicionário
def encontrar_valor(dicionario, palavra):
    """
    Retorna o valor do dicionário correspondente à palavra ou à raiz do verbo regular.
    Ignora palavras irrelevantes (preposições, artigos, etc.).
    """

    # Conjunto de palavras irrelevantes para ignorar (mais eficiente que lista)
    ignorar = {"a", "e", "o", "de", "do", "da", "em", "uma", "para", "com", "por", "no", "na"}

    palavra_lower = palavra.lower()
    
    # Ignora palavras irrelevantes
    if palavra_lower in ignorar or not palavra_lower.strip():
        return None

    # Verifica se a palavra está diretamente no dicionário
    if palavra_lower in dicionario:
        return dicionario[palavra_lower]
    
    # Tenta reduzir a palavra à raiz de verbos regulares
    for possivel_verbo in reduzir_verbos(palavra_lower):
        if possivel_verbo in dicionario:
            return dicionario[possivel_verbo]
    
    # Nenhuma correspondência encontrada
    return None

    

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
        img_path = encontrar_valor(dicionario_libras, palavra)
        if img_path != None:
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
            if palavra.lower() not in ["a", "e", "o", "de", "do", "da", "em", "uma", "para", "com", "por", "no", "na"]:
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
