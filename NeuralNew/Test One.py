# TODO Comment Program

import pygame
import random
import math
import time

pygame.init()
font = pygame.font.Font('freesansbold.ttf', 15)
display_size = 900
screen = pygame.display.set_mode([display_size, display_size])
pygame.display.set_caption("Testing")
base = display_size - 150
ground = pygame.Rect((0, base, display_size, display_size - base))
GRAVITY = 1.2
AIR_FRICTION = 1.01
JOINT_FRICTION = 2.5


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
        self.resistance = 1
        self.friction = friction
        self.size = size * 3
        self.threshold = size * friction / 10
        self.cords = cords
        self.mass = size
        self.touching_ground = False
        self.connectors = []
        self.connected_nodes = []
        self.force_of_gravity = (self.mass * 5) * GRAVITY / 65 / self.resistance
        self.velocity = [0, self.force_of_gravity]
        self.applied_force = self.velocity
        self.color = (255, (203 - 135 * friction) * 1.88, (203 - 135 * friction) * 1.88)
        self.kinda_connected_nodes = []
        if friction > 1.5:
            self.color = (255, 0, 0)
        if friction < 0.5:
            self.color = (255, 230, 230)
        self.circle = Circle(self.color, self.size * 5, cords)

    def update(self):
        self.touching_ground = (self.cords[1] + self.size) == base
        self.update_cords()

    def update_cords(self):
        # self.circle.move_to(self.cords)
        return

    def add_node(self, other):
        self.connected_nodes.append(other)
        self.kinda_connected_nodes.append(other)
        for n in other.connected_nodes:
            if n not in self.kinda_connected_nodes:
                self.kinda_connected_nodes.append(n)

    def move(self, adds):
        xadd = adds[0]
        yadd = adds[1]
        if self.touching_ground and yadd > 0:
            yadd = 0
        friction = self.friction
        if not self.touching_ground:
            friction = AIR_FRICTION
        self.cords = [self.cords[0]+xadd/(friction*self.mass), self.cords[1]+yadd/self.mass]
        if self.cords[1] + self.size >= base:
            self.cords[1] = base-self.size
            self.touching_ground = True
        else:
            self.touching_ground = False
        self.update_cords()

    def get_long(self, other_node):
        x_length = math.fabs(self.cords[0] - other_node.cords[0])
        y_length = math.fabs(self.cords[1] - other_node.cords[1])
        return (x_length ** 2 + y_length ** 2) ** .5

    def draw(self):
        pygame.draw.circle(screen, self.color, [int(self.cords[0]), int(self.cords[1])], self.size)

    def sum_forces(self, calculated):
        if self in calculated:
            return [0, 0]
        calculated.append(self)
        self.resistance = 1
        for n in self.connected_nodes:
            adds = n.sum_forces(calculated)
            ratio = find_angle(self, n) * 3
            thing = 5 - ratio
            if thing < 0:
                thing = 1
            adds = [adds[0] / JOINT_FRICTION * ratio, adds[1] / JOINT_FRICTION * thing]
            self.applied_force = [self.applied_force[0] + adds[0], self.applied_force[1] + adds[1]]
        to_return = [self.applied_force[0], self.applied_force[1]]
        return to_return

    def apply_forces(self):
        if math.fabs(self.applied_force[0]) >= self.threshold or not self.touching_ground:
            self.move(self.applied_force)
        else:
            self.move([0, self.applied_force[1]])
        if self.touching_ground:
            self.velocity[1] = self.force_of_gravity
            self.applied_force = [self.velocity[0], self.velocity[1]]
            if self.applied_force[1] > 0:
                self.applied_force[1] = 0
        else:
            self.velocity[1] += self.force_of_gravity
            self.applied_force = [self.velocity[0], self.velocity[1]]

    def add_force(self, adds):
        self.applied_force = [self.applied_force[0] + adds[0], self.applied_force[1] + adds[1]]

    def check_collision(self, other):
        return pygame.sprite.collide_circle(self.circle, other.circle)

    def is_connected(self, other):
        return other in self.kinda_connected_nodes


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
        nodes[0].add_node(nodes[1])
        nodes[1].add_node(nodes[0])

    def take_action(self):
        step = moment
        if step % self.sleep == 0 and round(step) != self.last_time:
            self.last_time = round(step)
            self.status += 1
            if self.status == 3:
                self.status = 0
        if self.status == 0:
            self.expand()
        if self.status == 1:
            self.relax()
        return self.status

    def expand(self):
        self.warping = .75
        ratio = find_ratio(self.nodes[0].cords, self.nodes[1].cords)
        self.nodes[0].add_force([ratio[0][0] * self.power * -1, -ratio[0][1] * self.power * -1])
        self.nodes[1].add_force([ratio[1][0] * self.power, -ratio[1][1] * self.power])
        self.touching = False

    def relax(self):
        if not self.touching:
            self.warping = 1
            ratio = find_ratio(self.nodes[0].cords, self.nodes[1].cords)
            multiply = 1
            self.nodes[0].add_force([ratio[0][0] * multiply * self.power, ratio[0][1] * self.power])
            self.nodes[1].add_force([-ratio[0][0] * multiply * self.power, -ratio[0][1] * self.power])

    def draw(self):
        node1_thickness = int(self.nodes[0].size/5 * self.warping)
        node2_thickness = int(self.nodes[1].size/5 * self.warping)
        node1 = self.nodes[0].cords
        node2 = self.nodes[1].cords
        color = (75, 15, 15)
        if self.status == 1:
            color = (15, 75, 15)
        if self.status == 2 or self.power == 0:
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
        self.is_good_organism = True
        self.run = False

    def control_forces(self):
        for n in self.nodes:
            n.sum_forces([])
            n.apply_forces()

    def take_action(self):
        self.run = True
        x = -1
        for c in self.connectors:
            x += 0
            x = c.take_action()
        return x

    def draw(self):
        for n in self.nodes:
            if n.cords[0] + n.size < - 100 or \
                    n.cords[1] + n.size < - 100 or \
                    n.cords[0] - n.size > display_size + 100 or \
                    n.cords[1] - n.size > display_size + 100:
                self.is_good_organism = False
                return
        for c in self.connectors:
            c.draw()

    def update(self):
        for n in self.nodes:
            n.update()

    def get_distance_traveled(self):
        total = 0
        for n in self.nodes:
            total += n.cords[0]
        return total


