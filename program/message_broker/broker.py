import ast
import datetime
import threading
from queue import Queue

import requests
from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)


def check_status_nodes():
    """
    Функция для проверки "живучести" подключенных нод.
    """
    for node, time_notification in computing_nodes.items():
        diff = datetime.datetime.now() - time_notification
        if not (subtasks_in_work.get(node) is None):
            step_node = subtasks_in_work.get(node)
            if diff.total_seconds() > 5:
                del computing_nodes[node]
                q_subtasks.put(ast.literal_eval(step_node))
                del subtasks_in_work[node]
        else:
            if diff.total_seconds() > 5:
                del computing_nodes[node]


def set_interval(func, sec):
    """
    Вспомогательная функция-таймер. Необходима, чтобы вызывать check_status_nodes.
    """
    def func_wrapper():
        set_interval(func, sec)
        func()

    t = threading.Timer(sec, func_wrapper)
    t.start()


@app.route('/newTask', methods=['GET'])
def newTask():
    """
    Функция, принимающая новую подзадачу.
    """
    INPUT_DATA = request.json

    # Добавляем подзадачу в очередь и отправляем уведомление выч. цзлам
    q_subtasks.put(INPUT_DATA)
    for node in computing_nodes.keys():
        if subtasks_in_work.get(node) is None:
            submit_task(node)
    return jsonify({'status': 'задача принята!'})


@socketio.on('connect')
def connect():
    """
    После установки соединения с новым выч. узлом добавляем его в список узлов.
    """
    new_node = request.sid
    if not (new_node in computing_nodes.keys()):
        computing_nodes[new_node] = datetime.datetime.now()
    print(f'Клиент {new_node} подключился к серверу')



@socketio.on('submit_task')
def submit_task(id_node=None):
    """
    Функция для назначения подзадач.
    """
    if not q_subtasks.empty():
        # Назначаем подзадачу узлу
        node = request.sid if id_node is None else id_node
        if not (node in computing_nodes.keys()):
            connect()
        data_for_subtask = q_subtasks.get()
        step = data_for_subtask['arguments'].split('|')[-1]
        print(f'Узел {node} получил задачу {step}')
        subtasks_in_work[node] = str(data_for_subtask)
        computing_nodes[node] = datetime.datetime.now()
        data_send = {
            'sender_address': data_for_subtask['sender_address'],
            'filename': data_for_subtask['filename'],
            'content': data_for_subtask['content'],
            'arguments': data_for_subtask['arguments']
        }
        emit('my_message', data_send, namespace='', room=node)


@socketio.on('subtask_completed')
def subtask_completed(data):
    """
    После выполнения подзадачи проверяем на наличие доступных задач и если такие имеются,
    то назначаем освободившемуся узлу.
    """
    # Получаем данне
    node = request.sid
    requests.get(f'{data["recipient_address"]}/get_solution_subtask', json=data['output'])

    # Обновить данные
    computing_nodes[node] = datetime.datetime.now()
    completed_subtasks[subtasks_in_work[node]] = data
    del subtasks_in_work[node]

    # Отправляем новую подзадачу
    submit_task()


@socketio.on('getting_status')
def getting_status():
    """
    Функция обновляющая время последнего соединения выч. узла с брокером.
    Необходима для определения "живучести" ноды.
    """
    node = request.sid
    computing_nodes[node] = datetime.datetime.now()


@socketio.on('disconnect')
def disconnect():
    """
    При разрыве соединения подзадача возвращается в очередь,
    а отвалившаяся нода удаляется из списка доступных.
    """
    node = request.sid
    if not (subtasks_in_work.get(node) is None):
        step_node = subtasks_in_work[node]
        if not (step_node in completed_subtasks.keys()):
            q_subtasks.put(ast.literal_eval(step_node))
        del subtasks_in_work[node]
    computing_nodes.pop(node)
    print(f'Клиент {node} отключился от сервера')


"""
Входные данные
"""
input_data = str()

"""
Данные для выполнения работы
"""
computing_nodes = {}  # Словарь нод: {node: время_последнего_уведомления}
q_subtasks = Queue()  # Подзадачи: '0-0;0-2', ...
subtasks_in_work = {}  # Подзадачи в работе: {node: '0-0;0-2'}
completed_subtasks = {}  # Выполненные подзадачи: {'0-0;0-2': [[0,0]]}


threading.Thread(target=set_interval, args=(check_status_nodes, 5)).start()
socketio.run(app, host='localhost', port=5001, allow_unsafe_werkzeug=True)
