import random

from Classes.Constants import *
from Classes.Materials import Materials
from Classes.TradeOffer import TradeOffer
from Interfaces.AgentInterface import AgentInterface
from Managers.CommerceManager import CommerceManager

class b2(AgentInterface):
    """
    Es necesario poner super().nombre_de_funcion() para asegurarse de que coge la función del padre
    """
    town_number = 0
    material_given_more_than_three = None
    MAX_STACK = 4
    COMMERCE_COUNT = 0
    MAX_VP = 3
    vp = 2
    # Son los materiales más necesarios en construcciones, luego se piden con year of plenty para tener en mano
    year_of_plenty_material_one = MaterialConstants.CEREAL
    year_of_plenty_material_two = MaterialConstants.MINERAL

    def __init__(self, agent_id):
        super().__init__(agent_id)

    def on_trade_offer(self, board_instance, incoming_trade_offer=TradeOffer(), player_making_offer=int):
        """
        Hay que tener en cuenta que gives se refiere a los materiales que da el jugador que hace la oferta,
        luego en este caso es lo que recibe
        :param incoming_trade_offer:
        :return:
        """
        # turns_left = self.id - player_making_offer
        offers = incoming_trade_offer.gives
        demands = incoming_trade_offer.receives
        numOffers = offers.cereal + offers.clay + offers.mineral + offers.wood + offers.wool
        numDemands = demands.cereal + demands.mineral + demands.wood + demands.wool + demands.clay

        if numOffers >= numDemands:
            if (self.town_number > 0 and self.MAX_VP <= self.vp and
                    offers.cereal > 0 and self.hand.resources.cereal < 2 or
                    offers.mineral > 0 and self.hand.resources.mineral < 3):
                return True
            elif len(self.board.valid_town_nodes(self.id)) > 0:
                i = 0
                for mat in self.hand.resources.array_ids:
                    if i != 1 and mat < 1 and demands.get_from_id(i) < 1 and offers.get_from_id(i) > 0:
                        return True
                    else:
                        return False
            elif not self.hand.resources.has_this_more_materials('road'):
                if (offers.clay > 0 and self.hand.resources.clay < 1 or
                        offers.wood > 0 and self.hand.resources.mineral < 1):
                    return True
                else:
                    return False
        else:
            return False
            # if turns_left == 1 or turns_left == -3:



    def on_turn_start(self):
        # Si tiene mano de cartas de desarrollo
        if len(self.development_cards_hand.check_hand()):
            # Mira todas las cartas
            for i in range(0, len(self.development_cards_hand.check_hand())):
                # Si una es un caballero
                if self.development_cards_hand.hand[i].type == DevelopmentCardConstants.KNIGHT:
                    # La juega
                    return self.development_cards_hand.select_card_by_id(self.development_cards_hand.hand[i].id)
        return None

    def on_having_more_than_7_materials_when_thief_is_called(self):
        # Comprueba si tiene materiales para construir una ciudad. Si los tiene, descarta el resto que no le sirvan.
        if self.hand.resources.has_this_more_materials(BuildConstants.CITY):
            while self.hand.get_total() > 7:
                if self.hand.resources.wool > 0:
                    self.hand.remove_material(4, 1)

                if self.hand.resources.cereal > 2:
                    self.hand.remove_material(0, 1)
                if self.hand.resources.mineral > 3:
                    self.hand.remove_material(1, 1)

                if self.hand.resources.clay > 0:
                    self.hand.remove_material(2, 1)
                if self.hand.resources.wood > 0:
                    self.hand.remove_material(3, 1)
        # Si no tiene materiales para hacer una ciudad descarta de manera aleatoria cartas de su mano
        return self.hand

    def on_moving_thief(self):
        # Bloquea un número 6 u 8 donde no tenga un pueblo, pero que tenga uno del rival
        # Si no se dan las condiciones lo deja donde está, lo que hace que el GameManager lo ponga en un lugar aleatorio
        terrain_with_thief_id = -1
        for terrain in self.board.terrain:
            if not terrain['has_thief']:
                if terrain['probability'] == 6 or terrain['probability'] == 8:
                    nodes = self.board.__get_contacting_nodes__(terrain['id'])
                    has_own_town = False
                    has_enemy_town = False
                    enemy = -1
                    for node_id in nodes:
                        if self.board.nodes[node_id]['player'] == self.id:
                            has_own_town = True
                            break
                        if self.board.nodes[node_id]['player'] != -1:
                            has_enemy_town = True
                            enemy = self.board.nodes[node_id]['player']

                    if not has_own_town and has_enemy_town:
                        return {'terrain': terrain['id'], 'player': enemy}
            else:
                terrain_with_thief_id = terrain['id']

        return {'terrain': terrain_with_thief_id, 'player': -1}

    def on_turn_end(self):
        # Si tiene mano de cartas de desarrollo
        if len(self.development_cards_hand.check_hand()):
            # Mira todas las cartas
            for i in range(0, len(self.development_cards_hand.check_hand())):
                # Si una es un punto de victoria
                if self.development_cards_hand.hand[i].type == DevelopmentCardConstants.VICTORY_POINT:
                    # La juega
                    self.vp += 1
                    return self.development_cards_hand.select_card_by_id(self.development_cards_hand.hand[i].id)
        return None

    def on_commerce_phase(self):
        """
        Se podría complicar mucho más la negociación, cambiando lo que hace en función de si tiene o no puertos y demás
        """
        if self.COMMERCE_COUNT > 0:
            self.COMMERCE_COUNT = 0

        harbor = self.board.player_harbors(self.id)
        harbor_manager = CommerceManager()

        gives = Materials()
        receives = Materials()

        has_city = self.hand.resources.has_this_more_materials(BuildConstants.CITY)
        has_town = self.hand.resources.has_this_more_materials(BuildConstants.TOWN)
        has_road = self.hand.resources.has_this_more_materials(BuildConstants.ROAD)

        # Pedir lo que falte para una ciudad, ofrece el resto de materiales iguales a los que pide
        if not has_city and self.town_number > 0 and self.vp >= self.MAX_VP:
            # PUERTOS
            if HarborConstants.WOOL in harbor:
                while not has_city and self.hand.resources.wool >= 2:
                    if self.hand.resources.mineral < 3:
                        harbor_manager.trade_through_special_harbor(self.hand, MaterialConstants.WOOL,
                                                                    MaterialConstants.MINERAL)
                    elif self.hand.resources.cereal < 2:
                        harbor_manager.trade_through_special_harbor(self.hand, MaterialConstants.WOOL,
                                                                    MaterialConstants.CEREAL)

                    has_city = self.hand.resources.has_this_more_materials(BuildConstants.CITY)
            elif HarborConstants.ALL in harbor:
                while not has_city and self.hand.resources.wool >= 3:
                    if self.hand.resources.mineral < 3:
                        harbor_manager.trade_through_special_harbor(self.hand, MaterialConstants.WOOL,
                                                                    MaterialConstants.MINERAL)
                    elif self.hand.resources.cereal < 2:
                        harbor_manager.trade_through_special_harbor(self.hand, MaterialConstants.WOOL,
                                                                    MaterialConstants.CEREAL)
                    has_city = self.hand.resources.has_this_more_materials(BuildConstants.CITY)

            if has_city:
                # self.material_given_more_than_three = None
                return None

            cereal_left = 2 - self.hand.resources.cereal
            id, max = self.max_hand() # randomizar si hay mas de uno

            if max >= self.MAX_STACK:
                gives.add_material(id,1)
            else:
                gives.add_material(MaterialConstants.WOOL,1)

            # Probamos intercambio 1:2
            if self.COMMERCE_COUNT < 1:
                for i in range(2):
                    if cereal_left > 0:
                        receives.add_material(MaterialConstants.CEREAL,1)
                        cereal_left -= 1
                    else:
                        receives.add_material(MaterialConstants.MINERAL,1)
                self.COMMERCE_COUNT += 1
            # Pasamos a 1:1
            else:
                if cereal_left > 0:
                    receives.add_material(MaterialConstants.CEREAL,1)
                else:
                    receives.add_material(MaterialConstants.MINERAL,1)
                self.COMMERCE_COUNT = 0

            return TradeOffer(gives,receives)
            # CIUDAD END

        # POBLADO
        elif not has_town and len(self.board.valid_town_nodes(self.id)) > 0:
            # PUERTOS
            if HarborConstants.NONE not in harbor:
                # Buscamos el material que nos falta y lo intercambiamos solo por piedra, o en un puerto especial de piedra
                i = 0
                for mat in self.hand.resources.array_ids:
                    if mat < 1 and i != 1:
                        if HarborConstants.MINERAL in harbor:
                            harbor_manager.trade_through_special_harbor(self.hand, MaterialConstants.MINERAL, i)
                        else:
                            harbor_manager.trade_through_harbor(self.hand, MaterialConstants.MINERAL, i)
                    i += 1
            # Negociación con jugadores
            id, max = self.max_hand()

            if max >= self.MAX_STACK:
                gives.add_material(id, 1)
            else:
                gives.add_material(MaterialConstants.MINERAL, 1)

            # Probamos intercambio 1:2
            if self.COMMERCE_COUNT < 1:
                i = 0
                j = 0
                for mat in self.hand.resources.array_ids:
                    if mat < 1 and i != 1 and j < 2:
                        j += 1
                        receives.add_material(i,1)
                    i += 1

                self.COMMERCE_COUNT += 1
            # Pasamos a 1:1
            else:
                i = 0
                for mat in self.hand.resources.array_ids:
                    i += 1
                    if mat < 1 and i != 1:
                        receives.add_material(i, 1)

                self.COMMERCE_COUNT = 0
            return TradeOffer(gives,receives)

        elif not has_road:
            # Buscamos el material que nos falta y lo intercambiamos solo por piedra, o en un puerto especial de piedra
            if HarborConstants.MINERAL in harbor:
                while not has_road and self.hand.resources.mineral >= 2:
                    if self.hand.resources.clay < 1:
                        harbor_manager.trade_through_special_harbor(self.hand, MaterialConstants.MINERAL,
                                                                    MaterialConstants.CLAY)
                    elif self.hand.resources.wood < 1:
                        harbor_manager.trade_through_special_harbor(self.hand, MaterialConstants.MINERAL,
                                                                    MaterialConstants.WOOD)

                    has_road = self.hand.resources.has_this_more_materials(BuildConstants.ROAD)
            elif HarborConstants.ALL in harbor:
                while not has_road and self.hand.resources.mineral >= 3:
                    if self.hand.resources.clay < 1:
                        harbor_manager.trade_through_harbor(self.hand, MaterialConstants.MINERAL,
                                                                    MaterialConstants.CLAY)
                    elif self.hand.resources.wood < 1:
                        harbor_manager.trade_through_harbor(self.hand, MaterialConstants.MINERAL,
                                                                    MaterialConstants.WOOD)

                    has_road = self.hand.resources.has_this_more_materials(BuildConstants.ROAD)


            if has_road:
                return None

            id, max = self.max_hand()
            total_road = self.hand.resources.wood + self.hand.resources.clay

            if max >= self.MAX_STACK:
                gives.add_material(id, 1)
            else:
                gives.add_material(MaterialConstants.MINERAL, 1)

            # Probamos intercambio 1:2
            if self.COMMERCE_COUNT < 1 and total_road < 1:
                receives.add_material(MaterialConstants.CLAY,1)
                receives.add_material(MaterialConstants.WOOD,1)
                self.COMMERCE_COUNT += 1
            # Pasamos a 1:1
            else:
                if self.hand.resources.wood <= 0:
                    receives.add_material(MaterialConstants.WOOD, 1)
                else:
                    receives.add_material(MaterialConstants.CLAY, 1)
                self.COMMERCE_COUNT = 0
            return TradeOffer(gives,receives)

    def on_build_phase(self, board_instance):
        # Juega año de la cosecha si le faltan 2 o 1 materiales para completar una construcción
        # Juega construir carreteras si le da para camino más largo o con ello puede alcanzar un puerto (que no tenga)
        self.board = board_instance

        # Si tiene mano de cartas de desarrollo
        if len(self.development_cards_hand.check_hand()):
            # Mira todas las cartas
            for i in range(0, len(self.development_cards_hand.check_hand())):
                # Comprueba primero de que hay más de 2 carreteras disponibles para construirlas
                road_possibilities = self.board.valid_road_nodes(self.id)

                # Si una es año de la cosecha o construir carreteras y hay al menos 2 carreteras disponibles a construir
                if (self.development_cards_hand.hand[i].effect == DevelopmentCardConstants.YEAR_OF_PLENTY_EFFECT or
                        (self.development_cards_hand.hand[i].effect == DevelopmentCardConstants.ROAD_BUILDING_EFFECT and
                         len(road_possibilities) > 1)):
                    # La juega
                    return self.development_cards_hand.select_card_by_id(self.development_cards_hand.hand[i].id)

        if self.hand.resources.has_this_more_materials(BuildConstants.CITY) and self.town_number > 0:
            possibilities = self.board.valid_city_nodes(self.id)
            for node_id in possibilities:
                for terrain_piece_id in self.board.nodes[node_id]['contacting_terrain']:
                    # Hacemos una ciudad solo si la probabilidad de que salga el número es mayor o igual a 4/36
                    if self.board.terrain[terrain_piece_id]['probability'] == 5 or \
                            self.board.terrain[terrain_piece_id]['probability'] == 6 or \
                            self.board.terrain[terrain_piece_id]['probability'] == 8 or \
                            self.board.terrain[terrain_piece_id]['probability'] == 9:
                        self.town_number -= 1  # Transformamos un pueblo en una ciudad
                        self.town_number += 1 # Añadimos la cuidad
                        self.vp += 1
                        return {'building': BuildConstants.CITY, 'node_id': node_id}

        if self.hand.resources.has_this_more_materials(BuildConstants.TOWN):
            possibilities = self.board.valid_town_nodes(self.id)
            for node_id in possibilities:
                for terrain_piece_id in self.board.nodes[node_id]['contacting_terrain']:
                    # Hacemos un pueblo solo si la probabilidad de que salga el número es mayor o igual a 3/36
                    # O si el nodo es costero y posee un puerto
                    if self.board.terrain[terrain_piece_id]['probability'] == 4 or \
                            self.board.terrain[terrain_piece_id]['probability'] == 5 or \
                            self.board.terrain[terrain_piece_id]['probability'] == 6 or \
                            self.board.terrain[terrain_piece_id]['probability'] == 8 or \
                            self.board.terrain[terrain_piece_id]['probability'] == 9 or \
                            self.board.terrain[terrain_piece_id]['probability'] == 10:
                        self.town_number += 1  # Añadimos un pueblo creado
                        self.vp += 1
                        return {'building': BuildConstants.TOWN, 'node_id': node_id}

        if self.hand.resources.has_this_more_materials(BuildConstants.ROAD):
            # Construye sí o sí carretera si acaba en un nodo costero, pero, ¿y si no lo busca aleatoriamente?
            # Idealmente, debe de poder buscar caminos y encontrar el ideal a un puerto o similar, pero eso implicaría
            #  programar un algoritmo de búsqueda de nodos por pesos que actualmente me parece imposible de hacer.

            # Comprobar qué caminos posibles hay para cada nodo. Escoger el más alto si el ID del nodo es 32 o más.
            # Más bajo si es menor hacer override de eso si uno de los dos es directamente costero

            # TODO: Sería ideal que funcionase pero hay poco tiempo, que coja una aleatoria,
            #  pero si es costero y tiene puerto lo coge siempre
            possibilities = self.board.valid_road_nodes(self.id)
            for road_obj in possibilities:
                if self.board.is_it_a_coastal_node(road_obj['finishing_node']) and \
                        self.board.nodes[road_obj['finishing_node']]['harbor'] != HarborConstants.NONE:
                    return {'building': BuildConstants.ROAD,
                            'node_id': road_obj['starting_node'],
                            'road_to': road_obj['finishing_node']}

            # Asumiendo que no hay ninguna ideal (es decir, robarse los puertos),
            #   construye una carretera aleatoria, el 60% de las veces
            will_build = random.randint(0, 2)
            if will_build:
                if len(possibilities):
                    road_node = random.randint(0, len(possibilities) - 1)
                    return {'building': BuildConstants.ROAD,
                            'node_id': possibilities[road_node]['starting_node'],
                            'road_to': possibilities[road_node]['finishing_node']}

        # Si tiene materiales para hacer una carta, la construye. Como va la última en la pila,
        #    ya habrá construido cualquier otra cosa más útil
        if self.hand.resources.has_this_more_materials(BuildConstants.CARD):
            return {'building': BuildConstants.CARD}

        return None

    def on_game_start(self, board_instance):
        # Si el terreno tiene un 6 o un 8 mirar los adyacentes y el siguiente número más cercano a 7
        #   es donde construye la casa si no hay nadie. La carretera se hace apuntando al mar
        self.board = board_instance
        possibilities = self.board.valid_starting_nodes()
        # Se generan las variables que tendrán el resultado final
        chosen_node_id = -1
        # chosen_road_to_id = -1
        for node_id in possibilities:
            for terrain_id in self.board.nodes[node_id]['contacting_terrain']:
                if (self.board.terrain[terrain_id]['probability'] == 6 or
                        self.board.terrain[terrain_id]['probability'] == 8):
                    chosen_node_id = node_id

        # Si no hay ningún nodo ideal, se elige aleatoriamente entre las opciones
        if chosen_node_id == -1:
            chosen_node_id = possibilities[random.randint(0, len(possibilities) - 1)]

        # Sumamos 1 a la cantidad de pueblos creados
        self.town_number += 1

        # Se elige una carretera aleatoria entre todas las opciones
        possible_roads = self.board.nodes[chosen_node_id]['adjacent']
        chosen_road_to_id = possible_roads[random.randint(0, len(possible_roads) - 1)]

        return chosen_node_id, chosen_road_to_id

    def on_monopoly_card_use(self):
        # Elige el material que más haya intercambiado (variable global de esta clase)
        return self.material_given_more_than_three

    # noinspection DuplicatedCode
    def on_road_building_card_use(self):
        # Elige dos carreteras aleatorias entre las opciones
        valid_nodes = self.board.valid_road_nodes(self.id)
        # Se supone que solo se ha usado la carta si hay más de 2 carreteras disponibles a construir,
        # pero se dejan por si acaso
        if len(valid_nodes) > 1:
            while True:
                road_node = random.randint(0, len(valid_nodes) - 1)
                road_node_2 = random.randint(0, len(valid_nodes) - 1)
                if road_node != road_node_2:
                    return {'node_id': valid_nodes[road_node]['starting_node'],
                            'road_to': valid_nodes[road_node]['finishing_node'],
                            'node_id_2': valid_nodes[road_node_2]['starting_node'],
                            'road_to_2': valid_nodes[road_node_2]['finishing_node'],
                            }
        elif len(valid_nodes) == 1:
            return {'node_id': valid_nodes[0]['starting_node'],
                    'road_to': valid_nodes[0]['finishing_node'],
                    'node_id_2': None,
                    'road_to_2': None,
                    }
        return None

    def on_year_of_plenty_card_use(self):
        return {'material': self.year_of_plenty_material_one, 'material_2': self.year_of_plenty_material_two}

    def max_hand(self):
        max = 0
        id = 0
        for i in range(5):
            if max < self.hand.resources.get_from_id(i):
                max = self.hand.resources.get_from_id(i)
                id = i

        return (id, max)

    def min_hand(self):
        min = 10
        id = 0
        for i in range(5):
            if min > self.hand.resources.get_from_id(i):
                min = self.hand.resources.get_from_id(i)
                id = i

        return (id, min)

