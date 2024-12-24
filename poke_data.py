from typing import Optional, List
from pokemontcgsdk import Card
from pokemontcgsdk.ability import Ability
from pokemontcgsdk.attack import Attack

import datetime
import re
import json
import copy

# Turn json data into dicts
with open('data.json', 'r', encoding='utf-8') as file:
    data = json.load(file)
    energy_types = data['energy_types']
    rarity_format = data['rarity_format']
    rarity_weights = data['rarity_weights']
    sets = data['sets']
    trainer_names = data['trainer_names']
    generations = data['generations']
    card_amount = data['card_amount']

trainer_subtypes = {
    'Item': [
        'Clefairy Doll',
        'Computer Search'
        'Devolution Spray',
        'Item Finder',
        'Switch',
        'Scoop Up',
        'Defender',
        'Energy Retrieval',
        'Full Heal',
        'Maintenance',
        'PlusPower',
        'Pokémon Flute',
        'Pokédex',
        'Revive',
        'Super Potion',
        'Energy Removal',
        'Potion',
        'Switch',
        'Poké Ball',
        'Energy Search',
        'Recycle',
        'Mysterious Fossil',
        ''
    ],
    'Supporter': [
        'Imposter Professor Oak',
        'Impostor Professor Oak',
        'Lass',
        'Pokémon Breeder',
        'Pokémon Trader',
        'Super Energy Removal',
        'Super Energy Removal 2',
        'Pokémon Center',
        'Bill',
        'Gust of Wind',
        'Mr. Fuji',
        'Gambler',
        'Here Comes Team Rocket!',
        ''
    ],
    'Stadium': [
        ''
    ],
    'Tool': [
        ''
    ]
}

special_rules = {}

basic_energy_list = [
    "Fighting Energy", "Fire Energy", "Grass Energy", "Lightning Energy", "Psychic Energy", "Water Energy"
]

letter_widths = {
    'a': 6,
    'b': 6,
    'c': 6,
    'd': 6,
    'e': 6,
    'f': 5,
    'g': 6,
    'h': 6,
    'i': 2,
    'j': 6,
    'k': 5,
    'l': 3,
    'm': 6,
    'n': 6,
    'o': 6,
    'p': 6,
    'q': 6,
    'r': 6,
    's': 6,
    't': 4,
    'u': 6,
    'v': 6,
    'w': 6,
    'x': 6,
    'y': 6,
    'z': 6,
    'A': 6,
    'B': 6,
    'C': 6,
    'D': 6,
    'E': 6,
    'F': 6,
    'G': 6,
    'H': 6,
    'I': 4,
    'J': 6,
    'K': 6,
    'L': 6,
    'M': 6,
    'N': 6,
    'O': 6,
    'P': 6,
    'Q': 6,
    'R': 6,
    'S': 6,
    'T': 6,
    'U': 6,
    'V': 6,
    'W': 6,
    'X': 6,
    'Y': 6,
    'Z': 6,
    '0': 6,
    '1': 6,
    '2': 6,
    '3': 6,
    '4': 6,
    '5': 6,
    '6': 6,
    '7': 6,
    '8': 6,
    '9': 6,
    '\'': 2,
    '/': 6,
    '.': 2,
    ',': 2,
    ':': 2,
    ';': 2,
    '%': 6,
    '#': 6,
    '!': 2,
    '&': 6,
    '(': 5,
    ')': 5,
    '"': 4,
    '-': 6,
    '_': 6,
    ' ': 4,
    '[': 4,
    ']': 4,
    '♥': 6,
    '>': 6,
    '♂': 6,
    '♀': 6,
    '●': 5,
    '$': 5
}

special_strings_dict = {
    "\u2605": {
        "text": "Shining ",
        "underlined": False,
        "bold": False,
        "italic": False,
        "color": "#eff707"
    },
    "ex": {
        "text": " ex",
        "underlined": False,
        "bold": True,
        "italic": True,
        "color": "white"
    },
    "\u03B4": {
        "text": " \u03b4",
        "underlined": False,
        "bold": True,
        "italic": False,
        "color": "gray"
    }
}

energy_trainer_cards = {}


