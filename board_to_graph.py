import argparse


def make_base_connections(nr_cells, nr_dice_sides):
    connections = []
    for cell in range(1, nr_cells+1):
        for reached in range(cell+1, cell+nr_dice_sides+1):
            if reached <= nr_cells:
                connections.append((cell, reached))
    return connections

def add_ladders(connections, ladder_starts, ladder_ends):
    modified_connections = []
    for con in connections:
        if con[1] in ladder_starts:
            ind = ladder_starts.index(con[1])
            modified_connections.append((con[0], ladder_ends[ind]))
        elif not (con[0] in ladder_starts):
            modified_connections.append(con)
    return modified_connections

def add_snakes(connections, snake_starts, snake_ends):
    modified_connections = []
    for con in connections:
        if con[1] in snake_starts:
            ind = snake_starts.index(con[1])
            modified_connections.append((con[0], snake_ends[ind]))
        elif not (con[0] in snake_starts):
            modified_connections.append(con)

    return modified_connections

def connections_to_graph(connections):
    pass

if __name__ == "__main__":
    def list_of_ints(arg):
        return list(map(int, arg.split(',')))

    parser = argparse.ArgumentParser()
    parser.add_argument('--nr_cells', type=int, default=10)
    parser.add_argument('--nr_dice_sides', type=int, default=4)
    parser.add_argument('--snake_starts', type=list_of_ints)
    parser.add_argument('--snake_ends', type=list_of_ints)
    parser.add_argument('--ladder_starts', type=list_of_ints)
    parser.add_argument('--ladder_ends', type=list_of_ints)
    args = parser.parse_args()

    base_connections = make_base_connections(args.nr_cells, args.nr_dice_sides)
    connections = add_ladders(base_connections, args.ladder_starts, args.ladder_ends)
    final_connections = add_snakes(connections, args.snake_starts, args.snake_ends)
    network = connections_to_graph(final_connections)

    # Example usage (using the board from my notebook):
    # python board_to_graph.py --nr_cells 9 --nr_dice_sides 4 --ladder_starts 2 --ladder_ends 6 --snake_starts 8 --snake_ends 3