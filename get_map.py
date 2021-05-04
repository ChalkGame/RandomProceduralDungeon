# from colorama import init, Fore, Back, Style
import sys
from generate_random_dungeon import create_map


def pretty_draw_map(width, height, Map):
    # init(autoreset=True)
    # mapear todo el mapa
    for y in range(height):
        print("\n", end='')
        for x in range(width):

            # Interior de habitacion
            if Map[y][x] == 0:
                print(Fore.GREEN + ". ", end='')

            # Espacio vacio
            if Map[y][x] == 1:
                print("  ", end='')

            # Muros de habitacion
            elif Map[y][x] == 2:
                print(Fore.RED+"# ", end="")

            # Muros de habitacion
            elif Map[y][x] == 5:
                print(Fore.WHITE+"# ", end="")

            # Pasillo
            elif Map[y][x] == 3:
                print(Fore.YELLOW + ', ', end='')

            # Puerta
            elif Map[y][x] == 4:
                print(Fore.BLUE+'D ', end='')


def draw_map(width, height, Map):
    # mapear todo el mapa
    for y in range(height):
        for x in range(width):
            print(f'{y} {x} {Map[y][x]}|', end='')


if __name__ == "__main__":
    _args = sys.argv
    # ancho del mapa
    width = int(_args[1])
    # largo del mapa
    height = int(_args[2])
    # ancho minimo de una habitacion
    min_width_room = int(_args[3])
    # ancho maximo de una habitacion
    max_width_room = int(_args[4])
    # altura minima de una habitacion
    min_height_room = int(_args[5])
    # altura maxima de una habitacion
    max_height_room = int(_args[6])
    # bool para saber si deformar o no cada habitacion usando el automata celular
    deform_rooms = _args[7]
    if deform_rooms == 'yes':
        deform_rooms = True
    elif deform_rooms == 'no':
        deform_rooms = False
    # cantidad minima de habitaciones
    min_rooms = int(_args[8])
    # cantidad maxima de habitaciones
    max_rooms = int(_args[9])

    # # Dimensiones del mapa
    # width = 65
    # height = 35

    # min_width_room = 3
    # max_width_room = 10
    # min_height_room = 3
    # max_height_room = 10

    # # min_rooms = (width*height)//(max_width_room*max_height_room)
    # min_rooms = 5
    # max_rooms = (width*height)//(((max_width_room+min_width_room)//2)
    #                              * ((max_height_room+min_height_room)//2))

    # # bool para saber si deformar o no cada habitacion usando el automata celular
    # deform_rooms = False

    Map, rooms_info = create_map(width, height, min_rooms, max_rooms, min_width_room,
                                 max_width_room, min_height_room, max_height_room, deform_rooms)

    # print(len(rooms_info))

    # Dibujar el mapa
    draw_map(width, height, Map)