def attack_cost_tag_line(attack: Attack) -> tuple[list[list[dict]], dict]:
    attack_cost = {}
    attack_tag_line1 = []
    attack_tag_line2 = []
    if attack.cost is not None:
        for energy in attack.cost:
            if energy in attack_cost:
                attack_cost[energy] += 1
            else:
                attack_cost[energy] = 1
    colorless_value = attack_cost.pop("Colorless", None)
    attack_cost = dict(sorted(attack_cost.items(), key=lambda item: item[1], reverse=True))
    if colorless_value is not None:
        attack_cost["Colorless"] = colorless_value
    energy_type = energy_types[next(iter(attack_cost))]
    color = energy_type["main_color"]
    tag_string = "        Cost : "
    attack_tag_line1.append(
        tag_line_generator(text=tag_string, color=color, underlined=False, bold=False, italic=False))
    for n, energy in enumerate(attack_cost):
        tag_string = f"{attack_cost[energy]} {str(energy)}"
        if n + 1 == 3:
            tag_string = f"                {attack_cost[energy]} {str(energy)}"
        if n + 1 < len(attack_cost):
            tag_string += ", "
        energy_color = energy_types[energy]["main_color"]
        tag_line = tag_line_generator(text=tag_string, color=energy_color, underlined=False, bold=False, italic=False)
        if n + 1 < 3:
            attack_tag_line1.append(tag_line)
        else:
            attack_tag_line2.append(tag_line)

    return [attack_tag_line1, attack_tag_line2], energy_type


def tag_line_generator(text: str, color: str, underlined: bool, bold: bool, italic: bool) -> dict:
    tag_line = {"text": text}
    optional_styles = {"color": color, "underlined": underlined, "bold": bold, "italic": italic}
    tag_line.update({key: value for key, value in optional_styles.items() if value})
    tag_line["italic"] = italic

    return tag_line


def headline_generator(text: str, color: str, underlined: bool, bold: bool, italic: bool) -> dict:
    return {"text": text, "color": color, "bold": bold, "italic": italic}


def evolution_line(card, type_color: str, lore_lines: list) -> list:
    max_health_width = 188 - sum(letter_widths.get(char, 0) for char in f"{card.hp}HP")
    if card.evolves_from is None:
        evolution_string = f"> Basic Pokémon"
    else:
        evolution_name = card.evolves_from
        name_split = evolution_name.split()
        if "Team" in name_split:
            evolution_name = evolution_name.replace("Team ", "")
        evolution_string = f"> Evolves from {evolution_name}"
    evolution_string = evolution_line_width(evolution_string, max_health_width, card.hp)
    evolution = tag_line_generator(evolution_string, color=type_color, underlined=False, bold=False, italic=False)
    hp = tag_line_generator(text=card.hp + "HP", color="#FF0000", underlined=False, bold=False, italic=False)
    lore_lines.append([evolution, hp])

    return lore_lines


def ability_line(ability, pokemon_type: str, lore_lines: list) -> list:
    ability_name = f"# {ability.name}"
    color = energy_types[pokemon_type]["main_color"]
    sub_color = energy_types[pokemon_type]["sub_color"]
    ability_name_tag = tag_line_generator(text=ability_name, color=color, underlined=False, bold=False, italic=False)
    lore_lines.append(ability_name_tag)
    if ability.text is not None:
        lines = wrap_text(ability.text, 188, letter_widths)
        for line in lines:
            tag_line = tag_line_generator(text=f"  {line}", color=sub_color, underlined=False, bold=False, italic=True)
            lore_lines.append(tag_line)

    return lore_lines


def attack_line(attack, energy_type: dict, attack_cost_tag: list, lore_lines: list) -> list:
    header = []
    color = energy_type["main_color"]
    sub_color = energy_type["sub_color"]
    attack_name = f"* {attack.name} :  "
    header.append(tag_line_generator(text=attack_name, color=color, underlined=False, bold=False, italic=False))
    if attack.damage != "":
        attack_damage = f"{attack.damage} Damage"
        header.append(tag_line_generator(text=attack_damage, color=color, underlined=False, bold=True, italic=False))
    lore_lines.append(header)

    if attack.text is not None:
        lines = wrap_text(attack.text, 188, letter_widths)
        for line in lines:
            tag_line = tag_line_generator(text=f"  {line}", color=sub_color, underlined=False, bold=False, italic=True)
            lore_lines.append(tag_line)

    for line in attack_cost_tag:
        if len(line) > 0:
            lore_lines.append(line)

    return lore_lines


