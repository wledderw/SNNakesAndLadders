import argparse
from simsnn.core.networks import Network
from simsnn.core.simulators import Simulator
import numpy as np

def make_base_connections(nr_cells, nr_dice_sides):
    """
    Creates a list of base connections between cells on a game board based on dice rolls.

    Args:
        nr_cells (int): Number of cells on the board.
        nr_dice_sides (int): Number of sides on the dice.

    Returns:
        list: A list of tuples representing connections in the form (start_cell, end_cell, dice_roll).
    """
    connections = []
    for cell in range(0, nr_cells + 1):
        for throw in range(1, nr_dice_sides + 1):
            if cell + throw <= nr_cells:
                connections.append((cell, cell + throw, throw))
    return connections

def add_ladders(connections, ladder_starts, ladder_ends):
    """
    Modifies the connections to incorporate ladders on the board.

    Args:
        connections (list): List of base connections.
        ladder_starts (list): List of starting positions of ladders.
        ladder_ends (list): List of ending positions of ladders.

    Returns:
        list: Modified list of connections with ladders.
    """
    modified_connections = []
    for con in connections:
        if con[1] in ladder_starts:
            ind = ladder_starts.index(con[1])
            modified_connections.append((con[0], ladder_ends[ind], con[2]))
        elif not (con[0] in ladder_starts):
            modified_connections.append(con)
    return modified_connections

def add_snakes(connections, snake_starts, snake_ends):
    """
    Modifies the connections to incorporate snakes on the board.

    Args:
        connections (list): List of base connections.
        snake_starts (list): List of starting positions of snakes.
        snake_ends (list): List of ending positions of snakes.

    Returns:
        list: Modified list of connections with snakes.
    """
    modified_connections = []
    for con in connections:
        if con[1] in snake_starts:
            ind = snake_starts.index(con[1])
            modified_connections.append((con[0], snake_ends[ind], con[2]))
        elif not (con[0] in snake_starts):
            modified_connections.append(con)
    return modified_connections

def connections_to_graph(nr_cells, nr_dice_sides, connections, net, sim):
    """
    Converts the board connections into a neural network graph.

    Args:
        nr_cells (int): Number of cells on the board.
        nr_dice_sides (int): Number of sides on the dice.
        connections (list): List of connections on the board.
        net (object): Neural network object to create neurons and synapses.
        sim (object): Simulation object to add raster targets.

    Returns:
        None
    """
    board_neurons = []
    read_neurons = []
    start_neuron = net.createInputTrain(train=[1], loop=False, ID="B0")
    board_neurons.append(start_neuron)
    for c in range(nr_cells):
        # Adding a neuron for each square on the board
        neuron = net.createLIF(ID=f"B{c+1}", thr=nr_cells * nr_dice_sides + 1, V_reset=0, m=1, V_init=nr_cells * nr_dice_sides)
        board_neurons.append(neuron)
        for d in range(nr_dice_sides):
            # Adding read-out neurons to track what throw was used to get there
            read_neuron = net.createLIF(ID=f"R{c+1}-D{d+1}", thr=nr_cells * nr_dice_sides + 1, V_reset=0, m=1, V_init=nr_cells * nr_dice_sides)
            read_neurons.append(read_neuron)

    # Adding synapses and ladder/snake neurons
    ladder_read_neurons = []
    snake_read_neurons = []
    for c in connections:
        (start_neuron, post_neuron, throw) = c
        # Synapse between board neurons
        net.createSynapse(pre=board_neurons[start_neuron], post=board_neurons[post_neuron], ID=f"s{start_neuron}, p{post_neuron}, d{throw}", w=1, d=1)

        # Synapse between board neurons and read-out neurons
        read_index = (post_neuron - 1) * nr_dice_sides + (throw - 1)

        # Create read-out neurons/synapses to check if a ladder/snake was used
        if post_neuron - start_neuron != throw:
            # If ladder
            if post_neuron - start_neuron > throw:
                ladder_read_neuron = net.createLIF(ID=f"L{post_neuron}-D{throw}", thr=nr_cells * nr_dice_sides + 1, V_reset=0, m=1, V_init=nr_cells * nr_dice_sides)
                ladder_read_neurons.append(ladder_read_neuron)
                net.createSynapse(pre=board_neurons[start_neuron], post=ladder_read_neuron, ID=f"s{start_neuron}, p{post_neuron}, d{throw}", w=1, d=1)
            # If snake
            elif post_neuron - start_neuron < throw:
                snake_read_neuron = net.createLIF(ID=f"S{post_neuron}-D{throw}", thr=nr_cells * nr_dice_sides + 1, V_reset=0, m=1, V_init=nr_cells * nr_dice_sides)
                snake_read_neurons.append(snake_read_neuron)
                net.createSynapse(pre=board_neurons[start_neuron], post=snake_read_neuron, ID=f"s{start_neuron}, p{post_neuron}, d{throw}", w=1, d=1)
        else:
            net.createSynapse(pre=board_neurons[start_neuron], post=read_neurons[read_index], ID=f"s{start_neuron}, p{post_neuron}, d{throw}", w=1, d=1)

    sim.raster.addTarget(read_neurons)
    sim.raster.addTarget(ladder_read_neurons)
    sim.raster.addTarget(snake_read_neurons)
    sim.raster.addTarget(board_neurons)


