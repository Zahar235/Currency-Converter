import tkinter as tk
from tkinter import ttk, messagebox
import requests
import json
from tkcalendar import DateEntry
import datetime


class CurrencyConverterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Currency Converter")
        self.api_key = 'YOUR_API_KEY'  # ЗАМЕНИТЕ НА СВОЙ КЛЮЧ
        self.history_file = "history.json"
        self.history = self.load_history()

        # --- Элементы интерфейса ---
        # Выбор валют
        ttk.Label(root, text="Из:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.from_currency = ttk.Combobox(root, values=self.get_currency_list(), width=5)
        self.from_currency.current(0)  # По умолчанию USD
        self.from_currency.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(root, text="В:").grid(row=0, column=2, padx=5, pady=5, sticky="e")
        self.to_currency = ttk.Combobox(root, values=self.get_currency_list(), width=5)
        self.to_currency.current(1)  # По умолчанию EUR
        self.to_currency.grid(row=0, column=3, padx=5, pady=5)

        # Поле ввода суммы
        ttk.Label(root, text="Сумма:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.amount_entry = ttk.Entry(root)
        self.amount_entry.grid(row=1, column=1, columnspan=3, padx=5, pady=5, sticky="we")

        # Кнопка конвертации и результат
        ttk.Button(root, text="Конвертировать", command=self.convert).grid(row=2, column=0, columnspan=4, pady=10)

        self.result_label = ttk.Label(root, text="Результат: ")
        self.result_label.grid(row=3, column=0, columnspan=4, pady=(0, 10))

        # Таблица истории
        ttk.Label(root, text="История конвертаций:").grid(row=4, column=0, columnspan=4)

        self.tree = ttk.Treeview(root, columns=("date", "from_cur", "to_cur", "amount", "rate", "result"),
                                 show='headings')

        self.tree.heading("date", text="Дата")
        self.tree.heading("from_cur", text="Из")
        self.tree.heading("to_cur", text="В")
        self.tree.heading("amount", text="Сумма")
        self.tree.heading("rate", text="Курс")
        self.tree.heading("result", text="Результат")

        self.tree.grid(row=5, column=0, columnspan=4, padx=5, pady=5)

        # Загрузка истории в таблицу
        self.update_history_table()

    def get_currency_list(self):
        """Возвращает список валют из API или стандартный список при ошибке."""
        try:
            response = requests.get(f"https://v6.exchangerate-api.com/v6/{self.api_key}/codes")
            response.raise_for_status()
            data = response.json()
            # Формируем список вида ['USD - Доллар США', ...]
            return [f"{code} - {name}" for code, name in data["supported_codes"]]
        except Exception as e:
            print(f"Ошибка при получении списка валют: {e}")
            return ["USD - Доллар США", "EUR - Евро", "RUB - Российский рубль"]

    def get_rate(self, from_cur_code, to_cur_code):
        """Получает курс обмена из API."""
        try:
            # Берем только код валюты (до первого пробела)
            from_code = from_cur_code.split()[0]
            to_code = to_cur_code.split()[0]

            response = requests.get(f"https://v6.exchangerate-api.com/v6/{self.api_key}/pair/{from_code}/{to_code}")
            response.raise_for_status()
            data = response.json()
            return data["conversion_rate"]

        except requests.exceptions.RequestException as e:
            messagebox.showerror("Ошибка сети", f"Не удалось подключиться к серверу курсов валют.\n{e}")
            return None

    def convert(self):
        """Обрабатывает нажатие кнопки конвертации."""
        try:
            amount = float(self.amount_entry.get())
            if amount <= 0:
                raise ValueError("Сумма должна быть положительной.")

            from_cur = self.from_currency.get()
            to_cur = self.to_currency.get()

            rate = self.get_rate(from_cur, to_cur)
            if rate is None:
                return  # Ошибка уже показана в get_rate

            result = round(amount * rate, 2)

            # Сохранение в историю
            entry = {
                "date": str(datetime.datetime.now()),
                "from": from_cur,
                "to": to_cur,
                "amount": amount,
                "rate": rate,
                "result": result
            }

            self.history.insert(0, entry)  # Добавляем в начало списка
            self.save_history()

            # Обновление интерфейса
            self.result_label.config(text=f"Результат: {result} {to_cur.split()[0]}")
            self.update_history_table()

        except ValueError as e:
            messagebox.showerror("Ошибка ввода", str(e))

    def load_history(self):
        try:
            with open(self.history_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def save_history(self):
        with open(self.history_file, 'w', encoding='utf-8') as f:
            json.dump(self.history[:20], f, ensure_ascii=False, indent=4)  # Сохраняем 20 последних записей

    def update_history_table(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        for item in self.history:
            self.tree.insert("", tk.END, values=(
            item["date"], item["from"], item["to"], item["amount"], item["rate"], item["result"]))


if __name__ == "__main__":
    root = tk.Tk()
    app = CurrencyConverterApp(root)
    root.mainloop()