def flavor_text_lines(flavor_text: str, lore_lines: list) -> list:
    lines = wrap_text(flavor_text, 188, letter_widths)
    for line in lines:
        tag_line = tag_line_generator(text=f"  {line}", color="gray", underlined=False, bold=False, italic=True)
        lore_lines.append(tag_line)

    return lore_lines


def weakness_and_resistance(weaknesses: list, resistances: list,
                            energy_color: str, lore_lines: list, price: float) -> list:
    tag_line_list = []
    weakness_string = ""
    resistance_string = ""
    price_string = f'${price}'

    if weaknesses is not None:
        if len(weaknesses) > 1:
            weakness_string = " Weaknesses: "
        else:
            weakness_string = " Weakness: "
        tag_line = tag_line_generator(text=weakness_string, color=energy_color, underlined=False, bold=False,
                                      italic=False)
        tag_line_list.append(tag_line)

        for weakness in weaknesses:
            color = energy_types[weakness.type]["main_color"]
            symbol = '●   ' if weakness == weaknesses[-1] else '●'
            tag_line = tag_line_generator(text=symbol, color=color, underlined=False, bold=False, italic=False)
            tag_line_list.append(tag_line)

    if resistances is not None:
        if len(resistances) > 1:
            resistance_string = "Resistances: "
        else:
            resistance_string = "Resistance: "

        if weaknesses is None:
            resistance_string = " " + resistance_string

        tag_line = tag_line_generator(text=resistance_string, color=energy_color, underlined=False, bold=False,
                                      italic=False)
        tag_line_list.append(tag_line)

        for resistance in resistances:
            color = energy_types[resistance.type]["main_color"]
            tag_line = tag_line_generator(text="● ", color=color, underlined=False, bold=False, italic=False)
            tag_line_list.append(tag_line)

    # Spaces
    resistance_str = resistance_string + " ".join(["●" for _ in resistances]) if resistances else resistance_string
    spaces = weakness_resistance_spaces(weakness_string, resistance_str, price_string)

    tag_line = tag_line_generator(text=spaces, color=energy_color, underlined=False, bold=False, italic=False)
    tag_line_list.append(tag_line)

    # Price
    tag_line = tag_line_generator(text=price_string, color='#4caf50', underlined=False, bold=False, italic=False)
    tag_line_list.append(tag_line)

    lore_lines.append(tag_line_list)

    return lore_lines


def weakness_resistance_spaces(weakness_string: str, resistance_string: str, price_string: str) -> str:
    spaces = ""
    string = weakness_string + resistance_string + price_string
    width = sum(letter_widths.get(char, 0) for char in string)
    while width + 4.2 <= 188:
        spaces += " "
        width += + 4.2

    if len(weakness_string) > 1 and len(spaces) > 1:
        spaces = spaces[:-3]

    return spaces


def card_type_selector(card) -> str:
    pokemon_type = card.types[0]
    if len(card.types) > 1:
        if "Darkness" in card.types and "Metal" in card.types:
            if card.set_name == "Team Rocket Returns":
                pokemon_type = card.types[0]
            else:
                pokemon_type = card.types[1]
        else:
            pokemon_type = card.types[1]

    return pokemon_type


def subtype_line(subtypes: list[str], lore_lines: list) -> list:
    subtype_string = f"> {subtypes[0]}"
    tag_line = tag_line_generator(text=subtype_string, color="gray", underlined=False, bold=False, italic=False)
    lore_lines.append(tag_line)

    return lore_lines


def rules_line(rules: list[str], lore_lines: list) -> list:
    for rule in rules:
        lines = wrap_text(rule, 188, letter_widths)
        for line in lines:
            tag_line = tag_line_generator(text=f"  {line}", color="gray", underlined=False, bold=False, italic=True)
            lore_lines.append(tag_line)

    return lore_lines


