from simsnn.core.networks import Network
from simsnn.core.simulators import Simulator

print("test")

def run(duration=10, options=None):
    options = {} if options is None else options

    # Create the network and the simulator object
    net = Network()
    sim = Simulator(net)

    # Create a programmed neuron, that spikes on times 1 and 3,
    # does not repeat it's programming and has the ID "pn".
    start_neuron = net.createInputTrain(train=[1, 0, 0, 0], loop=False, ID="1")

    # Create a LIF neuron, with a membrane voltage threshold of 1,
    # a post spike reset value of 0 and no voltage decay (m=1).
    neuron_2 = net.createLIF(ID="2", thr=1, V_reset=0, m=1)
    neuron_3 = net.createLIF(ID="3", thr=1, V_reset=0, m=1)
    neuron_4 = net.createLIF(ID="4", thr=1, V_reset=0, m=1)
    neuron_5 = net.createLIF(ID="5", thr=1, V_reset=0, m=1)
    neuron_6 = net.createLIF(ID="6", thr=1, V_reset=0, m=1)
    neuron_7 = net.createLIF(ID="7", thr=1, V_reset=0, m=1)
    neuron_8 = net.createLIF(ID="8", thr=1, V_reset=0, m=1)
    end_neuron = net.createLIF(ID="9", thr=1, V_reset=0, m=1)

    # Create a Synapse, between the programmed neuron and the LIF neuron,
    # with a voltage weight of 1 and a delay of 1.
    # net.createSynapse(pre=start_neuron, post=end_neuron, ID="pn-ln", w=1, d=1)
    net.createSynapse(pre=start_neuron, post=neuron_6, ID="pn-ln", w=1, d=1)
    net.createSynapse(pre=start_neuron, post=neuron_3, ID="pn-ln", w=1, d=1)
    net.createSynapse(pre=start_neuron, post=neuron_4, ID="pn-ln", w=1, d=1)
    net.createSynapse(pre=neuron_3, post=neuron_4, ID="pn-ln", w=1, d=1)
    net.createSynapse(pre=neuron_3, post=neuron_5, ID="pn-ln", w=1, d=1)
    net.createSynapse(pre=neuron_3, post=neuron_6, ID="pn-ln", w=1, d=1)
    net.createSynapse(pre=neuron_3, post=neuron_7, ID="pn-ln", w=1, d=1)
    net.createSynapse(pre=neuron_4, post=neuron_5, ID="pn-ln", w=1, d=1)
    net.createSynapse(pre=neuron_4, post=neuron_6, ID="pn-ln", w=1, d=1)
    net.createSynapse(pre=neuron_4, post=neuron_7, ID="pn-ln", w=1, d=1)
    net.createSynapse(pre=neuron_4, post=neuron_3, ID="pn-ln", w=1, d=1)
    net.createSynapse(pre=neuron_5, post=neuron_6, ID="pn-ln", w=1, d=1)
    net.createSynapse(pre=neuron_5, post=neuron_7, ID="pn-ln", w=1, d=1)
    net.createSynapse(pre=neuron_5, post=neuron_3, ID="pn-ln", w=1, d=1)
    net.createSynapse(pre=neuron_5, post=end_neuron, ID="pn-ln", w=1, d=1)
    net.createSynapse(pre=neuron_6, post=end_neuron, ID="pn-ln", w=1, d=1)
    net.createSynapse(pre=neuron_6, post=neuron_7, ID="pn-ln", w=1, d=1)
    net.createSynapse(pre=neuron_6, post=neuron_3, ID="pn-ln", w=1, d=1)
    net.createSynapse(pre=neuron_7, post=neuron_3, ID="pn-ln", w=1, d=1)
    net.createSynapse(pre=neuron_7, post=end_neuron, ID="pn-ln", w=1, d=1)



    # Add all neurons to the raster
    sim.raster.addTarget([start_neuron, neuron_2, neuron_3, neuron_4, neuron_5, neuron_6, neuron_7, neuron_8, end_neuron,])
    # Add all neurons to the multimeter
    sim.multimeter.addTarget([start_neuron])

    # Run the simulation for 10 rounds, enable the plotting of the raster,
    # the multimeter and the network structure.
    sim.run(duration, plotting=True, options=options)

run()