class Generation:

    def __init__(self, number_of_organisms=50, older_gen=None):
        self.organisms = []
        self.active_org = 0
        if older_gen:
            for x in range(1, number_of_organisms - 1):
                self.breed_organisms([older_gen.organisms[x], older_gen.organisms[x - 1]])
                self.breed_organisms([older_gen.organisms[x], older_gen.organisms[x + 1]])
            print(len(self.organisms))
        else:
            for x in range(number_of_organisms):
                self.create_organisms()

    def create_organisms(self):
        num_nodes = random.randint(3, 6)
        nodes = []
        for num in range(num_nodes):
            nodes.append(Node(float(random.randint(7, 20)) / 10.0,
                              random.randint(3, 6),
                              [random.randint(display_size / 3, display_size / 3 * 2),
                               random.randint(base - 50, base)]))
        all_connected = False
        connectors = []
        while not all_connected:
            n1 = 0
            n2 = 0
            checking = True
            while checking:
                n1 = random.randint(0, num_nodes - 1)
                n2 = random.randint(0, num_nodes - 1)
                if nodes[n1].is_connected(nodes[n2]) or n2 == n1 or nodes[n1] == blank_node or nodes[n2] == blank_node:
                    checking = True
                else:
                    checking = False
            new_con = Connector(10, random.randint(1, 3), [nodes[n1], nodes[n2]], 2)
            connectors.append(new_con)
            broken = False
            for no1 in nodes:
                for no2 in nodes:
                    if no1 != no2:
                        all_connected = no1.is_connected(no2)
                    if not all_connected:
                        break
                if broken:
                    break
        self.organisms.append(Organism(nodes, connectors))

    def breed_organisms(self, old_organisms):
        with_least = 0
        num_nodes = [len(old_organisms[0].nodes), len(old_organisms[1].nodes)]
        if len(old_organisms[0].nodes) > len(old_organisms[0].nodes):
            num_nodes = [len(old_organisms[1].nodes), len(old_organisms[0].nodes)]
            with_least = 1
        num_nodes = random.randint(num_nodes[0], num_nodes[1])
        nodes = []
        for num in range(num_nodes):
            friction = []
            if num < num_nodes[0]:
                friction = [old_organisms[0].nodes[num].friction, old_organisms[1].nodes[num].friction]
                if old_organisms[0].nodes[num].friction > old_organisms[1].nodes[num].friction:
                    friction = [old_organisms[1].nodes[num].friction, old_organisms[0].nodes[num].friction]
            else:
                friction = [old_organisms[with_least].nodes[num].friction - .2,
                            old_organisms[with_least].nodes[num].friction + .2]
            if num < num_nodes[0]:  # TODO This
                sizes = [len(old_organisms[0].nodes), len(old_organisms[1].nodes)]
                if len(old_organisms[0].nodes) > len(old_organisms[0].nodes):
                    sizes = [len(old_organisms[1].nodes), len(old_organisms[0].nodes)]
            else:
                sizes = [len(old_organisms[1].nodes), len(old_organisms[0].nodes)]
            nodes.append(Node(float(random.randint(friction[0], friction[1])) / 10.0,
                              random.randint(3, 6),
                              [random.randint(display_size / 3, display_size / 3 * 2),
                               random.randint(base - 50, base)]))
        all_connected = False
        connectors = []
        while not all_connected:
            n1 = 0
            n2 = 0
            checking = True
            while checking:
                n1 = random.randint(0, num_nodes - 1)
                n2 = random.randint(0, num_nodes - 1)
                if nodes[n1].is_connected(nodes[n2]) or n2 == n1 or nodes[n1] == blank_node or nodes[n2] == blank_node:
                    checking = True
                else:
                    checking = False
            new_con = Connector(1, random.randint(1, 3), [nodes[n1], nodes[n2]], 2)
            connectors.append(new_con)
            broken = False
            for no1 in nodes:
                for no2 in nodes:
                    if no1 != no2:
                        all_connected = no1.is_connected(no2)
                    if not all_connected:
                        break
                if broken:
                    break
        self.organisms.append(Organism(nodes, connectors))

    def control_forces(self):
        self.organisms[self.active_org].control_forces()

    def take_action(self):
        self.organisms[self.active_org].take_action()

    def draw(self):
        self.organisms[self.active_org].draw()
        if not self.organisms[self.active_org].is_good_organism:
            self.next_org()

    def update(self):
        self.organisms[self.active_org].update()

    def next_org(self):
        self.active_org += 1
        if self.active_org == len(self.organisms):
            self.active_org = 0
            need_new_generation = True

    def sort_organisms(self):
        for dsa in self.organisms:
            for o in range(len(self.organisms) - 1):
                if self.organisms[o].get_distance_traveled() > self.organisms[o + 1].get_distance_traveled():
                    temp = self.organisms[o]
                    self.organisms[o] = self.organisms[o + 1]
                    self.organisms[o + 1] = temp

    def kill(self):
        self.sort_organisms()
        del self.organisms[0:4]
        for x in range(int((len(self.organisms) + 5) / 2 - 3)):
            del self.organisms[random.randint(0, len(self.organisms) - 11)]
        for x in range(3):
            del self.organisms[random.randint(len(self.organisms) - 11, len(self.organisms))]


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
    for gen in generations:
        gen.draw()
    pygame.display.update()