def number_set_release_line(card, lore_lines: list) -> list:
    # Card number / printed total
    tag_line = []
    if card.rarity == "Trainer":
        card_number_text = f"~ {card.number}/{card.printed_total}  "
    else:
        card_number_text = f"~   {card.number}/{card.printed_total}  "
        if card.set_id == 'ex6' and int(card.number) > 99:
            card_number_text = f"~ {card.number}/{card.printed_total} "
    tag_string = tag_line_generator(text=card_number_text, color="white", underlined=False, bold=False, italic=False)
    tag_line.append(tag_string)
    # Set name
    set_name = sets[card.set_id]["name"]
    color = sets[card.set_id]["color"]
    tag_string = tag_line_generator(text=f"{set_name} ", color=color, underlined=False, bold=False, italic=False)
    tag_line.append(tag_string)
    # Release year
    if card.rarity != "Promo":
        release_date = datetime.datetime.strptime(card.release_date, "%Y/%m/%d")
        release_year = str(release_date.year)
        tag_string = tag_line_generator(text=release_year, color="white", underlined=False, bold=False, italic=False)
        tag_line.append(tag_string)
    # Append to lore list
    lore_lines.append(tag_line)

    return lore_lines


def symbol_tag_lines(name: list) -> list:
    special_tag_lines = []
    for item in name:
        if item in special_strings_dict:
            symbol = special_strings_dict[item]
            text = symbol["text"]
            color = symbol["color"]
            bold = symbol["bold"]
            italic = symbol["italic"]
            tag_line = headline_generator(text=text, color=color, underlined=False, bold=bold, italic=italic)
            special_tag_lines.append(tag_line)

    return special_tag_lines


def trainer_tag_line(name: list, trainer: str) -> tuple:
    predecessor = f"{name[0]} "
    if trainer == "Team":
        predecessor = f"{name[0]} {name[1]} "
    successor = " ".join(name)
    for trainer_name in trainer_names:
        successor = successor.replace(trainer_name, "")
    color = trainer_names[predecessor]
    predecessor_tag_line = headline_generator(text=predecessor, color=color, underlined=False, bold=False, italic=False)

    return predecessor_tag_line, successor


def rarity_symbol(rarity: str) -> dict:
    rarity_symbol = rarity_format[rarity]["symbol"]
    color = rarity_format[rarity]["color"]
    tag_line = headline_generator(text=rarity_symbol, color=color, underlined=False, bold=False, italic=False)

    return tag_line


def nbt_tags(card) -> list:
    nbt_tags_list = []
    card_name = card.name.replace(" Energy", "")
    # Add enchantment
    if card.rarity in ["Rare Holo", "Rare Secret", "Rare Holo EX", "Rare Holo Star"]:
        nbt_tags_list.append({"Enchantments": [{"id": "minecraft:infinity", "lvl": 1}]})
    if card.rarity != "Promo":
        card_nr = 32000 + Card_Data.static_poke_num_cntr
    else:
        card_nr = 64000 + Card_Data.static_poke_num_cntr
    if card_name in energy_types:
        if energy_types[card_name]["card_nr"] and card.rarity != "Rare Holo":
            card_nr = energy_types[card_name]["card_nr"]
    nbt_tags_list.append({"HideFlags": 97})
    nbt_tags_list.append({"CustomModelData": card_nr})
    nbt_tags_list.append({"map": card_nr})

    return nbt_tags_list


def format_header(card) -> list:
    energy_list = ["Fighting Energy", "Fire Energy", "Grass Energy", "Lightning Energy",
                   "Psychic Energy", "Water Energy"]
    name_tag_line = []
    if card.name in energy_list:
        tag_line = headline_generator(text=card.name, color="white", underlined=False, bold=False, italic=False)
        name_tag_line.append(tag_line)
        return name_tag_line

    special_tag_lines = None
    name = card.name.split()
    if len(name) > 1 and card.supertype == "Pokémon":
        predecessor_tag_line = None
        color = rarity_format[card.rarity]["name_color"]
        for string in name:
            if string in special_strings_dict:
                special_tag_lines = symbol_tag_lines(name)
                name.remove(string)
            if string + " " in trainer_names or string == "Team":
                predecessor_tag_line, successor = trainer_tag_line(name, string)
                name.remove(string)
        # Shining pokemon
        if special_tag_lines and special_tag_lines[0]["text"] == "Shining ":
            name_tag_line.append(special_tag_lines[0])
            special_tag_lines.remove(special_tag_lines[0])
        # Team name / trainer name
        if predecessor_tag_line:
            name_tag_line.append(predecessor_tag_line)
            successor_tag_line = headline_generator(text=successor, color=color, underlined=False, bold=True,
                                                    italic=False)
            name_tag_line.append(successor_tag_line)
        else:
            pokemon_name = copy.deepcopy(name)
            for special_string in special_strings_dict:
                if special_string in pokemon_name:
                    pokemon_name.remove(special_string)
            pokemon_name = " ".join(pokemon_name)
            pokemon_name_tag_line = headline_generator(text=pokemon_name, color=color, underlined=False, bold=True,
                                                       italic=False)
            name_tag_line.append(pokemon_name_tag_line)
        # Append ex, star, delta species tag lines
        if special_tag_lines:
            for tag_line in special_tag_lines:
                name_tag_line.append(tag_line)
    else:
        name = card.name
        color = rarity_format[card.rarity]["name_color"]
        tag_line = headline_generator(text=name, color=color, underlined=False, bold=True, italic=False)
        name_tag_line.append(tag_line)
    # Rarity
    rarity_tag_line = rarity_symbol(card.rarity)
    name_tag_line.append(rarity_tag_line)

    return name_tag_line


