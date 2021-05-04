import random
import numpy as np
import sys
from pathfinding.core.grid import Grid
from pathfinding.finder.a_star import AStarFinder


# Deformar cada habitacion con un automata celular(levantar muros o no, segun el estado de cada celula)
def deform_rooms(Map, width, height, rooms_info, lim_isolation, lim_birth, n, P):
    rooms = np.copy(rooms_info)
    for room in rooms:  # recorremos cada habitacion
        # Sub-mapa con muros
        x_w = room[0]-1
        y_w = room[1]-1
        sizex_w = room[2]+2
        sizey_w = room[3]+2

        # Sub-mapa del interior de la habitacion
        x_i = room[0]
        y_i = room[1]
        sizex_i = room[2]
        sizey_i = room[3]

        # EL q tiene muros
        submap_w = Map[y_w:(y_w+sizey_w), x_w:(x_w+sizex_w)]
        # El interior de la habiacio
        submap_i = Map[y_i:(y_i+sizey_i), x_i:(x_i+sizex_i)]

        doors = []

        # Ver si hay puertas en la 1ra fila o en la ultima, y lo mismo para las los columnas
        # , y si hay, guardar sus coordenadas
        # xq con esto quiero luego de deformar la habitacion, unir la region resultante con todas
        # las puertas, para q no halla ninguna puerta q no lleve a nigun lado.
        # Pero como yo deformo el interior de la habitacion, y en este no hay puerta,
        # al terminar de deformar, por cada una de las puertas, hallo la coordenada de la casilla
        # vecina a esta perpendicular dentro d la cueva, sea esta P, luego hallo un camino de P a
        # cualquier casilla de la habitacion que no sea muro, o sea, uno a P con la region generada

        for _x in range(sizex_w):
            if submap_w[0][_x] == 4:
                doors.append((_x-1, 0))
            if submap_w[sizey_w-1][_x] == 4:
                doors.append((_x-1, sizey_i-1))

        for _y in range(sizey_w):
            if submap_w[_y][0] == 4:
                doors.append((0, _y-1))
            if submap_w[_y][sizex_w-1] == 4:
                doors.append((sizex_i-1, _y-1))

        # for _y in range(sizey_i):
        #     for _x in range(sizex_i):
        #         print(submap_i[_y][_x], end=' ')
        #     print()
        # print('')

        submap_i = create_deform_room(
            sizex_i, sizey_i, lim_isolation, lim_birth, n, P, doors)

        # for _y in range(sizey_i):
        #     for _x in range(sizex_i):
        #         print(submap_i[_y][_x], end=' ')
        #     print()
        # print('')

        for _y in range(sizey_i):
            for _x in range(sizex_i):
                # print(submap_i[_y][_x], end=' ')
                if submap_i[_y][_x] != 0:
                    Map[y_i+_y][x_i+_x] = 2
            # print()
        # print('')

    return Map


def create_deform_room(dimx, dimy, lim_isolation, lim_birth, n, P, doors):
    # print(doors)
    Map = np.zeros((dimy, dimx), dtype=int)

    # Inicializar el mapa aleatoriamente
    init_map(Map, P)

    # Hacer n pasos del automata celular
    for i in range(n):
        Map = calculate_step(Map, lim_isolation, lim_birth)

    # Unir zonas aisladas
    Map = link_regions(Map, doors)

    return Map


def init_map(Map, P):
    # Init el mapa. Cada casilla tiene una probabilidad P de
    # inicializarse como viva.

    # Inicializar todas las casillas:
    for r in range(len(Map)):
        for c in range(len(Map[0])):
            # Generar un valor aleatorio entre 0 y 1
            U = random.uniform(0, 1)
            # Variable aleatoria con Esquema de Bernoulli
            if U < P:
                Map[r][c] = 1


def count_living_neighbors(Map, x, y):
    # Cuenta el numero de vecinos vivos que tiene Map[y][x]

    # Dimensiones del mapa
    dimy = len(Map)
    dimx = len(Map[0])

    # Numero de vecinos vivos:
    count = 0

    # Comprobar los vecinos
    for i in range(-1, 2):
        for j in range(-1, 2):

            # No contar la casilla del centro!
            if i == 0 and j == 0:
                pass

            # Si no estamos en el centro...
            else:
                # Coordenadas del vecino
                neighborx = x + i
                neighbory = y + j

                # Supondremos que todas las casillas que hay fuera del mapa estan 'vivas' (son paredes)
                if (neighborx < 0 or neighborx >= dimx or neighbory < 0 or neighbory >= dimy):
                    count += 1

                # Si es una casilla del interior del mapa se suma su valor al contador
                # (0 si esta muerta y 1 si esta viva)
                else:
                    count += Map[neighbory][neighborx]

    return count


