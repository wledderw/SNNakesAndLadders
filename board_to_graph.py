import argparse
from simsnn.core.networks import Network
from simsnn.core.simulators import Simulator


def make_base_connections(nr_cells, nr_dice_sides):
    connections = []
    for cell in range(1, nr_cells+1):
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
    for c in range(nr_cells):
        if c == 0:
            start_neuron = net.createInputTrain(train=[1, 0, 0, 0], loop=False, ID="B1")
            board_neurons.append(start_neuron)
            # sim.raster.addTarget(start_neuron)
        else:
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
        net.createSynapse(pre=board_neurons[start_neuron-1], post=board_neurons[post_neuron-1], ID=f"s{start_neuron}, p{post_neuron}, d{throw}", w=1, d=1)

        #Synapse between board neurons and read_out neurons, -2 because the starting cell does not need read-out neurons
        read_index = (post_neuron-2)*nr_dice_sides+(throw-1)
        print(post_neuron, nr_dice_sides, read_index)
        net.createSynapse(pre=board_neurons[start_neuron-1], post=read_neurons[read_index], ID=f"s{start_neuron}, p{post_neuron}, d{throw}", w=1, d=1)

        #Create read out neurons/synapses to check if a ladder/snake was used.
        if post_neuron-start_neuron != throw:
            #If ladder
            if post_neuron-start_neuron > throw:
                ladder_read_neuron = net.createLIF(ID=f"RL{post_neuron}-D{throw}", thr=nr_cells*nr_dice_sides+1, V_reset=0, m=1, V_init=nr_cells*nr_dice_sides)
                ladder_read_neurons.append(ladder_read_neuron)
                net.createSynapse(pre=board_neurons[start_neuron-1], post=ladder_read_neuron, ID=f"s{start_neuron}, p{post_neuron}, d{throw}", w=1, d=1)
            #If snake
            elif post_neuron-start_neuron < throw:
                snake_read_neuron = net.createLIF(ID=f"RS{post_neuron}-D{throw}", thr=nr_cells*nr_dice_sides+1, V_reset=0, m=1, V_init=nr_cells*nr_dice_sides)
                snake_read_neurons.append(snake_read_neuron)
                net.createSynapse(pre=board_neurons[start_neuron-1], post=snake_read_neuron, ID=f"s{start_neuron}, p{post_neuron}, d{throw}", w=1, d=1)
    
    sim.raster.addTarget(board_neurons)
    sim.raster.addTarget(read_neurons)
    sim.raster.addTarget(ladder_read_neurons)
    sim.raster.addTarget(snake_read_neurons)

def get_shortest_path(raster_data, ladder_starts, ladder_ends, snake_starts, snake_ends):
    print(raster_data)



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

    # Create the network and the simulator object
    net = Network()
    sim = Simulator(net)

    base_connections = make_base_connections(args.nr_cells, args.nr_dice_sides)
    connections = add_ladders(base_connections, args.ladder_starts, args.ladder_ends)
    final_connections = add_snakes(connections, args.snake_starts, args.snake_ends)
    print(final_connections)
    network = connections_to_graph(args.nr_cells, args.nr_dice_sides, final_connections, net , sim)

    sim.run(args.nr_cells, plotting=True)

    raster_data = sim.get_raster_data()
    get_shortest_path(raster_data, args.ladder_starts, args.ladder_ends, args.snake_starts, args.snake_ends)

    # Example usage (using the board from my notebook):
    # python board_to_graph.py --nr_cells 9 --nr_dice_sides 4 --ladder_starts 2 --ladder_ends 6 --snake_starts 8 --snake_ends 3