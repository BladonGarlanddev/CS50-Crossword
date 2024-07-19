import sys

from crossword import *


class CrosswordCreator():

    def __init__(self, crossword):
        """
        Create new CSP crossword generate.
        """
        self.crossword = crossword
        self.domains = {
            var: self.crossword.words.copy()
            for var in self.crossword.variables
        }

    def letter_grid(self, assignment):
        """
        Return 2D array representing a given assignment.
        """
        letters = [
            [None for _ in range(self.crossword.width)]
            for _ in range(self.crossword.height)
        ]
        for variable, word in assignment.items():
            direction = variable.direction
            for k in range(len(word)):
                i = variable.i + (k if direction == Variable.VERTICAL else 0)
                j = variable.j + (k if direction == Variable.HORIZONTAL else 0)
                letters[i][j] = word[k]
        return letters

    def print(self, assignment):
        """
        Print crossword assignment to the terminal.
        """
        letters = self.letter_grid(assignment)
        for i in range(self.crossword.height):
            for j in range(self.crossword.width):
                if self.crossword.structure[i][j]:
                    print(letters[i][j] or " ", end="")
                else:
                    print("█", end="")
            print()

    def save(self, assignment, filename):
        """
        Save crossword assignment to an image file.
        """
        from PIL import Image, ImageDraw, ImageFont
        cell_size = 100
        cell_border = 2
        interior_size = cell_size - 2 * cell_border
        letters = self.letter_grid(assignment)

        # Create a blank canvas
        img = Image.new(
            "RGBA",
            (self.crossword.width * cell_size,
             self.crossword.height * cell_size),
            "black"
        )
        font = ImageFont.truetype("assets/fonts/OpenSans-Regular.ttf", 80)
        draw = ImageDraw.Draw(img)

        for i in range(self.crossword.height):
            for j in range(self.crossword.width):

                rect = [
                    (j * cell_size + cell_border,
                     i * cell_size + cell_border),
                    ((j + 1) * cell_size - cell_border,
                     (i + 1) * cell_size - cell_border)
                ]
                if self.crossword.structure[i][j]:
                    draw.rectangle(rect, fill="white")
                    if letters[i][j]:
                        _, _, w, h = draw.textbbox((0, 0), letters[i][j], font=font)
                        draw.text(
                            (rect[0][0] + ((interior_size - w) / 2),
                             rect[0][1] + ((interior_size - h) / 2) - 10),
                            letters[i][j], fill="black", font=font
                        )

        img.save(filename)

    def solve(self):
        """
        Enforce node and arc consistency, and then solve the CSP.
        """
        self.enforce_node_consistency()
        print("Node consistency ensured")
        self.ac3()
        print("Arc consistency ensured")
        return self.backtrack(dict())

    def enforce_node_consistency(self):
        """
        Update `self.domains` such that each variable is node-consistent.
        (Remove any values that are inconsistent with a variable's unary
         constraints; in this case, the length of the word.)
        """
        # print(f"Domains: {self.domains}")

        for variable, domain in self.domains.items():

            # sets cannot change size during iteration so create a set to hold all values that must be removed
            to_remove = set()
            for word in domain:

                # the expected variable length must match the length of the word of focus
                if variable.length != len(word):
                    to_remove.add(word)
            domain.difference_update(to_remove)

        # print(f"Domains: {self.domains}")

    def revise(self, x, y):
        """
        Make variable `x` arc consistent with variable `y`.
        To do so, remove values from `self.domains[x]` for which there is no
        possible corresponding value for `y` in `self.domains[y]`.

        Return True if a revision was made to the domain of `x`; return
        False if no revision was made.
        """

        print(f"running script for var x: {x}, var y: {y}")

        domains = self.domains
        overlap = self.crossword.overlaps[x, y]
        x_consistent_words = set()
        y_consistent_words = set()

        delta_x = overlap[1] - x.j + overlap[0] - x.i
        delta_y = overlap[1] - y.j + overlap[0] - y.i
        print(f"Length of x domain: {len(domains[x])}")
        print(f"Length of y domain: {len(domains[y])}")

        for x_word in domains[x]:
            x_letter = x_word[delta_x]
            for y_word in domains[y]:
                if y_word == x_word:
                    continue
                y_letter = y_word[delta_y]
                if x_letter == y_letter:
                    print(f"Found matching words: ({x_word}, {y_word})")
                    x_consistent_words.add(x_word)
                    y_consistent_words.add(y_word)

            print("\n")

        domains[x] = x_consistent_words
        domains[y] = y_consistent_words
        print(f"Updated domain: {domains[x]} \n")

    def ac3(self, arcs=None):
        """
        Update `self.domains` such that each variable is arc consistent.
        If `arcs` is None, begin with initial list of all arcs in the problem.
        Otherwise, use `arcs` as the initial list of arcs to make consistent.

        Return True if arc consistency is enforced and no domains are empty;
        return False if one or more domains end up empty.
        """

        arcs = [(x, y) for x in self.crossword.variables for y in self.crossword.neighbors(x)]

        checked_arcs = set()
        while arcs:
            (x, y) = arcs.pop()
            if (x, y) not in checked_arcs and (y, x) not in checked_arcs:
                checked_arcs.add((x, y))
                if self.revise(x, y):
                    if len(self.domains(x)) == 0:
                        return False

        return True 

        print(f"arcs: {arcs}")
        """
        variables = self.crossword.variables

        for variable in variables:
            for neighbor in self.crossword.neighbors(variable):
                overlap = self.crossword.overlaps[variable, neighbor]
                if overlap is not None:
                    self.revise(variable, neighbor, overlap)
        """

    def assignment_complete(self, assignment):
        """
        Return True if `assignment` is complete (i.e., assigns a value to each
        crossword variable); return False otherwise.
        """
        for value in assignment:
            if not value:
                return False

    def consistent(self, assignment, var):
        """
        Return True if `assignment` is consistent (i.e., words fit in crossword
        puzzle without conflicting characters); return False otherwise.
        """    

        print(f"\nassignment: {assignment}")

        overlaps = self.crossword.overlaps
        domains = self.domains

        x = var
        x_word = assignment[x]

        print(f"main var: {x}")

        for keys, overlap in overlaps.items():
            x_index = None
            if not x in keys or overlap == None:
                print(f"Skipped vars: {keys}")
                continue

            print(f"keys: ({keys}), overlap: {overlap}")

            x_index = keys.index(x)
            y_index = abs(x_index - 1)

            y = keys[y_index]

            delta_x = overlap[1] - x.j + overlap[0] - x.i
            delta_y = overlap[1] - y.j + overlap[0] - y.i

            y_word = assignment.get(y, None) 

            if not y_word:
                continue

            if y_word == x_word:
                return False

            if not y_word[delta_y] == x_word[delta_x]: return False

        return True

    def order_domain_values(self, var, assignment):
        """
        Return a list of values in the domain of `var`, in order by
        the number of values they rule out for neighboring variables.
        The first value in the list, for example, should be the one
        that rules out the fewest values among the neighbors of `var`.
        """

        domains = self.domains
        overlaps = {overlap for overlap in self.crossword.overlaps if var in overlap}
        consistent_words = set()
        ranked_values = {}

        for x_word in domains[var]:

            print(f"domains[x]: {domains[x]}")
            print(f"x direction: {x.direction}, x: ({x.i}, {x.j})")

            if x.direction == Variable.HORIZONTAL:
                print(f"overlap[0]: {overlap[0]}")
                delta_x = overlap[1] - x.j
            else:
                delta_x = overlap[0] - x.i

            print(f"delta: {delta_x}, overlap: {overlap}")

            x_letter = x_word[delta_x]

            print(f"x_word: {x_word}, x_letter: {x_letter}, delta: {delta_x}")

            for variable in overlaps:
                if variable == var:
                    continue

                for y_word in variable:
                    if y_word == x_word:
                        continue

                    print(f"y direction: {y.direction}, y: ({y.i}, {y.j})")
                    if y.direction == Variable.VERTICAL:
                        print(f"overlap[0]: {overlap[0]}, y.j: {y.j}")
                        delta_y = overlap[0] - y.i
                    else:
                        print(f"overlap[1]: {overlap[1]}, y.i: {y.i}")
                        delta_y = overlap[1] - y.j

                    y_letter = y_word[delta_y]

                    print(f"y_word: {y_word}, y_letter: {y_letter}, delta: {delta_y}")
                    if x_letter == y_letter:
                        print(f"Found matching words: ({x_word}, {y_word})")
                        consistent_words.add(x_word) 
                print("\n")

            ranked_values[x_word] = len(consistent_words)

        ranked_values = {key: value for key, value in sorted(ranked_values.items(), key=lambda item: item[1])}

        return ranked_values

    def select_unassigned_variable(self, assignment):
        """
        Return an unassigned variable not already part of `assignment`.
        Choose the variable with the minimum number of remaining values
        in its domain. If there is a tie, choose the variable with the highest
        degree. If there is a tie, any of the tied variables are acceptable
        return values.
        """

        variables = self.crossword.variables
        domains = self.domains
        fewest_values = float('inf')
        selected_var = set()
        unassigned_variables = [variable for variable in variables if not (variable in assignment)]

        for variable in unassigned_variables:
            n_domains = len(domains[variable])
            # print(f"n_domains: {n_domains}")
            if n_domains < fewest_values:
                # print(f"Selected variable with lower domain value")
                fewest_values = n_domains
                selected_var = {variable}
            elif n_domains == fewest_values:
                # print(f"Equal value domain found")
                selected_var.add(variable)

        # print()
        # print(f"Fewest val vars: {selected_var}")

        if len(selected_var) > 1:
            highest_degree = 0
            highest_degree_vars = set()
            overlaps = self.crossword.overlaps
            for var in selected_var:
                degree = sum(1 for overlap_var in overlaps if var in overlap_var)

                if degree > highest_degree:
                    highest_degree = degree
                    highest_degree_vars = {var}
                elif degree == highest_degree:
                    highest_degree_vars.add(var)

            return highest_degree_vars.pop()

        elif len(selected_var) == 1:
            return selected_var.pop()

        return None

    def backtrack(self, assignment):
        """
        Using Backtracking Search, take as input a partial assignment for the
        crossword and return a complete assignment if possible to do so.

        `assignment` is a mapping from variables (keys) to words (values).

        If no assignment is possible, return None.
        """

        print(f"assignment: {assignment}")

        variables = self.crossword.variables
        domains = self.domains

        if len(assignment) == len(variables):
            print(f"Finished !!!!!!!!!!!!!!!!")
            return True

        assigned = False
        variable = self.select_unassigned_variable(assignment)
        for word in domains[variable]:
            copy = assignment.copy()
            copy[variable] = word
            if self.consistent(copy, variable):
                assignment[variable] = word
                result = self.backtrack(assignment)
                if result:
                    return assignment
        word = assignment.popitem()
        print(f"\n word: {word} was not consistent")
        return False


def main():

    # Check usage
    if len(sys.argv) not in [3, 4]:
        sys.exit("Usage: python generate.py structure words [output]")

    print("Program running")

    # Parse command-line arguments
    structure = sys.argv[1]
    words = sys.argv[2]
    output = sys.argv[3] if len(sys.argv) == 4 else None

    # Generate crossword
    crossword = Crossword(structure, words)
    creator = CrosswordCreator(crossword)
    assignment = creator.solve()

    # Print result
    if assignment is None:
        print("No solution.")
    else:
        creator.print(assignment)
        if output:
            creator.save(assignment, output)


if __name__ == "__main__":
    main()