def get_shortest_path(sim, ladder_starts, ladder_ends, snake_starts, snake_ends):
    """
    Function that finds one shortest path.
    - sim: the simulation object as returned by the SNN.
    - ladder_starts: the spaces on which ladders have their starts
    - ladder_ends: the spaces on which ladders have their ends, where each
      ladder end index corresponds with the same index for ladder starts
    - snake_starts: the spaces on which snakes have their starts
    - snake_ends: the spaces on which snakes have their ends, where each
      snake end index corresponds with the same index for snake starts
    Returns:
    - a list with the log.
    - a list with the dice throws.
    """

    # Get raster and label data:
    raster = np.array(sim.get_raster_data()).T
    labels = sim.raster.get_labels()

    # Make a list of nodes and a dictionary of nodes with their edges:
    nodes = [int(nr[1:]) for nr in labels if nr[0] == 'B']
    edges = dict()
    for node in nodes:
        edges[node] = [edge for edge in labels if edge.split('-')[0][0] != 'B' and int(edge.split('-')[0][1:]) == node]

    # Find final node:
    final_node = max(nodes)
    # Find final timestep:
    t = np.where(raster[-1])[0][0]

    # Initialize the list of dice throws:
    dice_throws = []
    log = [f"You reached the finish by reaching final space {final_node}."]

    # Backtrack the spiked neurons:
    node = final_node
    while node != 0 and t >= 0:  # Backtrack back until the start of simulation
        node_edges = edges[node]  # Get the edges of this node
        diff = 0

        node_edge = None
        for potential_node_edge in node_edges:
            row = labels.index(potential_node_edge)
            if raster[row, t]:
                node_edge = potential_node_edge

        # If this node is a ladder end:
        if node_edge[0] == 'L':
            end = node
            start = ladder_starts[ladder_ends.index(end)]
            diff = end - start  # Extra moves because of ladder
            log.append(f"Now, you are on {start}, take a ladder from here.")

        # If this node is a snake start:
        if node_edge[0] == 'S':
            # if node in snake_starts:
            start = node
            end = snake_starts[snake_ends.index(start)]
            diff = start - end  # Extra (negative) moves because of snake
            log.append(f"Now, you are on {end}, take a snake from here.")

        # Get dice throw and add to history list:
        dice = int(node_edge.split('-')[1][1:])
        dice_throws.append(dice)
        # Go to new node and new timestep:
        node -= (diff + dice)
        t -= 1

        log.append(f"You throw a {dice}.")
        if node != 0:
            log.append(f"You are now on space {node}.")
        else:
            log.append("You start on space 0.")


    return dice_throws[::-1], log[::-1]


