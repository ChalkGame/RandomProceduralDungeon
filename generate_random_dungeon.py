import numpy as np
import sys
import random as rd
from pathfinding.core.grid import Grid
from pathfinding.finder.a_star import AStarFinder
from deform_rooms import deform_rooms as _deform_rooms


def create_map(width, height, min_rooms, max_rooms, min_width_room,
               max_width_room, min_height_room, max_height_room, deform_rooms):
    # Crear la matriz del 'mapa' guarda el contenido de cada casilla de la mazmorra:
    # np.ones((n,m),dtype=int) crea una matriz de tipo int de n*m y la rellena de 1
    Map = np.ones((height, width), dtype=int)
    # Significado del valor de las casillas:
    #   '0' - El espacio esta ocupado por el interior de una habitacion
    #   '1' - El espacio contiene tierra
    #   '2' - El espacio contiene el muro de una habitacion
    #   '3' - El espacio contiene un pasillo
    #   '4' - El espacio contiene una puerta
    #   '5' - El espacio contiene el muro de un pasillo

    # Este segundo mapa indica el coste de excavar un pasillo en una casilla de la mazmorra
    weights_map = np.ones((height, width), dtype=int)
    weights_map.fill(3)
    # Significado de los valores del mapa de costes:
    #   '0' - Coste 'infinito' (muro de habitacion - no se puede excavar)
    #   '1' - Coste bajo (interior de habitaciones)
    #   '2' - Coste medio (pasadizos ya excavados)
    #   '3' - Coste alto (casillas aun no excavadas)

    # Colocar habitaciones sobre la matriz del mapa y guardar sus centros
    centers, rooms_info = place_rooms(width, height, Map,
                                      weights_map, max_rooms, min_rooms, min_width_room,
                                      max_width_room, min_height_room, max_height_room)

    # # Unir las habitaciones con pasillos con su camino minimo
    create_hallways(Map, weights_map, centers)

    dr = [-1, -1, -1, 0, 0, 1, 1, 1]
    dc = [-1, 0, 1, -1, 1, -1, 0, 1]

    # Algunas pasadas para retocar detalles

    _Map = Map.copy()

    # Si en las casillas vecinas de los pasillos hay tierra colocar pasillo tambien
    # para tratar de tener pasillos con + ancho
    for r in range(height):
        for c in range(width):
            if Map[r, c] == 3 and _Map[r][c] != -1:
                for d in range(len(dr)):
                    k = 1
                    nr = r+dr[d]*k
                    nc = c+dc[d]*k
                    if isIn(nr, nc, width, height) and Map[nr][nc] == 1 and _Map[nr][nc] != -1:
                        Map[nr][nc] = 3
                        _Map[nr][nc] = -1

    # Analizar los bordes de cada pasillo, y si s tierra lo q hay, ponemos muros
    for r in range(height):
        for c in range(width):
            if Map[r, c] == 3:
                for d in range(len(dr)):
                    k = 1
                    nr = r+dr[d]*k
                    nc = c+dc[d]*k
                    if isIn(nr, nc, width, height) and Map[nr][nc] == 1:
                        Map[nr][nc] = 5

    # Para quitar todo el espacio que sobre, o sea, si los bordes del mapa son vacio, los kito
    # countUp = 0
    # for r in range(width):
    #     if row_is_all_x(Map, r, 1):
    #         countUp += 1
    #     else:
    #         break

    # countDown = height
    # for r in range(width):
    #     if row_is_all_x(Map, height-r-1, 1):
    #         countDown -= 1
    #     else:
    #         break

    # countLeft = 0
    # for c in range(height):
    #     if col_is_all_x(Map, c, 1, height):
    #         countLeft += 1
    #     else:
    #         break

    # countRight = width
    # for c in range(height):
    #     if col_is_all_x(Map, width-c-1, 1, height):
    #         countRight -= 1
    #     else:
    #         break

    # countUp -= 1
    # countDown += 1
    # countLeft -= 1
    # countRight += 1

    # cu_valid = countUp >= 0
    # cd_valid = countDown < height
    # cl_valid = countLeft >= 0
    # cr_valid = countRight < width

    # for c in range(width):
    #     if cu_valid:
    #         Map[countUp][c] = -1
    #     if cd_valid:
    #         Map[countDown][c] = -1

    # for r in range(height):
    #     if cl_valid:
    #         Map[r][countLeft] = -1
    #     if cr_valid:
    #         Map[r][countRight] = -1

    # --------------------------------------------------------------------------------------
    # -------------------Deformar cada habitacion con un automata celular-------------------
    # --------------------------------------------------------------------------------------

    if deform_rooms:
        # Minimo de vecinos que debe tener una celda para sobrevivir, recomendado 3
        lim_isolation = 3
        # Minimo de vecinos para que una celda muerta pase a estar viva, recomendado 4
        lim_birth = 4
        # Numero de iteraciones para el automata celular (cantida de pasos), recomendado 5-6
        n = 5
        # Probabilidad de inicializar una celda como viva, recomendado 0.4
        P = 0.4
        _deform_rooms(Map, width, height, rooms_info,
                     lim_isolation, lim_birth, n, P)

    return Map, rooms_info


# def row_is_all_x(Map, r, x):  # ver si una fila es completamente de tipo x
#     for item in Map[r]:
#         if item != x:
#             return False
#     return True


# def col_is_all_x(Map, c, x, height):  # ver si una columna es completamente de tipo x
#     for r in range(height):
#         if Map[r][c] != x:
#             return False
#     return True


def isIn(r, c, width, height):
    return r >= 0 and c >= 0 and r < height-1 and c < width-1


