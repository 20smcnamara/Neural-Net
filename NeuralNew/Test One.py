import pygame
import random
import math
import time

pygame.init()
font = pygame.font.Font('freesansbold.ttf', 15)
display_size = 750
screen = pygame.display.set_mode([display_size, display_size])
pygame.display.set_caption("Testing")
base = display_size - 150
GRAVITY = 1.5


class Node:

    def __init__(self, friction, size, cords):
        self.friction = friction*2
        self.size = size*3
        self.threshold = size * friction / 100
        self.cords = cords
        self.mass = size
        self.touching_ground = False
        self.connectors = []
        self.connected_nodes = []
        self.applied_force = [0, 0]
        if friction <= .9:
            self.color = (250, 185, 255)
        elif friction >= 1.5:
            self.color = (255, 125, 175)
        else:
            self.color = (255, 102, 102)

    def update(self):
        self.touching_ground = (self.cords[1] + self.size) == base

    def move(self, adds):
        print(self.size, ":",  adds)
        xadd = adds[0]
        yadd = adds[1]
        if self.touching_ground and yadd < 0:
            yadd = 0
        friction = self.friction
        if not self.touching_ground:
            friction = 1
        self.cords = [self.cords[0]+xadd/(friction*self.mass), self.cords[1]+yadd/self.mass]
        if self.cords[1] + self.size >= base:
            self.cords[1] = base-self.size
            self.touching_ground = True

    def get_long(self, other_node):
        x_length = math.fabs(self.cords[0] - other_node.cords[0])
        y_length = math.fabs(self.cords[1] - other_node.cords[1])
        return (x_length ** 2 + y_length ** 2) ** .5

    def draw(self):
        pygame.draw.circle(screen, self.color, [int(self.cords[0]), int(self.cords[1])], self.size)

    def sum_forces(self, to):  # TODO Decide ridged or jelly joints (Please do ridged)
        if to.size != 0:
            boolean = True
            ratio = find_ratio(self.cords, to.cords)
            total = 0
            amount = 0
            for no in self.connected_nodes:
                if no.cords[1] < self:
                    total += find_angle(self, no)
                    amount += 1
            if amount > 0:
                total_force = [ratio[0][0] * ((self.size * GRAVITY) * find_angle(self, to)/(total/amount)),
                               ratio[0][1] * ((self.size * GRAVITY) * find_angle(self, to)/(total/amount))]
            else:
                total_force = [ratio[0][0] * ((self.size * GRAVITY) * find_angle(self, to)),
                               ratio[0][1] * ((self.size * GRAVITY) * find_angle(self, to))]
            for no in self.connected_nodes:
                if no.cords[1] > self.cords[1] and not no.touching_ground:
                    boolean = False
                    break
            if boolean:
                return total_force
        elif not self.touching_ground:
            total_force = [0, (self.size * GRAVITY)]
        else:
            total_force = [0, 0]
        force_on = [0, 0]
        for con in self.connectors:
            if con.nodes[0] != self:
                no = con.nodes[0]
                other = con.nodes[1]
            else:
                no = con.nodes[1]
                other = con.nodes[0]

            if no.cords[1] > self.cords[1] and not no.touching_ground:
                add = no.sum_forces(self)
                force_on[0] += add[0]
                force_on[1] += add[1]
            elif not self.touching_ground:
                add = no.sum_forces(self)
                other.add_force(add)

        applied_force = [self.applied_force[0] + force_on[0] + total_force[0],
                         self.applied_force[1] + force_on[1] + total_force[1]]
        return applied_force

    def apply_forces(self):
        if math.fabs(self.applied_force[0]) >= self.threshold or self.touching_ground:
            self.move(self.applied_force)
        else:
            self.move([0, self.applied_force[1]])
        self.applied_force = [0, 0]

    def add_force(self, adds):
        print(self.size, 1, self.applied_force)
        self.applied_force = [self.applied_force[0] + adds[0], self.applied_force[1] + adds[1]]
        print(self.size, 2, self.applied_force)


