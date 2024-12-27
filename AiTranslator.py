import sys
import os
import customtkinter as ctk
from googletrans import Translator as GoogleTrans
from deep_translator import GoogleTranslator as DeepTranslator
from difflib import SequenceMatcher
from tkinter import messagebox, Menu
import keyboard
import threading
from PIL import Image
from customtkinter import CTkImage


def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)
class EnhancedTranslator:
    def __init__(self, root):
        self.root = root
        self.root.title("AI Translator")
        self.root.geometry("700x400")

        self.google_translator = GoogleTrans()
        self.deep_translator = DeepTranslator

        self.languages = {
            "Английский": "en", "Русский": "ru", "Украинский": "ukma", "Испанский": "es", "Французский": "fr", "Немецкий": "de",
            "Китайский (упрощенный)": "zh-cn", "Китайский (традиционный)": "zh-tw", "Японский": "ja",
            "Корейский": "ko", "Итальянский": "it", "Португальский": "pt", "Арабский": "ar", "Голландский": "nl",
            "Греческий": "el", "Иврит": "he", "Индонезийский": "id", "Польский": "pl", "Румынский": "ro",
            "Турецкий": "tr", "Чешский": "cs", "Вьетнамский": "vi", "Хинди": "hi", "Шведский": "sv"
        }

        self.src_lang_var = ctk.StringVar(value="Английский")
        self.dest_lang_var = ctk.StringVar(value="Русский")

        self.create_widgets()
        self.src_lang_var.trace_add("write", self.translate_text)
        self.dest_lang_var.trace_add("write", self.translate_text)

        # Установите глобальные горячие клавиши для копирования, вставки и вырезания
        keyboard.add_hotkey('ctrl+c', self.global_copy)
        keyboard.add_hotkey('ctrl+v', self.global_paste)
        keyboard.add_hotkey('ctrl+x', self.global_cut)


    def create_widgets(self):
        ctk.CTkLabel(master=self.root, text="Исходный язык").grid(row=0, column=0, padx=10, pady=10)
        ctk.CTkLabel(master=self.root, text="Целевой язык").grid(row=0, column=1, padx=10, pady=10)

        src_lang_menu = ctk.CTkOptionMenu(master=self.root, variable=self.src_lang_var,
                                          values=list(self.languages.keys()))
        src_lang_menu.grid(row=1, column=0, padx=10, pady=10, sticky="ew")

        dest_lang_menu = ctk.CTkOptionMenu(master=self.root, variable=self.dest_lang_var,
                                           values=list(self.languages.keys()))
        dest_lang_menu.grid(row=1, column=1, padx=10, pady=10, sticky="ew")

        self.input_text = ctk.CTkTextbox(master=self.root, width=300, height=300)
        self.input_text.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")
        self.input_text.bind("<KeyRelease>", self.translate_text)
        self.add_context_menu(self.input_text)

        # Добавление иконки и кнопки очистки для левого текстового поля
        clear_icon_path = resource_path("clear_icon.png")
        self.clear_icon = CTkImage(Image.open(clear_icon_path), size=(20, 20))
        clear_button = ctk.CTkButton(
            master=self.input_text,
            image=self.clear_icon,
            width=20,
            height=20,
            command=self.clear_input_text,
            fg_color="transparent",
            text=""
        )
        clear_button.place(relx=1.0, rely=0.0, anchor='ne')
        self.add_tooltip(clear_button, "Очистить текст")

        self.output_text = ctk.CTkTextbox(master=self.root, width=300, height=300)
        self.output_text.grid(row=2, column=1, padx=10, pady=10, sticky="nsew")
        self.add_context_menu(self.output_text)

        # Добавление иконки и кнопки копирования для правого текстового поля
        copy_icon_path = resource_path("copy_icon.png")
        self.copy_icon = CTkImage(Image.open(copy_icon_path), size=(20, 20))
        copy_button = ctk.CTkButton(
            master=self.output_text,
            image=self.copy_icon,
            width=20,
            height=20,
            command=self.copy_output_text,
            fg_color="transparent",
            text=""
        )
        copy_button.place(relx=1.0, rely=0.0, anchor='ne')
        self.add_tooltip(copy_button, "Копировать текст")

        swap_button = ctk.CTkButton(master=self.root, text="<Поменять языки местами>", command=self.swap_languages)
        swap_button.grid(row=3, column=0, columnspan=2, padx=10, pady=10, sticky="ew")

        self.root.grid_rowconfigure(2, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=1)

    def clear_input_text(self):
        self.input_text.delete("1.0", "end")

    def copy_output_text(self):
        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(self.output_text.get("1.0", "end-1c"))
        except:
            messagebox.showerror("Ошибка", "Не удалось скопировать текст в буфер обмена")

    def add_tooltip(self, widget, text):
        tooltip = ctk.CTkLabel(
            master=widget,
            text=text,
            bg_color="#f0f0f0",
            text_color="#000000",
            corner_radius=5
        )

        def show_tooltip(event):
            tooltip.place(relx=1.0, rely=0.0, anchor='nw')

        def hide_tooltip(event):
            tooltip.place_forget()

        widget.bind("<Enter>", show_tooltip)
        widget.bind("<Leave>", hide_tooltip)
        hide_tooltip(None)

    def add_context_menu(self, widget):
        context_menu = Menu(self.root, tearoff=0)
        context_menu.add_command(label="Вставить", command=lambda: self.paste_text(widget))
        context_menu.add_command(label="Копировать", command=lambda: self.copy_text(widget))
        context_menu.add_command(label="Вырезать", command=lambda: self.cut_text(widget))

        widget.bind("<Button-3>", lambda event: self.show_context_menu(event, context_menu))

    def show_context_menu(self, event, context_menu):
        context_menu.tk_popup(event.x_root, event.y_root)

    def paste_text(self, widget):
        try:
            widget.insert("insert", self.root.clipboard_get())
        except:
            messagebox.showerror("Ошибка", "Не удалось вставить текст из буфера обмена")

    def copy_text(self, widget):
        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(widget.selection_get())
        except:
            messagebox.showerror("Ошибка", "Не удалось скопировать текст в буфер обмена")

    def cut_text(self, widget):
        try:
            self.copy_text(widget)
            widget.delete("sel.first", "sel.last")
        except:
            messagebox.showerror("Ошибка", "Не удалось вырезать текст")

    def global_copy(self):
        widget = self.root.focus_get()
        if isinstance(widget, ctk.CTkTextbox):
            self.copy_text(widget)

    def global_paste(self):
        widget = self.root.focus_get()
        if isinstance(widget, ctk.CTkTextbox):
            self.paste_text(widget)

    def global_cut(self):
        widget = self.root.focus_get()
        if isinstance(widget, ctk.CTkTextbox):
            self.cut_text(widget)

    def translate_text(self, event=None, *args):
        original_text = self.input_text.get("1.0", "end-1c")
        if original_text:
            threading.Thread(target=self.perform_translation, args=(original_text,)).start()

    def perform_translation(self, original_text):
        src_lang = self.src_lang_var.get()
        dest_lang = self.dest_lang_var.get()
        try:
            google_translation = self.google_translator.translate(original_text, src=self.languages[src_lang],
                                                                  dest=self.languages[dest_lang]).text
        except Exception as e:
            google_translation = None
            messagebox.showerror("Ошибка перевода Google", f"Не удалось выполнить перевод: {e}")

        try:
            deep_translation = self.deep_translator(source=self.languages[src_lang],
                                                    target=self.languages[dest_lang]).translate(original_text)
        except Exception as e:
            deep_translation = None
            messagebox.showerror("Ошибка перевода Deep", f"Не удалось выполнить перевод: {e}")

        best_translation = self.choose_best_translation(original_text, google_translation, deep_translation, src_lang,
                                                        dest_lang)
        self.update_output_text(best_translation)

    def update_output_text(self, text):
        self.output_text.delete("1.0", "end")
        self.output_text.insert("1.0", text)

    def choose_best_translation(self, original_text, google_translation, deep_translation, src_lang, dest_lang):
        google_similarity = SequenceMatcher(None, original_text, google_translation).ratio()
        deep_similarity = SequenceMatcher(None, original_text, deep_translation).ratio()

        # Проверка round-trip перевода (перевод туда и обратно)
        google_round_trip = self.google_translator.translate(google_translation, src=self.languages[dest_lang], dest=self.languages[src_lang]).text
        deep_round_trip = self.deep_translator(source=self.languages[dest_lang], target=self.languages[src_lang]).translate(deep_translation)

        google_round_trip_similarity = SequenceMatcher(None, original_text, google_round_trip).ratio()
        deep_round_trip_similarity = SequenceMatcher(None, original_text, deep_round_trip).ratio()

        # Дополнительные проверки для определения лучшего перевода
        if google_similarity + google_round_trip_similarity > deep_similarity + deep_round_trip_similarity:
            return google_translation
        elif deep_similarity + deep_round_trip_similarity > google_similarity + google_round_trip_similarity:
            return deep_translation
        else:
            # В случае равенства, можно использовать любой перевод или провести дополнительный анализ
            return google_translation if len(google_translation) <= len(deep_translation) else deep_translation

    def swap_languages(self):
        src_lang = self.src_lang_var.get()
        dest_lang = self.dest_lang_var.get()
        self.src_lang_var.set(dest_lang)
        self.dest_lang_var.set(src_lang)
        self.translate_text()

if __name__ == "__main__":
    root = ctk.CTk()
    app = EnhancedTranslator(root)
    root.mainloop()
