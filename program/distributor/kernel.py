#!/usr/bin/env python
import copy
import sys
import ast
import re

iter_range = 0  # Сколько ячеек прошли
last_value_col = {}
flag_starting_position = True


DIMENSION = int(sys.argv[1])  # Размер поля
QUEEN_POSITIONS = ast.literal_eval(sys.argv[2].replace(' ', ''))  # Позиции ферзей [0,0]
CELLS_FOR_PASSAGE = re.split(';|-', sys.argv[3])  # Ячейки, которые необходимо пройти 1-2;4-18;
maximumNumberQueens = len(QUEEN_POSITIONS)
solutionCounter = 0  # Количество расстановок
placementOptions = []  # Варианты расстановок

START_LINE = int(CELLS_FOR_PASSAGE[0])
END_LINE = int(CELLS_FOR_PASSAGE[1])
START_COLUMN = int(CELLS_FOR_PASSAGE[2])
END_COLUMN = int(CELLS_FOR_PASSAGE[3])


def checkingPosition(positions, newPosition):
    """
        Проверяет позицию ферзя (newPosition), чтобы не попадала под удар других фигур на доске (positions)

        Input:
        positions - [ [1,1], [2,3], [4,3] ]
        newPosition - [5,5]

        Output:
        resultСheck - Boolean
    """
    for _, position in enumerate(positions):

        # Проверяем вертикаль
        if position[1] == newPosition[1]:
            return False

        # Проверяем горизонталь
        elif position[0] == newPosition[0]:
            return False

        # Проверяем диагональ
        else:
            rowDiff = position[0] - newPosition[0]
            colDiff = position[1] - newPosition[1]
            intersection = abs(rowDiff / colDiff) == 1
            if intersection:
                return False
    return True


def solutionGenerator(positions, row):
    """ Функция генератор. Предлагает новые позиции. """
    """
    Проверка на случай, если строка шахматной доски последняя, и дальнейшая обработка не будет выполняться.
    В этом случае проверяем количество найденных комбинаций и при необходимости их обновляем.
    """
    global solutionCounter, maximumNumberQueens, iter_range, flag_starting_position, last_value_col
    if len(positions) > maximumNumberQueens and row == DIMENSION:
        maximumNumberQueens = len(positions)
        solutionCounter = 1
        placementOptions.clear()
        placementOptions.append(copy.deepcopy(positions))
        return
    if len(positions) == maximumNumberQueens and positions and row == DIMENSION:
        solutionCounter += 1
        placementOptions.append(copy.deepcopy(positions))
        return
    if len(positions) < maximumNumberQueens and row == DIMENSION:
        return

    """
    На случай, когда алгоритму нужно начинать обход доски не с начальной позиции [0, 0], а из середины.
    """
    starting_position = 0
    if flag_starting_position:
        starting_position = 0 if START_COLUMN % DIMENSION == 0 else START_COLUMN % DIMENSION
        flag_starting_position = False

    """
    Поиск с возвратом. Описание алгоритма есть в интернете.
    """
    for column in range(starting_position, DIMENSION):
        startingPosition = [row, column]  # Начальная позиция нового ферзя
        if checkingPosition(positions, startingPosition):  # Проверяем, что новая позиция еще не под ударом
            positions.append(startingPosition)
            solutionGenerator(positions, getNextRow(QUEEN_POSITIONS, row))
            positions.pop()
        if column == DIMENSION - 1 and not [x[0] for x in positions].count(row):
            solutionGenerator(positions, getNextRow(QUEEN_POSITIONS, row + 1))

        # Условия для выхода по концу шага
        if len(positions) != 0 and not (positions[0] in last_value_col.values()):
            iter_range += 1
            last_value_col[tuple(positions[0])] = positions[0]
        if iter_range > (END_COLUMN - START_COLUMN + 1):
            return


"""
Получить индекс следующей свободной строки
"""
numRows = [r for r in range(DIMENSION)]


def getNextRow(arrangements=[], currentRow=0):
    """
    Функция, которая определяет какая следующая строка доступна (находится не под ударом).
    """
    arrangementsRow = sorted([x[0] for x in arrangements])
    occupiedRows = list(set(arrangementsRow))
    for indexRow, valueRow in enumerate(numRows):
        lstRes = [
            checkingPosition(arrangements, [valueRow, res[1]])
            for res in enumerate(numRows)
            if checkingPosition(arrangements, [valueRow, res[1]])
        ]
        if not occupiedRows.count(valueRow) and valueRow >= currentRow and lstRes.count(True):
            return valueRow
    return DIMENSION


solutionGenerator(QUEEN_POSITIONS, getNextRow(QUEEN_POSITIONS, START_LINE))
print(maximumNumberQueens)
for _, solution in enumerate(placementOptions):
    print(solution)
