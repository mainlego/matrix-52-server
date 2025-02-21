from flask import request, jsonify
import win32com.client
import pythoncom
import os
from datetime import datetime
import traceback

from flask import Flask
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "http://localhost:5173"}})  # Ограничили CORS только на нужный домен

if __name__ == '__main__':
    app.run(debug=True, port=5000)

@app.route('/calculate-matrix', methods=['POST'])
def calculate_matrix():
    try:
        data = request.get_json()

        print("Received data:", data)  # Отладочный вывод

        # Получаем данные из запроса
        birth_date = data.get('birthDate')
        name = data.get('name')
        user_id = data.get('user_id')

        if not birth_date:
            return jsonify({'error': 'Birth date is required'}), 400

        # Инициализируем COM для текущего потока
        pythoncom.CoInitialize()

        try:
            # Получаем абсолютный путь к файлу
            excel_path = os.path.abspath('matrix.xlsx')
            print("Excel path:", excel_path)  # Отладочный вывод

            # Проверяем существование файла
            if not os.path.exists(excel_path):
                return jsonify({'error': 'Excel file not found'}), 500

            # Инициализируем Excel
            excel = win32com.client.Dispatch("Excel.Application")
            excel.Visible = False
            excel.DisplayAlerts = False

            try:
                # Открываем книгу
                workbook = excel.Workbooks.Open(excel_path)
                sheet = workbook.Sheets("Годовая матрица")

                # Устанавливаем дату и пересчитываем
                sheet.Range("K2").Value = birth_date
                excel.Calculate()

                # Считываем данные
                layout = {
                    'top_row': [
                        str(sheet.Range(f"{col}5").Value or '').strip()
                        for col in ['F', 'G', 'H']
                    ],
                    'rows': [
                        [
                            str(sheet.Range(f"{col}{row}").Value or '').strip()
                            for col in ['D', 'E', 'F', 'G', 'H', 'I', 'J']
                        ]
                        for row in range(6, 13)
                    ]
                }

                print("Generated layout:", layout)  # Отладочный вывод
                return jsonify(layout)

            finally:
                # Закрываем все
                if 'workbook' in locals():
                    workbook.Close(False)
                if 'excel' in locals():
                    excel.Quit()

        finally:
            pythoncom.CoUninitialize()

    except Exception as e:
        print("Error occurred:", str(e))  # Отладочный вывод
        print("Traceback:", traceback.format_exc())  # Полный стек ошибки
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, port=5000)