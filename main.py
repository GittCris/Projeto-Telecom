import speech_recognition as sr
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import os
import threading
from deepmultilingualpunctuation import PunctuationModel

model = PunctuationModel()


# --- Dicionário de sinais (palavra -> imagem) ---
dicionario_libras = {
    "olá": "libras_imagens/oi.jpeg",
    "oi": "libras_imagens/oi.jpeg",
    "casa": "libras_imagens/casa.jpg",
}

# --- Variáveis globais ---
captando = False
thread_rec = None
texto_final = ""

# --- Função de reconhecimento de fala em tempo real ---
def captura_continua():
    global captando, texto_final
    try:
        mic = sr.Microphone()
    except OSError:
        print("⚠️ Nenhum microfone detectado (WSL não tem suporte a áudio).")
        mic = None

    r = sr.Recognizer()

    if mic is None:
        # modo texto
        pass
        
    
    with mic as source:
        r.adjust_for_ambient_noise(source)
        while captando:
            try:
                audio = r.listen(source)
                if not captando:
                    break  # verifica imediatamente se deve parar
                texto = r.recognize_google(audio, language='pt-BR')
                texto_completo = model.restore_punctuation(texto)
                print(f"Você disse: {texto_completo}")
                mostrar_sinais(texto,texto_completo)
            except sr.WaitTimeoutError:
                continue
            except sr.UnknownValueError:
                continue
            except sr.RequestError as e:
                messagebox.showerror("Erro", f"Serviço de reconhecimento falhou: {e}")
                break

# --- Função para mostrar sinais ---
def mostrar_sinais(texto, texto_completo):
    # Limpar imagens anteriores
    for widget in frame_inner.winfo_children():
        widget.destroy()

    palavras = texto.lower().split()
    for palavra in palavras:
        if palavra in dicionario_libras:
            img_path = dicionario_libras[palavra]
            if os.path.exists(img_path):
                img = Image.open(img_path)
                img = img.resize((300, 300))
                img_tk = ImageTk.PhotoImage(img)

                label = tk.Label(frame_inner, image=img_tk)
                label.image = img_tk
                label.pack(side="left", padx=5, pady=5)
            else:
                tk.Label(frame_inner, text=f"[sem imagem: {palavra}]").pack(side="left")
        else:
            tk.Label(frame_inner, text=f"[sem sinal: {palavra}]").pack(side="left")

    # Atualiza o texto reconhecido
    lbl_texto.config(text=texto_completo)

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
root.geometry("1000x600")

# Canvas e scrollbar para permitir scroll horizontal
canvas = tk.Canvas(root, bg="white", height=320)
frame_inner = tk.Frame(canvas, bg="white")
canvas.create_window((0, 0), window=frame_inner, anchor='nw')

scrollbar = tk.Scrollbar(root, orient="horizontal", command=canvas.xview)
canvas.configure(xscrollcommand=scrollbar.set)

# Empacotamento: canvas primeiro, scrollbar depois
canvas.pack(fill="both", expand=True)
scrollbar.pack(side="top", fill="x")  # fica logo abaixo do canvas

# Ajusta o tamanho do canvas quando frame muda
def resize_canvas(event):
    canvas.configure(scrollregion=canvas.bbox("all"))
frame_inner.bind("<Configure>", resize_canvas)



# Label para mostrar o texto reconhecido
lbl_texto = tk.Label(root, text="", font=("Arial", 16), wraplength=1000)
lbl_texto.pack(pady=10)

# Botão para falar/parar
btn_falar = tk.Button(root, text="🎤 Falar", font=("Arial", 14), command=toggle_captura)
btn_falar.pack(pady=10)

root.mainloop()
