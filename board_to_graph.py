import argparse
from simsnn.core.networks import Network
from simsnn.core.simulators import Simulator
import numpy as np

def make_base_connections(nr_cells, nr_dice_sides):
    connections = []
    for cell in range(0, nr_cells+1):
        for throw in range(1, nr_dice_sides+1):
            if cell+throw <= nr_cells:
                connections.append((cell, cell+throw, throw))
    return connections

def add_ladders(connections, ladder_starts, ladder_ends):
    modified_connections = []
    for con in connections:
        if con[1] in ladder_starts:
            ind = ladder_starts.index(con[1])
            modified_connections.append((con[0], ladder_ends[ind], con[2]))
        elif not (con[0] in ladder_starts):
            modified_connections.append(con)
    return modified_connections

def add_snakes(connections, snake_starts, snake_ends):
    modified_connections = []
    for con in connections:
        if con[1] in snake_starts:
            ind = snake_starts.index(con[1])
            modified_connections.append((con[0], snake_ends[ind], con[2]))
        elif not (con[0] in snake_starts):
            modified_connections.append(con)

    return modified_connections

def connections_to_graph(nr_cells, nr_dice_sides, connections, net, sim):
    board_neurons = []
    read_neurons = []
    start_neuron = net.createInputTrain(train=[1], loop=False, ID="B0")
    board_neurons.append(start_neuron)
    for c in range(nr_cells):
        #Adding a neuron for each square on the board
        neuron = net.createLIF(ID=f"B{c+1}", thr=nr_cells*nr_dice_sides+1, V_reset=0, m=1, V_init=nr_cells*nr_dice_sides)
        board_neurons.append(neuron)
        for d in range(nr_dice_sides):
            #Adding read out neurons to track what throw was used to get there
            read_neuron = net.createLIF(ID=f"R{c+1}-D{d+1}", thr=nr_cells*nr_dice_sides+1, V_reset=0, m=1, V_init=nr_cells*nr_dice_sides)
            read_neurons.append(read_neuron)

    #adding synapses and ladder/snake neurons
    ladder_read_neurons = []
    snake_read_neurons = []
    for c in connections:
        (start_neuron, post_neuron, throw) = c
        #Synapse between board neurons
        net.createSynapse(pre=board_neurons[start_neuron], post=board_neurons[post_neuron], ID=f"s{start_neuron}, p{post_neuron}, d{throw}", w=1, d=1)

        #Synapse between board neurons and read_out neurons, -2 because the starting cell does not need read-out neurons
        read_index = (post_neuron-1)*nr_dice_sides+(throw-1)
        # print(post_neuron, nr_dice_sides, read_index)
        net.createSynapse(pre=board_neurons[start_neuron], post=read_neurons[read_index], ID=f"s{start_neuron}, p{post_neuron}, d{throw}", w=1, d=1)

        #Create read out neurons/synapses to check if a ladder/snake was used.
        if post_neuron-start_neuron != throw:
            #If ladder
            if post_neuron-start_neuron > throw:
                ladder_read_neuron = net.createLIF(ID=f"L{post_neuron}-D{throw}", thr=nr_cells*nr_dice_sides+1, V_reset=0, m=1, V_init=nr_cells*nr_dice_sides)
                ladder_read_neurons.append(ladder_read_neuron)
                net.createSynapse(pre=board_neurons[start_neuron], post=ladder_read_neuron, ID=f"s{start_neuron}, p{post_neuron}, d{throw}", w=1, d=1)
            #If snake
            elif post_neuron-start_neuron < throw:
                snake_read_neuron = net.createLIF(ID=f"S{post_neuron}-D{throw}", thr=nr_cells*nr_dice_sides+1, V_reset=0, m=1, V_init=nr_cells*nr_dice_sides)
                snake_read_neurons.append(snake_read_neuron)
                net.createSynapse(pre=board_neurons[start_neuron], post=snake_read_neuron, ID=f"s{start_neuron}, p{post_neuron}, d{throw}", w=1, d=1)
    
    sim.raster.addTarget(board_neurons)
    sim.raster.addTarget(read_neurons)
    sim.raster.addTarget(ladder_read_neurons)
    sim.raster.addTarget(snake_read_neurons)

