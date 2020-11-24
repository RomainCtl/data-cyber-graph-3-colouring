from enum import IntEnum
from secrets import token_bytes
import numpy as np
import random
import hashlib


class COLOR(IntEnum):
    RED = 1
    GREEN = 2
    BLUE = 3

    @staticmethod
    def values():
        """Get the list of the colors as int

        Returns:
            list: list of int
        """
        return list(map(int, COLOR))

    @property
    def firstletter(self):
        """Get the first letter of the color

        Returns:
            string: first letter
        """
        return self.name[:1]


class Graph3Colouring:
    def __init__(self, size: int = 20):
        self.size = size
        self.choose_colors()
        self.generate()

    def choose_colors(self):
        """Choose the colours randomly for the nodes in the graph.
        """
        self.colors = [random.choice(COLOR.values()) for _ in range(self.size)]

    def generate(self):
        """Randomly generate an adjacent matrix.
        """
        self.matrix = np.zeros((self.size, self.size))
        for i in range(self.size):
            for j in range(i):
                if self.colors[i] != self.colors[j]:
                    r = random.randint(0, 1)
                    self.matrix[i, j] = r
                    self.matrix[j, i] = r

    def __repr__(self):
        """Generate string matrix representation

        Returns:
            string: Matrix representation
        """
        string = "  " + " ".join(
            map(lambda clr: COLOR(clr).firstletter, self.colors)
        ) + '\n'
        for i in range(self.size):
            string += COLOR(self.colors[i]).firstletter + ' '
            for j in range(self.size):
                if self.matrix[i, j] == 0:
                    string += '  '
                else:
                    string += 'x '
            string += '\n'
        return string


def h(color: COLOR, rand_bytes: bytes):
    """Hash function (using sha512)

    Args:
        color (COLOR): the color object
        rand_bytes (bytes): random bytes (128)

    Returns:
        str: return the digest
    """
    return hashlib.sha512(color.name.encode('utf-8') + rand_bytes).digest()


def pledging_colouring(colors: list, rand: list):
    """Produces a table of pledged values

    Args:
        colors (list): list of colors
        rand (list): list of random values (128 bits)

    Returns:
        list: the product table containing the pledged values.
    """
    return list(map(
        lambda c: h(c[0], c[1]),
        zip(colors, rand)
    ))


def proof_of_colouring(pledged_colors: list, i: int, j: int, ri: int, ci: int, rj: int, cj: int):
    """[summary]

    Args:
        pledged_colors (list): table of pledged values (colors)
        i (int): node i
        j (int): node j
        ri (int): random value of the i th node
        ci (int): the colour of the i th node
        rj (int): random value of the j th node
        cj (int): the colour of the j th node

    Returns:
        boolean: return True if the two colours are different and h(ri || ci) = yi and h(rj || cj) = yj with 'h' the hash function
    """
    return h(ci, ri) == pledged_colors[i] and h(cj, rj) == pledged_colors[j] and ci != cj


class User:
    def __init__(self, graph: np.array):
        self.graph = graph

    def send_pledging_colouring(self, checker):
        """Send pledging colouring to the checker

        Args:
            checker (Checker): the Checker
        """
        # Permute the colours
        perm = np.random.permutation(COLOR.values())

        # Permute the colours of the nodes
        self.permuted_colors = [
            COLOR(perm[color-1]) for color in self.graph.colors
        ]

        # Generates 128 bits randomly for each node
        self.rand_bytes_array = [
            token_bytes(128) for _ in range(self.graph.size)
        ]

        # Send the pledge
        checker.pledging = pledging_colouring(
            self.permuted_colors,
            self.rand_bytes_array,
        )

    def send_colors(self, checker, i: int, j: int):
        """Send the permuted colors and the generated random 128 bytes for i th and j th nodes to the checker

        Args:
            checker (Checker): the Checker
            i (int): i th node
            j (int): j th node
        """
        checker.colors = (
            self.rand_bytes_array[i],
            self.permuted_colors[i],
            self.rand_bytes_array[j],
            self.permuted_colors[j],
        )


class Checker:
    def __init__(self, graph: np.array):
        self.graph = graph
        self.pledging = None
        self.colors = None
        self.results = dict(
            success=0,
            failures=0
        )

    def choose_nodes(self):
        """Choose two nodes who are connected by an edge

        Returns:
            i, j: the two randomly selected nodes
        """
        row, col = self.graph.matrix.nonzero()
        r = random.randint(0, row.shape[0]) - 1
        return row[r], col[r]

    def check_pledging(self, i: int, j: int):
        """Check pledging and store the result

        Args:
            i (int): node i
            j (int): node j
        """
        if proof_of_colouring(self.pledging, i, j, *self.colors):
            self.results["success"] += 1
        else:
            self.results["failures"] += 1


if __name__ == "__main__":
    g = Graph3Colouring(20)
    print(repr(g))

    user = User(g)
    checker = Checker(g)

    for i in range(400):
        # User sends a pledge of a colouring to a verifier
        user.send_pledging_colouring(checker)

        # The verifier asks to see the colours of two nodes i and j which are connected by an edge
        a, b = checker.choose_nodes()

        # The user sends the (ri; ci) and (rj; cj) that correspond to these two nodes.
        user.send_colors(checker, a, b)

        # The checker check the data
        checker.check_pledging(a, b)

    print(checker.results)