def create_hallways(Map, weights_map, centers):

    # Crear el objeto AStarFinder()
    finder = AStarFinder()

    # Guardar la primera habitacion creada
    first_room = centers[0]

    # Crear los dos vectores de habitaciones
    rooms_visited = [centers[0]]
    rooms_unresolved = centers[1:]

    # Array para guardar las casillas de los pasillos
    hallways = []

    while len(rooms_unresolved) > 0:
        # Crear un objeto Grid a partir del mapa de costes
        grid = Grid(matrix=weights_map)

        # Elegimos una habitacion de la lista de habitaciones visitadas
        room1 = rd.choice(rooms_visited)

        # Cada habitacion tiene 1/3 probabilidades de formar un ciclo con una habitacion ya visitada
        if rd.randint(1, 3) == 1 and len(rooms_visited) > 1:
            room2 = rd.choice(rooms_visited)
            while(room2 == room1):
                room2 = rd.choice(rooms_visited)

        else:
            # Elegimos otra habitacion de la lista de habitaciones pendientes
            room2 = rd.choice(rooms_unresolved)

            # Ponemos la 2a habitacion en la lista de visitadas
            rooms_visited.append(room2)
            rooms_unresolved.remove(room2)

        # Guardar las dos casillas como nodos
        start = grid.node(room1[0], room1[1])
        end = grid.node(room2[0], room2[1])

        # Para hallar el kmino minimo del nodo start al nodo end
        path, _ = finder.find_path(start, end, grid)

        # Actualizar el mapa de costes y guardar los pasillos en el array
        for _grid in path:
            # Guardar las casillas del camino en el array de pasillos
            hallways.append(_grid)

            # Actualizar el mapa de costes con el nuevo pasadizo
            if weights_map[_grid[1]][_grid[0]] == 3:
                weights_map[_grid[1]][_grid[0]] = 2

    # Poner los pasillos en el array del mapa
    for _grid in hallways:
        r = _grid[1]
        c = _grid[0]

        # Si el espacio es un muro, colocar una puerta
        if Map[_grid[1]][_grid[0]] == 2:
            Map[_grid[1]][_grid[0]] = 4

        # Si el espacio contiene tierra, colocar un pasillo
        elif Map[_grid[1]][_grid[0]] == 1:
            r = _grid[1]
            c = _grid[0]
            Map[r][c] = 3


def place_rooms(width, height, Map, weights_map, max_rooms, min_rooms, min_width_room,
                max_width_room, min_height_room, max_height_room):
    # Numero de habitaciones colocadas hasta el momento
    amount_placed_rooms = 0

    # Creamos un array para guardar las coordenadas de todos los centros de las habitaciones
    centers = []
    # Creamos un array para guardar las coordenadas iniciale, ancho y largo de cada habitacion
    rooms_info = []

    # Al menos deben haber min_rooms habitaciones
    while amount_placed_rooms < min_rooms:
        # Para evitar un ciclo infinito, hay 1000 intentos para colocar las habitaciones
        for i in range(1000):
            # Elegir las dimensiones del interior de la habitacion
            sizex = rd.randint(min_width_room, max_width_room)
            sizey = rd.randint(min_height_room, max_height_room)

            # Elegir una posicion random para la esquina superior izquierda de la habitacion,
            # evitando los bordes del mapa
            posx = rd.randint(5, width-sizex-1-5)
            posy = rd.randint(5, height-sizey-1-5)

            # Comprobar que se pueda colocar la habitacion sin que quede por encima o quede
            # pegada a otra habitacion
            submap = Map[(posy-3):(posy+sizey+3), (posx-3):(posx+sizex+3)]

            if np.all(submap == 1):
                # Actualizar el coste de estas casillas en el mapa de costes
                # Los muros tienen coste infinito
                weights_map[(posy-1):(posy+sizey+1),
                            (posx-1):(posx+sizex+1)] = 0
                # El interior tiene coste bajo
                weights_map[(posy):(posy+sizey), (posx):(posx+sizex)] = 1

                # Construir la habitacion con sus muros
                Map[(posy-1):(posy+sizey+1), (posx-1)
                     :(posx+sizex+1)] = 2  # muro
                # Map[(posy+1):(posy+sizey-1), (posx+1):(posx+sizex-1)] = 0  # interior
                Map[(posy):(posy+sizey), (posx):(posx+sizex)] = 0  # interior

                # Guardamos las coordenadas del centro de la habitacion en el array de centros
                cx = posx + int(sizex/2)
                cy = posy + int(sizey/2)
                centers.append((cx, cy))
                rooms_info.append((posx, posy, sizex, sizey))

                # Elegimos al azar las paredes de la habitacion donde vamos a colocar las puertas
                chosen_walls = rd.sample(
                    ["north", "east", "west", "south"], k=rd.randint(1, 4))

                for wall in chosen_walls:
                    if wall == "north":
                        # Coordenadas (y,x) para la puerta norte
                        cy = posy-1
                        cx = int(posx+(sizex+1)/2)

                    elif wall == "east":
                        # Coordenadas (y,x) para la puerta este
                        cy = int(posy-1+(sizey+1)/2)
                        cx = posx+sizex

                    elif wall == "west":
                        # Coordenadas (y,x) para la puerta oeste
                        cy = int(posy-1+(sizey+1)/2)
                        cx = posx-1
                    else:
                        cy = posy+sizey
                        cx = int(posx+(sizex+1)/2)

                    # Colocamos una apertura en el muro de la habitacion
                    weights_map[cy][cx] = 1

                # Si se ha llegado al maximo de habitaciones, salir del ciclo
                amount_placed_rooms += 1
                if max_rooms == amount_placed_rooms:
                    break

    return centers, rooms_info