def get_shortest_path(sim, ladder_starts, ladder_ends, snake_starts, snake_ends):
    # Get raster and label data:
    raster = np.array(sim.get_raster_data()).T
    labels = sim.raster.get_labels()
    print(labels)

    # Make a list of nodes and a dictionary of nodes with their edges:
    nodes = [int(nr[1:]) for nr in labels if nr[0] == 'B']
    edges = dict()
    for node in nodes:
        edges[node] = [edge for edge in labels if edge.split('-')[0][0] != 'B' and int(edge.split('-')[0][1:]) == node]

    # Find final node:
    final_node = max(nodes)
    print(final_node)
    # Find final timestep:
    t = np.where(raster[final_node])[0][0]

    # Initialize the list of dice throws:
    dice_throws = []
    log = [f"You reached the finish by reaching final space {final_node}."]

    # Backtrack the spiked neurons:
    node = final_node
    while node != 0 and t >= 0:  # Backtrack back until the start of simulation
        print("test")
        print(node)
        node_edges = edges[node]  # Get the edges of this node
        print(node_edges)
        diff = 0

        # We want to get an edge that got to this node, but there should be
        # priority for snakes and ladders:
        node_edge = ""
        for potential_node_edge in node_edges:
            row = labels.index(potential_node_edge)
            if raster[row, t] and node_edge == "":
                node_edge = potential_node_edge
            elif raster[row, t] and potential_node_edge[0] == 'S':
                node_edge = potential_node_edge
            elif raster[row, t] and potential_node_edge[0] == 'L':
                node_edge = potential_node_edge

        # If this node is a ladder end:
        
        print(node_edge[0])
        if node_edge[0] == 'L':
            end = node
            start = ladder_starts[ladder_ends.index(end)]
            diff = end - start  # Extra moves because of ladder
            log.append(f"Now, you are on {start}, from where you can take a ladder.")

        # If this node is a snake start:
        if node_edge[0] == 'S':
            # if node in snake_starts:
            start = node
            end = snake_starts[snake_ends.index(start)]
            diff = start - end  # Extra (negative) moves because of snake
            log.append(f"Now, you are on {end}, from where you have to take a snake.")

        # Get dice throw and add to history list:
        dice = int(node_edge.split('-')[1][1:])
        dice_throws.append(dice)
        print("dice: " + str(dice))
        # Go to new node and new timestep:
        node -= (diff + dice)
        t -= 1

        log.append(f"You throw a {dice}.")
        if node != 0:
            log.append(f"You are now on space {node}.")
        else:
            log.append("You start on space 0.")


    return dice_throws[::-1], log[::-1]#.append("You reached the goal!")


if __name__ == "__main__":
    def list_of_ints(arg):
        return list(map(int, arg.split(',')))

    parser = argparse.ArgumentParser()
    parser.add_argument('--nr_cells', type=int, default=9)
    parser.add_argument('--nr_dice_sides', type=int, default=4)
    parser.add_argument('--snake_starts', type=list_of_ints, default=[8])
    parser.add_argument('--snake_ends', type=list_of_ints, default=[3])
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

    sim.run(args.nr_cells, plotting=True)

    dice_throws, log = get_shortest_path(sim, args.ladder_starts, args.ladder_ends, args.snake_starts, args.snake_ends)
    print("Dice throws:", dice_throws, end="\n\n")
    for info in log:
        print(info)

    # Example usage (using the board from my notebook):
    # python board_to_graph.py --nr_cells 9 --nr_dice_sides 4 --ladder_starts 2 --ladder_ends 6 --snake_starts 8 --snake_ends 3
    # python board_to_graph.py --nr_cells 20 --nr_dice_sides 2 --ladder_starts 2,9 --ladder_ends 12,19 --snake_starts 13 --snake_ends 8
    # python board_to_graph.py --nr_cells 100 --nr_dice_sides 6 --ladder_starts 1,4,8,21,28,50,71,80 --ladder_ends 38,14,20,42,76,67,92,99 --snake_starts 32,36,48,62,88,95,97 --snake_ends 10,6,26,18,24,56,78