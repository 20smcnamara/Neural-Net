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

    def __init__(self, friction, size, threshold, cords):
        self.friction = friction*2
        self.size = size*5
        self.threshold = threshold
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
        xadd = adds[0]
        yadd = adds[1]
        if self.touching_ground and yadd < 0:
            yadd = 0
        self.cords = [self.cords[0]+xadd/(self.friction*self.mass), self.cords[1]+yadd/self.mass]
        if self.cords[1] + self.size >= base:
            self.cords[1] = base-self.size
            self.touching_ground = True

    def get_long(self, other_node):
        x_length = math.fabs(self.cords[0] - other_node.cords[0])
        y_length = math.fabs(self.cords[1] - other_node.cords[1])
        return (x_length ** 2 + y_length ** 2) ** .5

    def draw(self):
        pygame.draw.circle(screen, self.color, [int(self.cords[0]), int(self.cords[1])], self.size)

    def fek_gravity(self, to):
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
            else:
                no = con.nodes[1]
            if no.cords[1] > self.cords[1] and not no.touching_ground:
                add = no.fek_gravity(self)
                force_on[0] += add[0]
                force_on[1] += add[1]
                print(no.cords[1], self.cords[1])
        self.applied_force = [force_on[0] + total_force[0], force_on[1] + total_force[1]]
        return self.applied_force

    def apply_forces(self):
        self.move(self.applied_force)


class Connector:

    def __init__(self, power, nodes):
        self.power = power * 5
        self.nodes = nodes
        self.warping = 1.0
        self.relaxing = False
        self.last_time = 0
        self.minLength = nodes[0].get_long(nodes[1])
        nodes[0].connectors.append(self)
        nodes[1].connectors.append(self)

    def expand(self, sleep, step):
        if round(step) % sleep == 0 and round(step) != self.last_time:
            self.last_time = round(step)
            self.relaxing = not self.relaxing
        if not self.relaxing:
            self.warping = .75
            ratio = find_ratio(self.nodes[0].cords, self.nodes[1].cords)
            # self.nodes[0].move([ratio[0][1] * self.power, -ratio[0][1] * self.power])
            # self.nodes[1].move([-ratio[1][1] * self.power, -ratio[1][1] * self.power])
            self.nodes[0].applied_force[0] += ratio[0][1] * self.power
            self.nodes[0].applied_force[1] += -ratio[0][1] * self.power
            self.nodes[1].applied_force[0] += -ratio[1][1] * self.power
            self.nodes[0].applied_force[1] += -ratio[1][1] * self.power

        else:
            self.relax()
        draw()

    def relax(self):
        self.warping = 1
        ratio = find_ratio(self.nodes[0].cords, self.nodes[1].cords)
        multiply = 1
        if self.nodes[0].cords[0] < self.nodes[1].cords[0]:
            multiply = -1
        # self.nodes[0].move([ratio[0][1] * multiply * self.power, ratio[0][1] * self.power])
        # self.nodes[1].move([ratio[1][1] * multiply * self.power, ratio[1][1] * self.power])
        self.nodes[0].applied_force[0] += ratio[0][1] * self.power * multiply
        self.nodes[0].applied_force[1] += -ratio[0][1] * self.power
        self.nodes[1].applied_force[0] += -ratio[1][1] * self.power * multiply
        self.nodes[1].applied_force[1] += -ratio[1][1] * self.power

    def draw(self):
        node1_thickness = int(self.nodes[0].size/5 * self.warping)
        node2_thickness = int(self.nodes[1].size/5 * self.warping)
        node1 = self.nodes[0].cords
        node2 = self.nodes[1].cords
        pygame.draw.polygon(screen, (75, 75, 75), ([node1[0], node1[1] + node1_thickness],
                                                   [node1[0], node1[1] - node1_thickness],
                                                   [node2[0], node2[1] - node2_thickness],
                                                   [node2[0], node2[1] + node2_thickness]))
        self.nodes[0].draw()
        self.nodes[1].draw()


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
    c.draw()
    pygame.display.update()


all_nodes = [Node(.75, 5, 10, [display_size/2 + 60, display_size]),
             Node(1.6, 3, 10, [display_size/2, display_size])]

c = Connector(50, [all_nodes[0], all_nodes[1]])
running = True
blank = Node(0, 0, 0, [0, 0])
while running:
    moment = time.time()
    draw()
    c.expand(3, moment)
    for n in all_nodes:
        n.fek_gravity(blank)
        n.apply_forces()
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            quit(0)
    time.sleep(.1)