class Connector:

    def __init__(self, power, nodes, relaxing):
        self.power = power/2*3
        self.nodes = nodes
        self.warping = 1.0
        self.relaxing = relaxing
        self.last_time = 0
        self.minLength = nodes[0].get_long(nodes[1])
        self.touching = False
        nodes[0].connectors.append(self)
        nodes[1].connectors.append(self)

    def expand(self, sleep):
        step = time.time()
        if round(step) % sleep == 0 and round(step) != self.last_time:
            self.last_time = round(step)
            self.relaxing += 1
            if self.relaxing == 3:
                self.relaxing = 0
        if self.relaxing == 1:
            self.warping = .75
            ratio = find_ratio(self.nodes[0].cords, self.nodes[1].cords)
            self.nodes[0].add_force([-ratio[0][0] * self.power, -ratio[0][1] * self.power])
            self.nodes[1].add_force([ratio[1][0] * self.power, ratio[1][1] * self.power])
            self.touching = False
        elif self.relaxing == 0:
            self.relax()
        draw()

    def relax(self):
        if not self.touching:
            self.warping = 1
            ratio = find_ratio(self.nodes[0].cords, self.nodes[1].cords)
            multiply = 1
            self.nodes[0].add_force([ratio[0][0] * multiply * self.power, ratio[0][1] * self.power])
            self.nodes[1].add_force([-ratio[0][0] * multiply * self.power, ratio[0][1] * self.power])

    def draw(self):
        node1_thickness = int(self.nodes[0].size/5 * self.warping)
        node2_thickness = int(self.nodes[1].size/5 * self.warping)
        node1 = self.nodes[0].cords
        node2 = self.nodes[1].cords
        color = (75, 15, 15)
        if self.relaxing == 1:
            color = (15, 75, 15)
        if self.relaxing == 2:
            color = (15, 15, 15)
        pygame.draw.polygon(screen, color, ([node1[0], node1[1] + node1_thickness],
                                                   [node1[0], node1[1] - node1_thickness],
                                                   [node2[0], node2[1] - node2_thickness],
                                                   [node2[0], node2[1] + node2_thickness]))
        self.nodes[0].draw()
        self.nodes[1].draw()


class Organism:

    def __init__(self, nodes, connectors, sleep):
        self.connectors = connectors
        self.nodes = nodes
        self.last_time = -1
        self.sleep = sleep

    def control_forces(self):
        for n in self.nodes:
            n.sum_forces(blank_node)
            n.apply_forces()

    def take_action(self):
        for c in self.connectors:
            c.expand(self.sleep)

    def draw(self):
        for c in self.connectors:
            c.draw()


def find_ratio(cords1, cords2):
    wide = cords1[0] - cords2[0]
    high = cords1[1] - cords2[1]
    long = (wide**2 + high**2) ** .5
    if long == 0:
        return [[0, 0], [0, 0]]
    return [[wide/long, high/long], [wide/long, high/long]]


def find_angle(node1, node2):
    x = round(math.fabs(node1.cords[1] - node2.cords[1]))
    y = round(math.fabs(node1.cords[0] - node2.cords[0]))
    z = round((x**2 + y**2) ** .5)
    if x == 0:
        x = 1
    if z == 0:
        z = 1
    return math.acos((-y**2 + x**2 + z**2)/(2*x*z))


def draw_back():
    screen.fill((66, 194, 244))
    pygame.draw.rect(screen, (66, 244, 98), (0, base, display_size, display_size))


def draw():
    draw_back()
    for org in organisms:
        org.draw()
    pygame.display.update()


all_nodes = [Node(.75, 5, [display_size/2 - 100, display_size]),
             Node(1.6, 3, [display_size/2 + 100, display_size]),
             Node(1.6, 4, [display_size/2, display_size/2])]

all_connectors = [Connector(10, [all_nodes[0], all_nodes[1]], 0),  # Between the OG 2 has the most power
                  Connector(10, [all_nodes[1], all_nodes[2]], 0),  # Between the 1, and 2 has the middlest power
                  Connector(10, [all_nodes[0], all_nodes[2]], 0)]  # Between the 0, and 2 has the least power
running = True
blank_node = Node(0, 0, [0, 0])
init_time = time.time()
organisms = [Organism(all_nodes, all_connectors, 2)]
while running:
    moment = init_time - time.time()
    draw()
    for o in organisms:
        o.take_action()
        o.control_forces()
    print("Loop")
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            quit(0)
    time.sleep(.01)
