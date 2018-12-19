# TODO Comment Program

import pygame
import random
import math
import time

pygame.init()
font = pygame.font.Font('freesansbold.ttf', 30)
display_size = 900
screen = pygame.display.set_mode([display_size, display_size])
pygame.display.set_caption("Testing")
base = display_size - 150
ground = pygame.Rect((0, base, display_size, display_size - base))
GRAVITY = 1.2
AIR_FRICTION = 1.01
JOINT_FRICTION = 2.5
spawns_x = [display_size / 2 - 150, display_size / 2 - 100, display_size / 2 - 50, display_size / 2]
spawns_y = [base, base - 50, base - 100]
for s1 in range(len(spawns_x)):
    for s2 in range(len(spawns_x)):
        if spawns_x[s2] < spawns_x[s1]:
            temp_spawn = spawns_x[s1]
            spawns_x[s1] = spawns_x[s2]
            spawns_x[s2] = temp_spawn
for s1 in range(len(spawns_y)):
    for s2 in range(len(spawns_y)):
        if spawns_y[s2] < spawns_y[s1]:
            temp_spawn = spawns_y[s1]
            spawns_y[s1] = spawns_y[s2]
            spawns_y[s2] = temp_spawn
spawns = []
for s1 in spawns_x:
    for s2 in spawns_y:
        spawns.append([s1, s2])


def read_organisms():
    file_object = open("save_one", "r")
    organisms = []
    nodes = []
    connectors = []
    for line in file_object:
        sliced = line.split(",")
        if sliced[0] == "Node":
            sliced_cords = sliced[3].split("-")
            nodes.append(Node(float(sliced[1]), int(sliced[2]), [int(sliced_cords[0]), int(sliced_cords[0])]))
        if sliced[0] == "Connector":
            sliced_cords = sliced[3].split("-")
            connectors.append(Connector(int(sliced[1]), int(sliced[2]), [int(sliced_cords[0]), int(sliced_cords[0])],
                                        int(sliced[4])))
        if sliced[0] == "Organism":
            organisms.append(Organism(nodes, connectors))
            nodes = []
            connectors = []
        if sliced[0] == "Generation":
            generations.append(Generation(organisms=organisms))


def write_organisms():
    file_object = open("save_one", "w")
    for organism in current_generation.organisms:
        for node in organism.nodes:
            file_object.write("Node,"+str(node.friction)+","+str(node.size)+","+str(node.cords[0])+"-"+str(node.cords[0])+"\n")
        for connector in organism.connectors:
            file_object.write("Connector,"+str(connector.power)+","+str(connector.sleep)+","+str(connector.nodes[0])+"-"+str(connector.nodes[0])+str(connector.status)+","+"\n")
        file_object.write("Organism\n")
    file_object.write("Generation\n")


