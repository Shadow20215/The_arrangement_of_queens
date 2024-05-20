import threading
from time import sleep
from dotenv import load_dotenv
import os
import socketio
import subprocess

sio = socketio.Client()


def sending_status():
    """
    Функция, оповещаящая, что вычислительная нода еще подключена и жива.
    """
    while True:
        sio.emit('getting_status')
        sleep(5)


@sio.event
def connect():
    """
    Для установки соединения
    """
    print('Установлено новое соединение')

@sio.event
def my_message(data):
    """
    Функция выполняющая вычисление подзадачи.
    Приходит:
    1) Имя файла
    2) Содержимое файла (массив байтов)
    3) Аргументы необходимые для запуска файла (в данном случае:
                                                                1) Размер поля;
                                                                2) Позиции предрасположенных ферзей;
                                                                3) Диапазон ячеек, которые необходимо пройти выч. ноде
                                                )
    Возвращается словарь вида:
    'recipient_address': data['sender_address'], 'output': str_data_list
    Где - recipient_address адрес, куда нужно вернуть результат, после того как он вернется обратно в распределитель.
    output - выходные данные из файла kernel.py после того как он отработал.
    """
    filename = data['filename']
    file_content = data['content']
    for ind, f in enumerate(filename):
        with open(f, 'wb') as file:
            file.write(bytes(file_content[ind]))
    arguments = data['arguments'].split('|')
    print('Файл успешно передан!')
    args = ['python', filename[0]]
    """
    Для запуска любых файлов:
    import os
    give_permission = f'chmod +x {filename[0]}'
    os.system(give_permission)
    args = [filename[0]]
    """
    for arg in arguments:
        args.append(arg)
    args = tuple(args)
    popen = subprocess.Popen(args, stdout=subprocess.PIPE)
    popen.wait()
    str_output = popen.stdout.read().decode()
    str_data_list = str_output.splitlines()
    sio.emit('subtask_completed', {'recipient_address': data['sender_address'], 'output': str_data_list})


@sio.event
def disconnect():
    """
    Для установки отсоединения
    """
    print('Отключились от сервера')


load_dotenv()
BROKER = os.getenv('BROKER')
sio.connect(BROKER)
availability = threading.Thread(target=sending_status)
availability.start()
sio.emit('submit_task')
sio.wait()
