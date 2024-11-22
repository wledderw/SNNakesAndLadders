import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import networkx as nx
from simsnn.core.detectors import Raster, Multimeter


class Simulator:
    """Simulator

    Parameters
    ----------
    network : Network
        Network to simulate
    detectors : List
        List of detectors
    """

    def __init__(self, network, seed=None):
        self.network = network
        self.multimeter = Multimeter()
        self.raster = Raster()
        if seed != None:
            self.network.update_rng(np.random.RandomState(seed))

    def run(self, steps, plotting=False, options=None):
        """Run the simulator

        Parameters
        ----------
        steps : int
            Number of steps to simulate
        """
        options = {} if options is None else options
        self.raster.initialize(steps)
        self.multimeter.initialize(steps)

        for _ in range(steps):
            self.network.step()
            self.raster.step()
            self.multimeter.step()

        if plotting:
            self.print_detectors(steps, options)

    def to_inet_string(self):
        inet_str = ""
        inet_str += self.raster.to_inet_string() + "\n\n"
        inet_str += self.multimeter.to_inet_string() + "\n\n"
        return inet_str

    def print_detectors(self, steps, options):
        rasterdata = self.raster.get_measurements()
        print("Rasterdata:")
        print(rasterdata.T)
        multimeterdata = self.multimeter.get_measurements()
        print("\nMultimeterdata:")
        print(multimeterdata.T)

        graph = options.get("graph", True)
        ntd = len(rasterdata.T)
        nvd = len(multimeterdata.T)

        ntd_pos = 1 if graph else 0
        nvd_offset = ntd_pos
        nvd_offset += 1 if ntd else 0

        fig, _ = plt.subplots(
            constrained_layout=True, nrows=nvd_offset + nvd, figsize=(14, 8)
        )

        options = {
            "with_labels": True,
            "node_color": "white",
            "edgecolors": "blue",
            "ax": fig.axes[0],
            "node_size": 1100,
            "pos": nx.circular_layout(self.network.graph),
        }
        if graph:
            nx.draw_networkx(self.network.graph, **options)

        if ntd:
            fig.axes[ntd_pos].matshow(rasterdata.T, cmap="gray", aspect="auto")
            fig.axes[ntd_pos].set_xticks(np.arange(-0.5, steps, 1), minor=True)
            fig.axes[ntd_pos].grid(
                which="minor", color="gray", linestyle="-", linewidth=2
            )
            fig.axes[ntd_pos].set_yticks(np.arange(-0.5, ntd, 1), minor=True)
            fig.axes[ntd_pos].xaxis.set_major_locator(ticker.MultipleLocator(1))
            fig.axes[ntd_pos].set_yticks(np.arange(0, ntd, 1))
            fig.axes[ntd_pos].set_yticklabels([t.ID for t in self.raster.targets])

        for i in range(nvd):
            fig.axes[i + nvd_offset].plot(multimeterdata[:, i])
            fig.axes[i + nvd_offset].set_ylim(top=(max(multimeterdata.T[i]) + 0.5))
            fig.axes[i + nvd_offset].set_ylabel(self.multimeter.targets[i].ID)
            fig.axes[i + nvd_offset].grid(which="major")
            fig.axes[i + nvd_offset].xaxis.set_major_locator(ticker.MultipleLocator(1))

        plt.show()