def format_pokemon_card(card) -> list:
    lore_lines = []
    pokemon_type = card_type_selector(card)
    type_color = energy_types[pokemon_type]["main_color"]
    # Evolution line
    lore_lines = evolution_line(card, type_color, lore_lines)
    lore_lines = seperator_line(lore_lines)
    # Abilities
    if card.abilities is not None:
        for ability in card.abilities:
            lore_lines = ability_line(ability, pokemon_type, lore_lines)
            lore_lines = seperator_line(lore_lines)
    # Attacks
    if card.attacks is not None:
        for attack in card.attacks:
            attack_cost_tag, energy_type = attack_cost_tag_line(attack)
            lore_lines = attack_line(attack, energy_type, attack_cost_tag, lore_lines)
            lore_lines = seperator_line(lore_lines)
    # Flavor text
    if card.flavor_text is not None:
        lore_lines = flavor_text_lines(card.flavor_text, lore_lines)
    # Weakness and resistance
    lore_lines = weakness_and_resistance(card.weaknesses, card.resistances, type_color, lore_lines, card.price)
    # Printed total, set, release year
    lore_lines = number_set_release_line(card, lore_lines)

    return lore_lines


def format_trainer_card(card) -> list:
    lore_lines = []
    # Subtypes
    if card.supertype == "Trainer" and card.subtypes is not None:
        lore_lines = subtype_line(card.subtypes, lore_lines)
    lore_lines = seperator_line(lore_lines)
    # Rules
    rules = card.rules
    if card.rules is not None:
        if card.name in special_rules:
            special_rules[card.name]["count"] += 1
            rules = special_rules[card.name]["rules"]
        else:
            special_rules[card.name] = {"count": 1}
            special_rules[card.name]["rules"] = rules
        lore_lines = rules_line(rules, lore_lines)
        lore_lines = seperator_line(lore_lines)
    # Printed total, set, release year
    lore_lines = number_set_release_line(card, lore_lines)

    return lore_lines


def format_energy_card(card) -> list:
    lore_lines = []
    if card.rules is not None:
        lore_lines = rules_line(card.rules, lore_lines)
        lore_lines = seperator_line(lore_lines)
        lore_lines = number_set_release_line(card, lore_lines)

    return lore_lines


def wrap_text(text, max_width, letter_widths):
    words = text.split()  # Split the text into individual words
    lines = []
    current_line = ""
    current_width = 0

    for word in words:
        width = sum(letter_widths.get(char, 0) for char in word)
        if current_width + width + len(current_line.split()) * 3 <= max_width:
            if current_line:
                current_line += " " + word
            else:
                current_line = word
            current_width += width
            current_width += 3
        else:
            lines.append(current_line)
            current_line = word
            current_width = width
            current_width += 3

    if current_line:
        lines.append(current_line)

    return lines


def evolution_line_width(evolution_string, max_health_width, hp) -> str:
    spaces = ""
    width = sum(letter_widths.get(char, 0) for char in evolution_string)
    hp_width = sum(letter_widths.get(char, 0) for char in hp) + sum(letter_widths.get(char, 0) for char in "HP")
    hp_width += len(hp) + len('HP')
    # for _ in chain(hp.strip(), "HP".strip()):
    #    hp_width += 1
    if width > max_health_width - hp_width:
        evolution_string = re.sub("Evolves", "Evls.", evolution_string)
        width = sum(letter_widths.get(char, 0) for char in evolution_string)
    current_width = width
    while current_width + 4 <= max_health_width:
        spaces = spaces + " "
        current_width = current_width + 4
    match = re.search('Basic', evolution_string)
    if not match:
        spaces += ' '

    return evolution_string + spaces