class Node:

    def __init__(self, friction, size, cords, copy=True):
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
        self.mode = 0
        self.init_cords = cords
        self.init_status = 0
        if copy:
            self.original = Node(friction, size, cords, copy=False)
        if friction > 1.5:
            self.color = (255, 0, 0)
        if friction < 0.5:
            self.color = (255, 230, 230)

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

        if self.mode == 0 or \
                (self.mode == 2 and xadd/(friction*self.mass) < 0) or \
                (self.mode == 1 and xadd/(friction*self.mass) > 0):
            self.cords = [self.cords[0]+xadd/(friction*self.mass), self.cords[1]+yadd/self.mass]
        else:
            self.cords = [self.cords[0], self.cords[1] + yadd / self.mass]
            global screen_adjust
            screen_adjust -= xadd / (friction * self.mass)

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
        self.init_status = status
        nodes[0].connectors.append(self)
        nodes[1].connectors.append(self)
        nodes[0].add_node(nodes[1])
        nodes[1].add_node(nodes[0])
        nodes[0].init_status = status
        nodes[1].init_status = status

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

    def __init__(self, nodes, connectors, copy=True):
        self.connectors = connectors
        self.nodes = nodes
        self.last_time = -1
        self.is_good_organism = True
        self.run = False
        self.spawns = []
        self.traveled = 0
        self.readjust()
        self.fitness = 0
        if copy:
            self.starting = Organism(nodes, connectors, copy=False)

    def compare_node_cords(self, other):
        same = []
        no_matches = []
        both = self.starting.nodes.copy()
        for o in other.starting.nodes:
            both.append(o)
        for n1 in range(len(self.starting.nodes)):
            if n1 == len(other.starting.nodes):
                break
            for n2 in range(len(self.starting.nodes)):
                if n2 == len(other.starting.nodes):
                    break
                if self.starting.nodes[n1].original.cords == other.starting.nodes[n2].original.cords:
                    same.append([self.starting.nodes[n1].original, self.starting.nodes[n2].original])
        for n1 in both:
            good = False
            for n2 in same:
                if n1 in n2:
                    good = True
            if not good:
                no_matches.append(n1)
        to_return = [same, no_matches]
        return to_return

    def readjust(self):
        bottom = spawns_y[len(spawns_y) - 1]
        rightist = spawns_x[len(spawns_x) - 1]
        for n in self.nodes:
            if n.cords[1] > bottom:
                bottom = n.cords[1]
            if n.cords[0] > rightist:
                rightist = n.cords[0]
        dist = [0, 0]
        dist[0] = spawns_y[0] - bottom
        dist[1] = spawns_x[0] - rightist
        for n in self.nodes:
            n.cords += dist
            n.original.cords += dist

    def control_forces(self):
        before = self.find_halfway()
        for n in self.nodes:
            n.sum_forces([])
            n.apply_forces()
        self.fitness += (before - self.find_halfway()) * -1

    def take_action(self):
        self.run = True
        x = -1
        for c in self.connectors:
            x += 0
            x = c.take_action()
        return x

    def draw(self):
        for c in self.connectors:
            c.draw()

    def update(self):
        for n in self.nodes:
            n.update()
        if self.get_space_between() > display_size or math.fabs(screen_adjust) > 500:
            self.is_good_organism = False
        for n in self.nodes:
            if n.cords[1] < 0:
                self.is_good_organism = False
        else:
            for n in self.nodes:
                if self.nodes[self.get_far_sides()[1]].cords[0] > display_size - 250 or \
                        self.nodes[self.get_far_sides()[1]].cords[0] > display_size - 300 and self.nodes[0].mode == 1:
                    n.mode = 2
                elif self.nodes[self.get_far_sides()[1]].cords[0] < 250 or \
                        self.nodes[self.get_far_sides()[1]].cords[0] < display_size - 300 and self.nodes[0].mode == 1:
                    n.mode = 1
                else:
                    n.mode = 0

    def find_halfway(self):
        sides = self.get_far_sides()
        return self.nodes[sides[0]].cords[0] - (self.nodes[sides[0]].cords[0] - self.nodes[sides[1]].cords[0]) / 2

    def get_distance_traveled(self):
        for n in self.nodes:
            self.traveled += n.cords[0] - display_size / 2
        return self.traveled

    def get_far_sides(self):
        leftist = 0
        rightist = 0
        for n in range(len(self.nodes)):
            if self.nodes[n].cords[0] < self.nodes[leftist].cords[0]:
                leftist = n
            if self.nodes[n].cords[0] > self.nodes[rightist].cords[0]:
                rightist = n
        return [leftist, rightist]

    def get_space_between(self):
        sides = self.get_far_sides()
        return self.nodes[sides[1]].cords[0] - self.nodes[sides[0]].cords[0]


class Generation:

    def __init__(self, number_of_organisms=100, older_gen=None, organisms=()):
        if len(organisms) == 0:
            self.organisms = []
            self.active_org = 0
            self.number_of_organisms = number_of_organisms
            self.ready = False
            if older_gen:
                self.breed_organisms(older_gen)
            else:
                for x in range(number_of_organisms):
                    self.create_organisms()
        else:
            self.organisms = organisms
            self.active_org = 0
            self.number_of_organisms = len(self.organisms)
            self.ready = False

    def create_organisms(self):
        num_nodes = random.randint(3, 6)
        nodes = []
        not_used_cords = spawns.copy()
        for num in range(num_nodes):
            cords = random.choice(not_used_cords)
            nodes.append(Node(float(random.randint(100, 200)) / 100.0,
                              random.randint(3, 6),
                              cords))
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
        # Kill the disabled
        num_bad = 0
        for o in old_organisms.organisms:
            if not o.is_good_organism:
                num_bad += 1
        for o in range(len(old_organisms.organisms) - num_bad):
            if not old_organisms.organisms[o].is_good_organism:
                del old_organisms.organisms[o]
            else:
                for o2 in range(o, len(old_organisms.organisms) - 1):
                    if old_organisms.organisms[o].fitness > old_organisms.organisms[o + 1].fitness:
                        temp = old_organisms.organisms[o]
                        old_organisms.organisms[o] = old_organisms.organisms[o + 1]
                        old_organisms.organisms[o] = temp

        # Kill the weak
        old_organisms = self.kill(old_organisms)

        # Breed the strong
        need_a_mate = old_organisms.organisms.copy()
        organisms = []
        while len(self.organisms) < self.number_of_organisms:
            if len(need_a_mate) > 0:
                o1 = random.randint(0, len(need_a_mate) - 1)
                o2 = random.randint(0, len(old_organisms.organisms) - 1)
                while need_a_mate[o1] == old_organisms.organisms[o2]:
                    o2 = random.randint(0, len(old_organisms.organisms) - 1)
                organisms.append(mix(need_a_mate.pop(o1), old_organisms.organisms[o2]))
            else:
                o1 = random.randint(0, len(old_organisms.orgamisms) - 1)
                o2 = random.randint(0, len(old_organisms.orgamisms) - 1)
                while need_a_mate[o1] == old_organisms.orgamisms[o2]:
                    o2 = random.randint(0, len(old_organisms.orgamisms) - 1)
                organisms.append(mix(old_organisms[o1], old_organisms.orgamisms[o2]))

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
        global organism_number
        if self.active_org == len(self.organisms):
            self.active_org = 0
            global need_new_generation, generation
            need_new_generation = True
            organism_number = 0
            generation += 1
        organism_number += 1
        global screen_adjust
        screen_adjust = 0

    def sort_organisms(self):
        for dsa in self.organisms:
            for o in range(len(self.organisms) - 1):
                if self.organisms[o].fitness > self.organisms[o + 1].fitness:
                    temp = self.organisms[o]
                    self.organisms[o] = self.organisms[o + 1]
                    self.organisms[o + 1] = temp

    def kill(self, old_organisms):
        self.ready = True
        old_organisms.sort_organisms()
        if len(old_organisms.organisms) > old_organisms.number_of_organisms / 4 and len(old_organisms.organisms) > 25:
            del old_organisms.organisms[0:4]
            for i in range(int(len(old_organisms.organisms) / 8) - 1):
                del old_organisms.organisms[random.randint(0, len(old_organisms.organisms) - 6)]
                del old_organisms.organisms[random.randint(len(old_organisms.organisms) - 6,
                                                           len(old_organisms.organisms) - 1)]
        return old_organisms

    def get_fitness_of_current(self):
        return self.organisms[self.active_org].fitness


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
    global screen_adjust
    while screen_adjust > 0:
        screen_adjust -= 100
    while screen_adjust < 0:
        screen_adjust += 100
    for x in range(0, display_size + 100, 100):
        xb = x + screen_adjust
        pygame.draw.rect(screen, (50, 50, 50), (xb + screen_adjust, 0, 6, base))


