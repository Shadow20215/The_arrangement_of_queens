import json

import requests

from fastapi import FastAPI, Body, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from starlette.responses import FileResponse, JSONResponse

in_process = False
res_answers = []
app = FastAPI()

app.mount("/static", StaticFiles(directory="app/Resources"))


@app.get("/")
async def main():
    return FileResponse("app/Main.html")


# Поиск максимальных решений
def correction_answers():
    global res_answers
    max_count_queens = 0
    array_answers = []
    for item in res_answers:
        if int(item[0]) > max_count_queens:
            max_count_queens = int(item[0])
            array_answers.clear()
            array_answers.extend(item[1:])
        elif int(item[0]) == max_count_queens:
            array_answers.extend(item[1:])
    res_answers = array_answers


# Уладение одинаковых решений
def unique_answers():
    global res_answers
    res_answers = list(set(res_answers))


def background_task(data_dict):
    global in_process, res_answers
    in_process = True
    response = requests.get('http://localhost:5000/assign_task', json=data_dict)
    if response.status_code == 200:
        result = response.json()
        # for res in result:
        #     res_answers.extend([int(0), json.])
        res_answers = result
        correction_answers()
        unique_answers()
    in_process = False


@app.post("/solve")
async def solve(background_tasks: BackgroundTasks, body=Body()):
    size_matrix = body["size_matrix"]
    pos_queens = body["pos_queens"]
    data_dict = {'data': f'{size_matrix}|{[[int(i) for i in j] for j in pos_queens]}', 'name_files': ['kernel.py']}
    background_tasks.add_task(background_task, data_dict)
    return JSONResponse(content={"message": "Успешная передача данных"}, status_code=200)


@app.get("/check_process")
async def check_process():
    if in_process:
        return JSONResponse(content={"in_process": in_process}, status_code=403)
    else:
        return JSONResponse(content={"in_process": in_process}, status_code=200)


@app.get("/answers")
async def answers():
    global res_answers
    return JSONResponse(content={"answers": json.dumps(res_answers)}, status_code=200)