# all_nodes = [Node(1.7, 5, [display_size / 2 - 100, display_size]),
#              Node(.89, 3, [display_size / 2 + 100, display_size]),
#              Node(1.23, 4, [display_size / 2, display_size/2])]
#
# all_connectors = [Connector(10, 2, [all_nodes[0], all_nodes[1]], 2),  # Between the OG 2 has the most power
#                   Connector(10, 2, [all_nodes[1], all_nodes[2]], 2),  # Between the 1, and 2 has the middlest power
#                   Connector(10, 2, [all_nodes[0], all_nodes[2]], 2)]  # Between the 0, and 2 has the least power
#
# running = True
# blank_node = Node(0, 0, [0, 0])
# init_time = time.time()
# organisms = [Organism(all_nodes, all_connectors)]
# while running:
#     moment = init_time - time.time()
#     draw()
#     for o in organisms:
#         o.control_forces()
#         x = o.take_action()
#         if x == 0:
#             print("expanding")
#         elif x == 1:
#             print("relaxing")
#         o.update()
#     for event in pygame.event.get():
#         if event.type == pygame.QUIT:
#             pygame.quit()
#             quit(0)
#     time.sleep(.01)
#     print("")

running = True
blank_node = Node(0, 0, [0, 0])
new_gen = Generation()
generations = [new_gen]
init_time = time.time()
last10 = 0
current_generation = generations[len(generations) - 1]
need_new_generation = False
speed = 100
while running:
    moment = round(init_time * speed - time.time() * speed)
    draw()
    current_generation.control_forces()
    current_generation.take_action()
    current_generation.update()
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            quit(0)
    if moment % 5 == 0 and last10 != moment:
        if need_new_generation:
            generations.append(Generation(older_gen=current_generation))
            need_new_generation = False
            current_generation = generations[len(generations) - 1]
        else:
            current_generation.next_org()
        last10 = moment