def draw_text():
    msg1 = "Distance Traveled: " + str(round(current_generation.get_fitness_of_current()))
    msg2 = "Organism: " + str(organism_number)
    text1 = pygame.font.Font.render(font, msg1, True, (255, 0, 0))
    text2 = pygame.font.Font.render(font,  msg2, True, (255, 0, 0))
    screen.blit(text1, (display_size / 2 - font.size(msg1)[0] / 2, 30))
    screen.blit(text2, (display_size / 2 - font.size(msg2)[0] / 2, 75))


def draw():
    draw_back()
    for gen in generations:
        gen.draw()
    draw_text()
    pygame.display.update()


def order(to_sort):
    if to_sort[0] > to_sort[1]:
        temp = to_sort[0]
        to_sort[0] = to_sort[1]
        to_sort[1] = temp
    return to_sort


def mix(org1, org2):
    nodes = org1.compare_node_cords(org2)
    cords_used = []
    created_nodes = []
    connectors_to_replicate = []
    for n in nodes[0]:
        to_sort = order([int(n[0].friction * 100), int(n[1].friction)])
        friction = float(random.randint(to_sort[0], to_sort[1])) / 100.0
        to_sort = order([n[0].size, n[1].size])
        size = random.randint(to_sort[0], to_sort[1])
        created_nodes.append(Node(friction, size, n[0].cords))
        cords_used.append(n[0].cords)
        connectors_to_replicate.append(n[random.randint(0, 1)].connectors)
    for n in nodes[1]:
        if random.randint(0, 2) == 2 and n.cords not in cords_used:
            friction = random.randint(int(n.friction * 100 - 5), int(n.friction * 100 + 5)) / 100
            size = random.randint(n.size - 2, n.size + 2)
            if size < 0:
                size += 1
            if friction < 1:
                friction = 1
            created_nodes.append(Node(friction, size, n.cords))
            cords_used.append(n.cords)
            connectors_to_replicate.append(n.connectors)

    created_connectors = []
    loading = []
    for c1 in connectors_to_replicate:
        for c2 in c1:
            correct_nodes = []
            for n in created_nodes:
                if n.cords == c2.nodes[0].init_cords or n.cords == c2.nodes[1].init_cords:
                    correct_nodes.append(n)
            correct_nodes.append(c2)
            loading.append(correct_nodes)
    for x in loading:
        created_connectors.append(Connector(10, x[2].init_status, [x[0], x[1]], 2))


running = True
blank_node = Node(0, 0, [0, 0])
new_gen = # Generation()
generations = [new_gen]
init_time = time.time()
last10 = 0
current_generation = generations[len(generations) - 1]
need_new_generation = False
speed = 1000
screen_adjust = 0
org_init_time = time.time()
generation = 1
organism_number = 1
organism_since_started = 1
sums = []
average = 0

write_organisms()

# while running:
#     start_loop = time.time()
#     moment = round(org_init_time * speed - start_loop * speed) * -1
#     draw()
#     current_generation.control_forces()
#     current_generation.take_action()
#     current_generation.update()
#     for event in pygame.event.get():
#         if event.type == pygame.QUIT:
#             pygame.quit()
#             quit(0)
#     if moment % 5 == 0 and last10 != moment:
#         if need_new_generation:
#             generations.append(Generation(older_gen=current_generation))
#             need_new_generation = False
#             current_generation = generations[len(generations) - 1]
#         else:
#             current_generation.next_org()
#             org_init_time = time.time()
#         organism_started = time.time()
#         last10 = moment
#     end_loop = time.time()
#     sums.append(end_loop - start_loop)
#     average += 1
    # print(sum(sums) / average)
