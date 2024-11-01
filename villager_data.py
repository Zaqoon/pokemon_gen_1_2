import re
import json

patterns = {
    "evolution_search_patterns": [
        r"> Evolves from\s+([^\"]+)",
        r"> Evls. from\s+([^\"]+)"
    ]
}

predicate_list = ["Blaine's ", "Brock's ", "Erika's ", "Lt. Surge's ", "Misty's ", "Rocket's ", "Sabrina's ", "Giovanni's ", "Koga's ", "Shining ",
                  "Team Aqua's ", "Team Magma's ", "Holon's ", "Dark "]


def fix_json(components):
    components = json.dumps(components)
    components = re.sub(r'\["\'{', r"'[{", components)
    components = re.sub(r"}'\"]", r"}]'", components)

    components = re.sub(r'\["\'\[{', r"['[{", components)
    components = re.sub(r'}]\'"]', r"}]']", components)

    components = re.sub(r"'text': '((?:[^'\\]|\\.)*)'", r'"text":"\1"', components)
    components = re.sub(r"'color': '((?:[^'\\]|\\.)*)'", r'"color":"\1"', components)
    components = re.sub(r"'bold': ((?:[^'\\]|\\.)*)", r'"bold":\1', components)
    components = re.sub(r"'italic': ((?:[^'\\]|\\.)*)", r'"italic":\1', components)
    components = re.sub(r"'underlined': ((?:[^'\\]|\\.)*)", r'"underlined":\1', components)
    components = re.sub(r"'text': \\\"(.*?)\\\"", r'"text":"\1"', components)
    components = re.sub(r"(\"text\":\s*\"(.*?)\")", lambda m: m.group(1).replace("'", "\\'"), components)
    components = re.sub(r'"custom_data":\s*{([^}]+)}',
                    lambda m: re.sub(r'(\s*"[^"]+"\s*:\s*)1', r'\g<1>1b', m.group(0)),
                    components)

    return components


def extract_pokemon_name(functions:list) -> str:
    pokemon_name = ''
    for name in functions[1]['name']:
        pokemon_name += name['text']
        if name['text'] in predicate_list:
            continue
        else:
            return pokemon_name


def extract_evolution_name(functions:list) -> str:
    evolution_line = functions[2]['lore'][0][0]['text']
    for searh_pattern in patterns["evolution_search_patterns"]:
        evolution_name = re.findall(searh_pattern, evolution_line)
        if len(evolution_name) > 0:
            pokemon_name = evolution_name[0].strip()
            pokemon_name = repr(pokemon_name)
            pokemon_name = pokemon_name[1:-1]
            return pokemon_name
    
    return 'Basic'


def generate_name(elements:list) -> str:
    return f'{elements}'


def generate_lore(elements:list) -> list:
    string = ""
    for line in elements:
        if string != "":
            string += ","
        string += "'" + str(line) + "'"
    
    return [string]


def trainer_weights(self) -> int:
    multiplier = {
        'Common': 3,
        'Uncommon': 2,
        'Rare': 1
    }
    weight = self.weight * multiplier[self.rarity]
    
    return weight


def unescape_string(escaped_string: str) -> str:
    unescaped_string = escaped_string.encode().decode('unicode_escape')
    unescaped_string = unescaped_string.replace('\\,', ',')
    return unescaped_string


class VillagerData:
    def __init__(self, data) -> None:
        self.weight = data['weight']
        self.functions = data['functions']
        self.name = extract_pokemon_name(self.functions)
        self.evolves_from = extract_evolution_name(self.functions)
        self.types = data['types']
        self.set = data['set']
        self.rarity = data['rarity']
        self.custom_name = generate_name(self.functions[1]['name'])
        self.lore = generate_lore(self.functions[2]['lore'])
        self.custom_model_data = self.functions[0]['components']['custom_model_data']
        self.map_id = self.functions[0]['components']['map_id']
        self.custom_data = {pokemon_type: 1 for pokemon_type in self.functions[0]['components']['custom_data']}
        self.components = {
            'hide_additional_tooltip': {},
            'custom_model_data': self.custom_model_data,
            'map_id': self.map_id,
            'custom_data': self.custom_data,
            'custom_name': self.custom_name,
            'lore': self.lore
        }
        self.components = fix_json(self.components)


class TrainerData:
    def __init__(self, data) -> None:
        self.weight = data['weight']
        self.functions = data['functions']
        self.name = extract_pokemon_name(self.functions)
        self.set = data['set']
        self.rarity = data['rarity']
        self.custom_name = generate_name(self.functions[1]['name'])
        self.lore = generate_lore(self.functions[2]['lore'])
        self.custom_model_data = self.functions[0]['components']['custom_model_data']
        self.map_id = self.functions[0]['components']['map_id']
        self.custom_data = {cd: 1 for cd in self.functions[0]['components']['custom_data']}
        self.components = {
            'hide_additional_tooltip': {},
            'custom_model_data': self.custom_model_data,
            'map_id': self.map_id,
            'custom_data': self.custom_data,
            'custom_name': self.custom_name,
            'lore': self.lore
        }
        self.components = fix_json(self.components)
        self.weight = trainer_weights(self)


class EnergyData:
    def __init__(self, data) -> None:
        self.functions = data['functions']
        self.rarity = data['rarity']
        self.name = extract_pokemon_name(self.functions)
        self.custom_name = generate_name(self.functions[1]['name'])
        self.lore = generate_lore(self.functions[2]['lore'])
        self.custom_model_data = self.functions[0]['components']['custom_model_data']
        self.map_id = self.functions[0]['components']['map_id']
        self.components = {
            'hide_additional_tooltip': {},
            'custom_model_data': self.custom_model_data,
            'map_id': self.map_id,
            'custom_data': {'energy': 1},
            'custom_name': self.custom_name,
            'lore': self.lore
        }
        self.components = fix_json(self.components)


class SetCount:
    def __init__(self, data: list) -> None:
        energy_types = ['Grass', 'Fire', 'Water', 'Fighting', 'Psychic', 'Lightning', 'Darkness', 'Metal']
        self.set_count = {
            energy_type: {
                'Common': 0,
                'Uncommon': 0,
                'Rare': 0
            }
            for energy_type in energy_types
        }
        for card in data:
            if card.rarity in self.set_count:
                self.set_count[card.rarity] += 1