def get_all_shortest_paths(sim, ladder_starts, ladder_ends, snake_starts, snake_ends):
    """
    Function that finds all shortest paths.
    - sim: the simulation object as returned by the SNN.
    - ladder_starts: the spaces on which ladders have their starts
    - ladder_ends: the spaces on which ladders have their ends, where each
      ladder end index corresponds with the same index for ladder starts
    - snake_starts: the spaces on which snakes have their starts
    - snake_ends: the spaces on which snakes have their ends, where each
      snake end index corresponds with the same index for snake starts
    Returns:
    - a list of lists with the log.
    - a list of lists with the dice throws.
    """

    # Get raster and label data:
    raster = np.array(sim.get_raster_data()).T
    labels = sim.raster.get_labels()

    # Make a list of nodes and a dictionary of nodes with their edges:
    nodes = [int(nr[1:]) for nr in labels if nr[0] == 'B']
    edges = dict()
    for node in nodes:
        edges[node] = [edge for edge in labels if edge.split('-')[0][0] != 'B' and int(edge.split('-')[0][1:]) == node]

    # Find final node:
    final_node = max(nodes)
    # Find final timestep:
    t = np.where(raster[-1])[0][0]

    # Initialize the list of dice throws:
    dice_throws = []
    log = [f"You reached the finish by reaching final space {final_node}."]

    logs = []
    dice_throws_list = []

    # Backtrack the spiked neurons:
    node = final_node


    def get_all_paths(node, log, dice_throws, grid, t):
        """
        Recursive function that finds all possible shortest paths, by using the
        node activations from the SNN.
        - node: the current node index.
        - log: the current log showing the moves we have taken: dice throws,
          snake/ladder usage, spaces we have been on.
        - dice_throws: a list with all dice throws we made.
        - t: the current time step.
        """

        # Count amount of options we have to get to the current node:
        count = 0
        for edge in edges[node]:
            if grid[labels.index(edge), t]:
                count += 1

        # Base case: we reached the start
        if node == 0 and t == 0:
            logs.append(log[::-1])
            dice_throws_list.append(dice_throws[::-1])
            return

        # Step case: there is just one activation for the current time step
        elif count == 1:
            diff = 0

            # Find the node activation for this timestep and for this particular node:
            activated_node_edges = np.array(labels)[np.where(grid[:len(grid)-len(nodes),t] == 1)[0]]
            node_edge = None
            for activated_node_edge in activated_node_edges:
                if int(activated_node_edge.split("-")[0][1:]) == node:
                    node_edge = activated_node_edge

            # If this node is a ladder end:
            if node_edge[0] == 'L':
                end = node
                start = ladder_starts[ladder_ends.index(end)]
                diff = end - start  # Extra moves because of ladder
                log.append(f"Now, you are on {start}, take a ladder from here.")

            # If this node is a snake start:
            if node_edge[0] == 'S':
                # if node in snake_starts:
                start = node
                end = snake_starts[snake_ends.index(start)]
                diff = start - end  # Extra (negative) moves because of snake
                log.append(f"Now, you are on {end}, take a snake from here.")

            # Get dice throw and add to history list:
            dice = int(node_edge.split('-')[1][1:])
            dice_throws.append(dice)
            # Go to new node and new timestep:
            node -= (diff + dice)
            t -= 1

            log.append(f"You throw a {dice}.")
            if node != 0:
                log.append(f"You are now on space {node}.")
            else:
                log.append("You start on space 0.")

            get_all_paths(node, log, dice_throws, grid, t)

        # Step case 2: there are multiple options from the current node
        # Approach: copy activation matrix as many times as there are options,
        # change the column for t=τ with only one activation, then recurse with
        # this new activation matrix, without changing the value for t=τ.
        else:
            # Use activation matrix to get vectors with only one activation
            id_matrix = np.eye(len(grid)-len(nodes), dtype=int)
            # Only make single activations for the current node
            for i, row in enumerate(id_matrix):
                if int(labels[i].split("-")[0][1:]) != node:
                    continue
                activation_vector = grid[:len(grid)-len(nodes),t] & row
                if sum(activation_vector) == 1:
                    new_grid = grid.copy()
                    new_row = np.hstack((activation_vector, grid[len(grid)-len(nodes):,t]))  # Make sure to include activations for B nodes
                    new_grid[:,t] = new_row
                    get_all_paths(node, log.copy(), dice_throws.copy(), new_grid, t)

    get_all_paths(node, log, dice_throws, raster, t)

    return dice_throws_list, logs


if __name__ == "__main__":
    def list_of_ints(arg):
        return list(map(int, arg.split(',')))

    parser = argparse.ArgumentParser()
    parser.add_argument('--nr_cells', type=int, default=9)
    parser.add_argument('--nr_dice_sides', type=int, default=4)
    parser.add_argument('--snake_starts', type=list_of_ints, default=[])
    parser.add_argument('--snake_ends', type=list_of_ints, default=[])
    parser.add_argument('--ladder_starts', type=list_of_ints, default=[2])
    parser.add_argument('--ladder_ends', type=list_of_ints, default=[6])
    args = parser.parse_args()

    # Create the network and the simulator object
    net = Network()
    sim = Simulator(net)

    base_connections = make_base_connections(args.nr_cells, args.nr_dice_sides)
    connections = add_ladders(base_connections, args.ladder_starts, args.ladder_ends)
    final_connections = add_snakes(connections, args.snake_starts, args.snake_ends)
    network = connections_to_graph(args.nr_cells, args.nr_dice_sides, final_connections, net, sim)

    sim.run(args.nr_cells, plotting=False)

    # Choose function: find one path (computationally efficient) or find more paths (computationally inefficient; requires recursion)
    # dice_throws, log = get_shortest_path(sim, args.ladder_starts, args.ladder_ends, args.snake_starts, args.snake_ends)
    dice_throws, log = get_all_shortest_paths(sim, args.ladder_starts, args.ladder_ends, args.snake_starts, args.snake_ends)

    print("Dice throws:", dice_throws, end="\n\n")
    for info in log:
        print(info)

    # Example usage (using the board from my notebook):
    # python board_to_graph.py --nr_cells 9 --nr_dice_sides 4 --ladder_starts 2 --ladder_ends 6 --snake_starts 8 --snake_ends 3
    # python board_to_graph.py --nr_cells 20 --nr_dice_sides 2 --ladder_starts 2,9 --ladder_ends 12,19 --snake_starts 13 --snake_ends 8
    # python board_to_graph.py --nr_cells 100 --nr_dice_sides 6 --ladder_starts 1,4,8,21,28,50,71,80 --ladder_ends 38,14,20,42,76,67,92,99 --snake_starts 32,36,48,62,88,95,97 --snake_ends 10,6,26,18,24,56,78
    # python board_to_graph.py --nr_cells 6 --nr_dice_sides 2 --ladder_starts 2 --ladder_ends 4 --snake_starts 5 --snake_ends 1
