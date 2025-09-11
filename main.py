import speech_recognition as sr
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import os

# --- Dicionário de sinais (palavra -> imagem) ---
dicionario_libras = {
    "olá": "libras_imagens/oi.jpeg",
    "oi": "libras_imagens/oi.jpeg",
    "obrigado": "libras_imagens/obrigado.png",
    "casa": "libras_imagens/casa.jpg",
    "estudar": "libras_imagens/estudar.png",
    "comer": "libras_imagens/comer.png",
    "tudo bem": "libras_imagens/tudo_bem.png",
}

# --- Função para reconhecimento de fala ---
def texto_do_audio():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        messagebox.showinfo("Fale agora", "Fale algo em português...")
        audio = r.listen(source)
    try:
        texto = r.recognize_google(audio, language='pt-BR')
        print("Você disse:", texto)
        return texto
    except sr.UnknownValueError:
        messagebox.showerror("Erro", "Não entendi o áudio")
        return None
    except sr.RequestError as e:
        messagebox.showerror("Erro", f"Serviço de reconhecimento falhou: {e}")
        return None

# --- Função para mostrar sinais ---
def mostrar_sinais():
    texto = texto_do_audio()
    if not texto:
        return

    # Limpar imagens anteriores
    for widget in frame_sinais.winfo_children():
        widget.destroy()

    palavras = texto.lower().replace(',', '').replace('.', '').split()
    for palavra in palavras:
        if palavra in dicionario_libras:
            img_path = dicionario_libras[palavra]
            if os.path.exists(img_path):
                img = Image.open(img_path)
                img = img.resize((300, 300))
                img_tk = ImageTk.PhotoImage(img)

                label = tk.Label(frame_sinais, image=img_tk)
                label.image = img_tk
                label.pack(side="left", padx=5, pady=5)
            else:
                tk.Label(frame_sinais, text=f"[sem imagem: {palavra}]").pack(side="left")
        else:
            tk.Label(frame_sinais, text=f"[sem sinal: {palavra}]").pack(side="left")

# --- Função para "tocar" sinais em sequência ---

# --- Interface Tkinter ---
root = tk.Tk()
root.title("Tradutor Voz → Libras")
root.geometry("1000x600")
# Frame superior para exibir sinais
frame_sinais = tk.Frame(root, bg="white", height=200)
frame_sinais.pack(fill="both", expand=True)

# Botão para falar
btn_falar = tk.Button(root, text="🎤 Falar", font=("Arial", 14), command=mostrar_sinais)
btn_falar.pack(pady=10)

root.mainloop()
