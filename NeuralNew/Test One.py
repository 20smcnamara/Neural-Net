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
ground = pygame.Rect((0, base, display_size, display_size - base))
GRAVITY = 1.2


class Circle(pygame.sprite.Sprite):

    def __init__(self, color, radius, cords):
        self.radius = radius
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.Surface((radius, radius))
        self.image.fill((255, 255, 255))
        self.color = color
        self.cords = cords
        self.len_rect = math.sqrt(2 * (self.radius ** 2))
        self.rect = pygame.Rect((cords[0] - self.len_rect / 2,
                                 cords[1] - self.len_rect / 2,
                                 self.len_rect,
                                 self.len_rect))
        self.rect.center = (cords[0], cords[1])
        self.dx = 5
        self.dy = 5

    def draw(self):
        pygame.draw.circle(screen, self.color, self.cords, self.radius)

    def move_to(self, cords):
        self.cords = cords
        self.len_rect = math.sqrt(2 * (self.radius ** 2))
        self.rect = pygame.Rect((cords[0] - self.len_rect / 2,
                                 cords[1] - self.len_rect / 2,
                                 self.len_rect,
                                 self.len_rect))

    def is_touching_object(self, other):
        return other.Rect.collidepoint(self.rect)


class Node:

    def __init__(self, friction, size, cords):
        self.friction = friction
        self.size = size*3
        self.threshold = size * friction / 10
        self.cords = cords
        self.mass = size
        self.touching_ground = False
        self.connectors = []
        self.connected_nodes = []
        self.applied_force = [0, 0]
        self.velocity = [0, 0]
        self.color = (255, (203 - 135 * friction) * 1.88, (203 - 135 * friction) * 1.88)  # Look at the magic #'s
        if friction > 1.5:
            self.color = (255, 0, 0)
        if friction < 0.5:
            self.color = (255, 230, 230)
        self.circle = Circle(self.color, self.size * 5, cords)

    def update(self):
        self.touching_ground = (self.cords[1] + self.size) == base
        self.update_cords()

    def update_cords(self):
        self.circle.move_to(self.cords)

    def move(self, adds):
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
        self.update_cords()

    def get_long(self, other_node):
        x_length = math.fabs(self.cords[0] - other_node.cords[0])
        y_length = math.fabs(self.cords[1] - other_node.cords[1])
        return (x_length ** 2 + y_length ** 2) ** .5

    def draw(self):
        pygame.draw.circle(screen, self.color, [int(self.cords[0]), int(self.cords[1])], self.size)

    def sum_forces(self, calculated):
        total_forces = [0, 0]
        if self in calculated:
            return [0, 0]
        for n in self.connected_nodes:
            adds = n.sum_forces()
            if not n.touching_ground:
                if n.cords[1] == self.cords[1]:
                    total_forces = [total_forces[0], total_forces[1] - adds[1]]
                elif n.cords[1] > self.cords[1]:
                    total_forces = [total_forces[0] + adds[1], total_forces[1] + adds[1]]
                else:
                    total_forces = [total_forces[0] + adds[1], total_forces[1] - adds[1]]
            else:
                if n.cords[1] == self.cords[1]:
                    total_forces = [total_forces[0], total_forces[1] - adds[1]]
                elif n.cords[1] > self.cords[1]:
                    total_forces = [total_forces[0] - adds[1], total_forces[1] + adds[1]]
                else:
                    total_forces = [total_forces[0] + adds[1], total_forces[1] + adds[1]]
        calculated.append(self)
        return total_forces

    def apply_forces(self):
        print(self.applied_force, self.size)
        if math.fabs(self.applied_force[0]) >= self.threshold or self.touching_ground:
            self.move(self.applied_force)
        else:
            self.move([0, self.applied_force[1]])
        if self.touching_ground:
            self.applied_force = [0, 0]
            self.velocity[1] = 0
        else:
            self.applied_force = [0, 0]
            self.velocity[1] += (self.mass * 5) * GRAVITY / 45

    def add_force(self, adds):
        self.applied_force = [self.applied_force[0] + adds[0], self.applied_force[1] + adds[1] + self.velocity[1]]

    def check_collision(self, other):
        return pygame.sprite.collide_circle(self.circle, other.circle)


class Connector:

    def __init__(self, power, sleep, nodes, status):
        self.init_status = status
        self.power = power/3
        self.nodes = nodes
        self.warping = 1.0
        self.status = status
        self.last_time = 0
        self.minLength = nodes[0].get_long(nodes[1])
        self.touching = False
        self.sleep = sleep
        nodes[0].connectors.append(self)
        nodes[1].connectors.append(self)

    def take_action(self):
        step = init_time - time.time()
        if round(step) % self.sleep == 0 and round(step) != self.last_time:
            self.last_time = round(step)
            self.status += 1
            if self.status == 3:
                self.status = 0
        if self.status == 1:
            self.expand()
        if self.status == 0:
            self.relax()

    def expand(self):
        self.warping = .75
        ratio = find_ratio(self.nodes[0].cords, self.nodes[1].cords)
        self.nodes[0].add_force([-ratio[0][0] * self.power, -ratio[0][1] * self.power])
        self.nodes[1].add_force([ratio[1][0] * self.power, ratio[1][1] * self.power])
        self.touching = False

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
        if self.status == 1:
            color = (15, 75, 15)
        if self.status == 2:
            color = (15, 15, 15)
        pygame.draw.polygon(screen, color, ([node1[0], node1[1] + node1_thickness],
                                            [node1[0], node1[1] - node1_thickness],
                                            [node2[0], node2[1] - node2_thickness],
                                            [node2[0], node2[1] + node2_thickness]))
        self.nodes[0].draw()
        self.nodes[1].draw()


class Organism:

    def __init__(self, nodes, connectors):
        self.connectors = connectors
        self.nodes = nodes
        self.last_time = -1

    def control_forces(self):
        for n in self.nodes:
            n.sum_forces([n])
            n.apply_forces()

    def take_action(self):
        for c in self.connectors:
            c.take_action()

    def draw(self):
        for c in self.connectors:
            c.draw()

    def update(self):
        for n in self.nodes:
            n.update()


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
             Node(1.3, 3, [display_size/2 + 100, display_size / 2]),
             Node(1.1, 4, [display_size/2, display_size/2])]

all_connectors = [Connector(10, 1, [all_nodes[0], all_nodes[1]], 1),  # Between the OG 2 has the most power
                  Connector(15, 1, [all_nodes[1], all_nodes[2]], 2),  # Between the 1, and 2 has the middlest power
                  Connector(10, 1, [all_nodes[0], all_nodes[2]], 0)]  # Between the 0, and 2 has the least power
running = True
blank_node = Node(0, 0, [0, 0])
init_time = time.time()
organisms = [Organism(all_nodes, all_connectors)]
while running:
    moment = init_time - time.time()
    draw()
    for o in organisms:
        o.take_action()
        o.control_forces()
        o.update()
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            quit(0)
    time.sleep(.01)