def calculate_step(Map, lim_isolation, lim_birth):
    # Calcula una iteracion del automata celular

    # Dimensiones del mapa original (Map)
    dimy = len(Map)
    dimx = len(Map[0])

    # Map auxiliar
    Map_aux = np.zeros((dimy, dimx), dtype=int)
    # El valor de las casillas se actualizará en el mapa auxiliar

    # Por cada casilla del mapa aplicar las reglas del automata celular
    for x in range(dimx):
        for y in range(dimy):

            # Calcular el numero de vecinos
            _count_living_neighbors = count_living_neighbors(Map, x, y)

            # Si la celda esta viva, comprobar si muere de aislamiento
            if Map[y][x] == 1:
                if _count_living_neighbors < lim_isolation:
                    Map_aux[y][x] = 0
                else:
                    Map_aux[y][x] = 1

            # Si la celda esta muerta, comprobar si tiene que nacer
            elif Map[y][x] == 0:
                if _count_living_neighbors > lim_birth:
                    Map_aux[y][x] = 1
                else:
                    Map_aux[y][x] = 0

    # Actualizar el mapa original
    return Map_aux


def find_all_region(dimx, dimy, Map_aux):
    # calcula todas las regiones

    # Vector para guardar el valor de las areas de cada region
    regions = []
    # NOTA: el elemento [0] se corresponde a la region '2', [1] es la region '3', etc.

    # Recorremos el mapa
    for x in range(dimx):
        for y in range(dimy):
            # Si la casilla actual es un espacio vacio, aplicar FloodFill para "infestar" toda la region
            if Map_aux[y][x] == 0:
                # Aplicar Flood-Fill y guardar la region
                region = floodFill(Map_aux, y, x, len(regions)+5)
                regions.append(region)
    return regions


def create_hallways(Map, regions):
    # Crea caminos que unan todas las regiones, sin ciclos
    # (MaxST con cada region como un nodo y su camino una arista)
    # print(f'len regions {len(regions)}')

    # Crear el objeto AStarFinder()
    finder = AStarFinder()

    first_region = regions[0]
    regions_visited = [first_region]
    regions_unresolved = regions[1:]

    # hallways = []

    Map_ones = np.ones((len(Map), len(Map[0])), dtype=int)

    while regions_unresolved:
        grid = Grid(matrix=Map_ones)

        region_u = regions_visited.pop()
        region_v = regions_unresolved.pop()

        regions_visited.append(region_v)

        # Hasta aqui tenemos la region u y la region v, queremos hallar un camino que las una
        #  Escogemos cualquier casilla de u y cualquiera de v y encontramos el camino minimo
        # que las una, con 'finder.find_path'.

        _u = region_u[0]
        _v = region_v[0]
        # Guardar las casillas u, v como nodos
        u = grid.node(_u[0], _u[1])
        v = grid.node(_v[0], _v[1])

        path, _ = finder.find_path(u, v, grid)

        # hallways.append(path)

        # Actualizar el mapa con los nuevos caminos
        for _grid in path:
            x = _grid[0]
            y = _grid[1]
            Map[y][x] = 0


def link_regions(Map, doors):
    # Encuentra cada region del mapa y las une mediante caminos(no de longitud minima, sino random)
    # pues se escog una casilla de cada region y se unen, estas si con su camino minimo, pero el kmino minimo entre dos regiones no tiene 
    # xq ser el de dos casillar cualeskiera

    # Dimensiones del mapa original
    dimy = len(Map)
    dimx = len(Map[0])

    # Como en el mapa tenemos 0s y is, las regiones las etiquetaremos con numeros a partir del 2

    # Crear un mapa auxiliar que sea una copia del mapa original
    Map_aux = np.copy(Map)

    # Todas las regiones
    regions = find_all_region(dimx, dimy, Map_aux)

    for door in doors:
        regions.append([door])
        # x = door[0]
        # y = door[1]
        # Map[y][x] = 0

    # Crear los caminos entre las regiones, en forma de arbol
    create_hallways(Map, regions)

    # Devolver el mapa actualizado con todas las regiones
    return Map


def floodFill(Map, posy, posx, num_region):
    # Llena ('infesta') todas las casillas de una region con el mismo numero (num_region)
    # y devuelve dicha region

    # Dimensiones del mapa original
    ysize = len(Map)
    xsize = len(Map[0])

    # Stack, para guardar las casillas de la region
    s = set(((posy, posx),))

    # Region
    region = []

    # Repetir mientras haya elementos en la pila
    while s:
        # Guardar las coordenadas (row, col) del objeto de la pila
        y, x = s.pop()

        # actualiza la region con la nueva casilla
        region.append((x, y))

        # "Infestar" la casilla
        if Map[y][x] == 0:
            Map[y][x] = num_region
            if y > 0:
                s.add((y - 1, x))
            if y < (ysize - 1):
                s.add((y + 1, x))
            if x > 0:
                s.add((y, x - 1))
            if x < (xsize - 1):
                s.add((y, x + 1))

    # Devolver la region
    return region
