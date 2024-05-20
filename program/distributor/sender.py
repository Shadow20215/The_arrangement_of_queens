import math
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)


def generate_data_for_sending(sending_data, files, step):
    """
    Формирование данных для отсылки их в вычислительные ноды.
    """
    list_content_file = list()
    for f in files:
        with open(f, 'rb') as file:
            file_content = file.read()
            list_content_file.append(list(file_content))
    sending_data += f'|{step}'
    data_to_send = {
        'filename': files,
        'content': list_content_file,
        'sender_address': f'http://{HOST}:{PORT}',
        'arguments': sending_data
    }
    return data_to_send


def fewer_location(num_cells, N):
    """
    Функция, выполняющая деление задачи на подзадачи.
    """
    return math.factorial(num_cells) / (math.factorial(N) * math.factorial(num_cells - N))


def split_task(data, files, task_size):
    """
    Функция выполняющая деление и отправку задач на вычислительные ноды.
    """
    total_scope_task = task_size ** 2
    tmp_num_cells = total_scope_task
    list_permutations = []
    iter = 1
    while tmp_num_cells >= task_size:
        list_permutations.append(fewer_location(tmp_num_cells, task_size))
        tmp_num_cells -= 1

    list_subtask = []
    second_init_step = 0
    second_final_step = 0
    step = 0

    while total_scope_task > 0:
        scope_subtask = 1
        if step > 0:
            last_count_combinations = list_permutations[0]
            current_count_combinations = 0
            while current_count_combinations < last_count_combinations and iter < len(list_permutations):
                current_count_combinations += list_permutations[iter]
                iter += 1
                if iter == len(list_permutations):
                    iter += task_size ** 2 - iter
            scope_subtask = iter - step
            step = iter

        first_init_step = second_init_step
        second_init_step = (second_final_step + scope_subtask) // task_size
        first_final_step = second_final_step
        second_final_step += scope_subtask - 1
        total_scope_task -= scope_subtask
        if total_scope_task < task_size:
            second_final_step += total_scope_task
            total_scope_task -= scope_subtask
        list_subtask.append(f'{first_init_step}-{second_init_step};{first_final_step}-{second_final_step}')
        step += 1
        second_final_step += 1
        subtask_parameters = generate_data_for_sending(data, files, list_subtask[-1])
        requests.get('http://localhost:5001/newTask', json=subtask_parameters)
    return list_subtask


@app.route('/assign_task', methods=['GET'])
def assign_task():
    """
    Route для приема входных данных задачи.
    """
    output_data.clear()
    INPUT_DATA = request.json['data']
    FILES = request.json['name_files']
    SCOPE_TASK = int(INPUT_DATA.split('|')[0])
    subtasks = split_task(INPUT_DATA, FILES, SCOPE_TASK)

    while True:
        if len(subtasks) == len(output_data):
            return output_data


@app.route('/get_solution_subtask', methods=['GET'])
def get_solution_subtask():
    """
    Route для приема результатов вычисление с вычислительных нод.
    """
    output_data.append(request.json)
    return jsonify({'status': 'Решение подзадачи получено!'})


input_data = str()
output_data = list()
HOST = 'localhost'
PORT = 5000
app.run(host=HOST, port=PORT)