def seperator_line(lore_lines: list) -> list:
    lore_lines.append({"text": "--------------------------------", "color": "white", "italic": False})

    return lore_lines


class SetEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, set):
            return list(obj)
        return super(SetEncoder, self).default(obj)


class Card_Data:
    name: str
    supertype: str
    number: str
    hp: Optional[str]
    evolvesFrom: Optional[str]
    abilities: Optional[List[Ability]]
    attacks: Optional[List[Attack]]
    flavorText: Optional[str]
    rules: Optional[List[str]]
    rarity: Optional[str]
    types: Optional[List[str]]
    weaknesses: Optional[List[str]]
    resistances: Optional[List[str]]
    convertedRetreatCost: Optional[List[str]]
    set: Optional[List[str]]
    images: Optional[dict]
    subtypes: Optional[List[str]]

    static_poke_num_cntr = 0
    promo_poke_num_cntr = 0

    def __init__(self, card: Card, price: float) -> None:
        if card.rarity is not None:
            if card.rarity == "Promo":
                Card_Data.promo_poke_num_cntr += 1
                self.static_poke_num_cntr = Card_Data.promo_poke_num_cntr + 64000
            else:
                Card_Data.static_poke_num_cntr += 1
                self.static_poke_num_cntr = Card_Data.static_poke_num_cntr + 32000

        if card.name.replace(" Energy", "") in energy_types and card.rarity != 'Rare Holo':
            self.static_poke_num_cntr = energy_types[card.name.replace(" Energy", "")]['card_nr']

        self.name = card.name
        self.supertype = card.supertype
        self.number = card.number
        self.rarity = card.rarity
        self.rules = card.rules
        self.printed_total = card.set.printedTotal
        self.release_date = card.set.releaseDate
        self.set_name = card.set.name
        self.set_id = card.set.id
        self.images = {
            'large': card.images.large,
            'small': card.images.small
        }
        self.price = price

        if self.supertype != "Energy":
            self.hp = card.hp
            self.evolves_from = card.evolvesFrom
            self.abilities = card.abilities
            self.attacks = card.attacks
            self.flavor_text = card.flavorText
            self.types = card.types
            self.weaknesses = card.weaknesses
            self.resistances = card.resistances
            self.converted_retreat_cost = card.convertedRetreatCost
        if self.supertype == "Trainer":
            self.subtypes = card.subtypes

        self.set_name = {'function': 'set_name', 'name': []}
        self.set_lore = {'function': 'set_lore', 'lore': [], 'mode': 'append'}
        self.set_components = {'function': 'set_components', 'components': {
            'hide_additional_tooltip': {},
            'custom_model_data': self.static_poke_num_cntr,
            'map_id': self.static_poke_num_cntr
        }}
        if self.rarity in ["Rare Holo", "Rare Secret", "Rare Holo EX", "Rare Holo Star"]:
            self.set_components['components'].update({'enchantment_glint_override': True})
        if self.supertype == "Pokémon" and self.types is not None:
            self.set_components['components'].update(
                {'custom_data': {pokemon_type.lower(): 1 for pokemon_type in self.types}})
        else:
            self.set_components['components'].update({'custom_data': {self.supertype.lower(): 1}})

        self.functions = [self.set_components, self.set_name, self.set_lore]

    def generate_components(self):
        lore_lines = []
        if self.supertype == "Pokémon":
            lore_lines = format_pokemon_card(self)
        elif self.supertype in ["Trainer", "Energy"] and self.name not in basic_energy_list:
            lore_lines = format_trainer_card(self)

        name_tag_line_list = format_header(self)  # Append name and lore
        self.set_name['name'] = name_tag_line_list
        self.set_lore['lore'] = lore_lines

        if self.supertype in ["Trainer", "Energy"]:  # Duplicate cards
            name_rarity = self.name + (f' {self.rarity}' if self.rarity else '')
            if name_rarity not in energy_trainer_cards:
                energy_trainer_cards[name_rarity] = self.functions
            else:
                self.functions = energy_trainer_cards[name_rarity]
