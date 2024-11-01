import os
import random
import re
import json
import shutil
from typing import List

from poke_data import sets
from poke_data import generations
from poke_data import energy_types

from villager_data import VillagerData
from villager_data import TrainerData
from villager_data import EnergyData
from villager_data import SetCount


sets = {key: {**value, "abbreviation": key} for key, value in sets.items()}

pokemon_data = {
    gen: {energy_type: {rarity: [] for rarity in ['Common', 'Uncommon', 'Rare']} for energy_type in energy_types}
    for gen in generations
}

trainer_data = {
    'supporter': [],
    'item': [],
    'stadium': [],
    'tool': [],
    'technical_machine': [],
    'gen_1': [],
    'gen_2': []
}

energy_data = {}

data_strings = {
    "data_modify_dict": "execute in the_nether as @p[x=-6363,y=98,z=13745,limit=1,sort=nearest] at @s run "
                        "data modify entity @e[type=villager,limit=1,sort=nearest,"
                        "nbt={VillagerData:{type:\"minecraft:%s\",profession:\"minecraft:%s\"}}] "
                        "Offers.Recipes append value ",
    "card_dict": '''{id: "minecraft:filled_map",count: %s,components: %s}''',
    "rare_card_dict": '''{id: "minecraft:carrot_on_a_stick",count: %s,components: %s}'''
}

deck_color = {"Grass": "green", "Fire": "red", "Water": "blue", "Fighting": "brown","Lightning": "yellow",
              "Psychic": "dark_purple", "Colorless": "gray", "Metal": "dark_gray", "Darkness": "dark_aqua"}

weights = [sets[key]["weight"] for key in sets]

predicate_list = ["Blaine's ", "Brock's ", "Erika's ", "Lt. Surge's ", "Misty's ", "Rocket's ",
                  "Sabrina's ", "Giovanni's ", "Koga's ", "Shining ",
                  "Team Aqua's ", "Team Magma's ", "Holon's ", "Dark "]


def populate_villager_data() -> None:
    for set in sets:
        if not sets[set]['deck_set']:
            continue
        gen = None
        for gen, set_names in generations.items():
            if sets[set]['abbreviation'] in set_names:
                gen = gen
                break
        for rarity in ['Common', 'Uncommon', 'Rare']:
            with open(f'{gen}/loot_tables/{set}/{rarity.lower()}.json', 'r') as file:
                loot_table = json.load(file)
            for entry in loot_table['pools'][0]['entries']:
                functions = entry['functions']
                custom_data = [pokemon_type for pokemon_type in functions[0]['components']['custom_data']]
                if 'trainer' in custom_data:
                    data = {
                        'functions': functions,
                        'set': set,
                        'rarity': rarity,
                        'weight': sets[set]['weight']
                    }
                    card_data = TrainerData(data)
                    trainer_data[gen].append(card_data)
                    for cd in card_data.custom_data:
                        if cd != 'trainer':
                            trainer_data[cd].append(card_data)
                    continue
                elif 'energy' in custom_data:
                    continue
                data = {'weight': sets[set]['weight'],
                        'functions': functions,
                        'types': custom_data,
                        'set': set,
                        'rarity': rarity
                        }
                card_data = VillagerData(data)
                for pokemon_type in custom_data:
                    card_type = pokemon_type.capitalize()
                    pokemon_data[gen][card_type][rarity].append(card_data)


def count_cards() -> dict:
    set_data = {}
    for gen in generations:
        rarities = ['Common', 'Uncommon', 'Rare']
        combined_list = [
            card_list
            for energy_type in energy_types
            for rarity in rarities
            for card_list in pokemon_data[gen][energy_type][rarity]
        ]

        set_data[gen] = SetCount(combined_list)

    return set_data


def populate_energy_cards() -> None:
    entry_numbers = {
        'energy': {
            'path': 'gen_1/loot_tables/base1/energy.json',
            'index': [0, 1, 2, 3, 4, 5]
        },
        'rare': {
            'path': 'gen_2/loot_tables/ecard1/rare.json',
            'index': [38, 39]
        }
    }

    for rarity in entry_numbers:
        with open(entry_numbers[rarity]['path'], 'r') as file:
            loot_table = json.load(file)
        for entry_num in entry_numbers[rarity]['index']:
            entry = loot_table['pools'][0]['entries'][entry_num]
            functions = entry['functions']
            data = {
                'functions': functions,
                'rarity': rarity
            }
            card_data = EnergyData(data)
            energy_type = card_data.name.replace(' Energy', '')
            energy_data.update({energy_type: card_data})


def sort_card_weights() -> dict:
    rarities = ['Common', 'Uncommon', 'Rare']
    card_weights = {
        gen: {
            pokemon_type: {rarity: [] for rarity in rarities}
            for pokemon_type in pokemon_data[gen]
        }
        for gen in pokemon_data
    }
    for gen in card_weights:
        for pokemon_type in energy_types:
            for rarity in rarities:
                villager_data_weights = [villager_data.weight for villager_data in pokemon_data[gen][pokemon_type][rarity]]
                card_weights[gen][pokemon_type][rarity] = villager_data_weights

    return card_weights


def sort_trainer_weights() -> dict:
    card_weights = {subtype: [] for subtype in trainer_data}
    for gen in generations:
        card_weights[gen] = [trainer.weight for trainer in trainer_data[gen]]

    return card_weights


def add_pokemon_cards(evolution_names:List[str], pokemon_type:str, sub_type:str, deck_dict:str, rarity:str, gen:str) -> tuple:
    card_amount = {
        "Common": {
            "Unique Cards": 5,
            "Stack Min": 2,
            "Stack Max": 4
        },
        "Uncommon": {
            "Unique Cards": 3,
            "Stack Min": 1,
            "Stack Max": 2
        },
        "Rare": {
            "Unique Cards": 1,
            "Stack Min": 2,
            "Stack Max": 2
        },
        "Trainer": {
            "Unique Cards": 5,
            "Stack Min": 2,
            "Stack Max": 4
        }
    }
    card_list = []
    added_cards = 0

    weight_dict = {
        key: card_weights[gen][key][rarity][:]
        for key in [pokemon_type, sub_type]
    }

    card_type_count = {
        key: {
            'total': 0,
            'basic': 0,
            'evolution': 0
        }
        for key in [pokemon_type, sub_type]
    }

    if rarity != 'Common':
        for poke_type in [pokemon_type, sub_type]:
            for card in pokemon_data[gen][poke_type][rarity]:
                if card.evolves_from == 'Basic':
                    card_type_count[poke_type]['basic'] += 1
                    card_type_count[poke_type]['total'] += 1
                elif card.evolves_from in evolution_names:
                    card_type_count[poke_type]['evolution'] += 1
                    card_type_count[poke_type]['total'] += 1

        for poke_type in [pokemon_type, sub_type]:
            basic_count = card_type_count[poke_type]['basic']
            evolution_count = card_type_count[poke_type]['evolution']
            for i, card in enumerate(pokemon_data[gen][poke_type][rarity]):
                if card.evolves_from not in evolution_names and card.evolves_from != 'Basic':
                    weight_dict[poke_type][i] = 0
                elif card.evolves_from in evolution_names and card.evolves_from != 'Basic':
                    weight_dict[poke_type][i] *= (8 * basic_count) / evolution_count

    total_weight = {
        energy_type: sum(weight_dict[energy_type])
        for energy_type in [pokemon_type, sub_type]
    }

    weight_odds = {
        pokemon_type: 0.6,
        sub_type:     0.4
    }

    multiplier = total_weight[pokemon_type] / total_weight[sub_type]

    # Make the total sub_type weight == the total pokemon_type weight
    weight_dict[sub_type] = [weight * multiplier for weight in weight_dict[sub_type]]

    # Adjust weights to match the odds
    for poke_type in weight_odds:
        multiplier = weight_odds[poke_type]
        weight_odds[poke_type] = [weight * multiplier for weight in weight_dict[poke_type]]

    pool = [card for key in [pokemon_type, sub_type] for card in pokemon_data[gen][key][rarity]]

    weight_list = [weight for sublist in weight_dict.values() for weight in sublist]

    while added_cards < card_amount[rarity]['Unique Cards']:
        card = random.choices(pool, weights=weight_list, k=1)[0]

        card_index = pool.index(card)
        weight_list[card_index] = 0

        min = card_amount[rarity]['Stack Min']
        max = card_amount[rarity]['Stack Max']
        components = fix_json(card.components)
     
        deck_dict = add_to_deck(deck_dict, min=min, max=max, components=components, item_type='card_dict')
        evolution_names.append(card.name)
        card_list.append(card)
        if card.evolves_from in evolution_names:
            evolution_names.remove(card.evolves_from)
            for i, card in enumerate(pokemon_data[gen][pokemon_type][rarity]):
                if card.evolves_from not in evolution_names and card.evolves_from != 'Basic':
                    weight_list[i] = 0
        added_cards += 1

    return deck_dict, evolution_names


def unescape_string(escaped_string: str) -> str:
    unescaped_string = escaped_string.encode().decode('unicode_escape')
    unescaped_string = unescaped_string.replace('\\,', ',')
    return unescaped_string


def add_to_deck(deck_dict:dict, min:int, max:int, components:str, item_type:str) -> dict:
    stack_amount = random.randrange(min, max + 1)
    card_dict = data_strings[item_type] % (stack_amount, components)
    deck_dict["sell"]["components"]["bundle_contents"].append(card_dict)

    return deck_dict


def get_trainer_cards(deck_dict: dict, gen: str) -> dict:
    weights = trainer_weights.copy()

    for i in range(1, 5):
        # subtype = subtype_selector[i]
        random_card = random.choices(trainer_data[gen], weights=weights[gen])[0]
        card_index = trainer_data[gen].index(random_card)
        weights[card_index] = 0
        components = random_card.components
        components = fix_json(components)
        deck_dict = add_to_deck(deck_dict, min=2, max=4, components=components, item_type="card_dict")

    return deck_dict


def energy_cards(main_type, sub_type, deck_dict) -> dict:
    energies = []

    def random_energy(energies:List[str]) -> str:
        if not energies:
            energies = [energy for energy in energy_data if energy not in ['Darkness', 'Metal', main_type, sub_type]]
        energy = energies.pop(random.randint(0, len(energies) - 1))
        
        return energy

    if sub_type == 'Colorless':
        sub_type = random_energy(energies)

    energy_dict = {
        "Grass": {
            "energy_entry": 'Grass',
            "type_sub_entry": sub_type,
            "color": "#4CAF50"
        },
        "Fire": {
            "energy_entry": 'Fire',
            "type_sub_entry": sub_type,
            "color": "#E53935"
        },
        "Water": {
            "energy_entry": 'Water',
            "type_sub_entry": sub_type,
            "color": "#2979FF"
        },
        "Fighting": {
            "energy_entry": 'Fighting',
            "type_sub_entry": sub_type,
            "color": "#8D6E63"
        },
        "Lightning": {
            "energy_entry": 'Lightning',
            "type_sub_entry": sub_type,
            "color": "#FDD835"
        },
        "Psychic": {
            "energy_entry": 'Psychic',
            "type_sub_entry": sub_type,
            "color": "#BA68C8"
        },
        "Colorless": {
            "energy_entry": sub_type,
            "type_sub_entry": random_energy(energies),
            "color": "#003f3f"
        },
        "Darkness": {
            "energy_entry": 'Darkness',
            "type_sub_entry": sub_type,
            "color": "#003f3f"
        },
        "Metal": {
            "energy_entry": 'Metal',
            "type_sub_entry": sub_type,
            "color": "#C0C0C0"
        }
    }

    stack_dict = {0: {'min': 15, 'max': 17}, 1: {'min': 7, 'max': 9}}
    for i in range(0, 2):
        if i == 0:
            energy_entry = energy_dict[main_type]['energy_entry']
            energy = energy_data[energy_entry]
        else:
            energy_entry = energy_dict[main_type]["type_sub_entry"]
            energy = energy_data[energy_entry]
        if main_type in ["Darkness", "Metal"] and i == 0:
            stack_min = 3
            stack_max = 5
        else:
            stack_min = stack_dict[i]['min']
            stack_max = stack_dict[i]['max']

        components = energy.components
        components = fix_json(components)
        deck_dict = add_to_deck(deck_dict, stack_min, stack_max, components, "card_dict")

    return deck_dict


def deck(deck_amount: int, gen: str) -> dict:
    decks = {}
    for i in range(1, deck_amount + 1):
        decks[f"Deck{i}"] = None

    custom_model_data_dict = {"Grass": 101, "Fire": 102, "Water": 103, "Fighting": 5, "Lightning": 14, "Psychic": 9,
                              "Colorless": 16, "Darkness": 1, "Metal": 3}
    deck_types = ["Grass", "Fire", "Water", "Fighting", "Lightning", "Psychic", "Colorless"]

    deck_weight = {"Grass": 300, "Fire": 300, "Water": 300, "Fighting": 150,
                   "Lightning": 150, "Psychic": 150, "Colorless": 150}

    type_hex = {"Grass": "#4CAF50", "Fire": "#E53935", "Water": "#2979FF", "Fighting": "#8D6E63",
                "Lightning": "#FDD835", "Psychic": "#BA68C8",
                "Colorless": "gray", "Darkness": "#003f3f", "Metal": "#C0C0C0"}

    sub_deck_type = deck_types[:]
    sub_deck_weight = deck_weight.copy()

    not_compatible = ['Fighting', 'Lightning']

    while decks[f"Deck{deck_amount}"] is None:
        deck_type = random.choices(deck_types, weights=list(deck_weight.values()))[0]
        deck_types.remove(deck_type)

        random_type_pool = sub_deck_type[:]
        temp_sub_weight = sub_deck_weight.copy()
        if deck_type in random_type_pool:
            random_type_pool.remove(deck_type)
            del temp_sub_weight[deck_type]

        sub_type = random.choices(random_type_pool, weights=list(temp_sub_weight.values()))[0]
        sub_deck_type.remove(sub_type)

        del deck_weight[deck_type]
        del sub_deck_weight[sub_type]

        if gen == 'gen_1' and deck_type in not_compatible and sub_type in not_compatible:
            continue

        deck_dict = {
            "maxUses": 1,
            "buy": {
                "id": "minecraft:emerald",
                "count": 1,
                "components": {
                    "minecraft:custom_name": '{"text":"Sapphire","italic":false,"color":"aqua"}',
                    "custom_model_data": 1,
                    "custom_data": {"sapphire": "1b"}}},
            "sell": {
                "id": "minecraft:bundle",
                "count": 1,
                "components": {
                    "custom_name": f'{{"bold":true,"color":"{type_hex[deck_type]}",'
                                   f'"italic":false,"text":"{deck_type} Deck"}}',
                    "lore": f'[{{"italic":false,"text":"Generation {gen.replace("gen_","")}"}}',
                    "custom_model_data": custom_model_data_dict[deck_type],
                    "bundle_contents": []
                }
            }
        }
        evolution_names = []
        # rarity, evolution_names, deck_type, deck_dict
        for rarity in ["Common", "Uncommon", "Rare"]:
            deck_dict, evolution_names = add_pokemon_cards(evolution_names, deck_type, sub_type, deck_dict, rarity, gen)

        gen_string = gen.replace('_', '')
        rare_card_string = f"{{\"custom_name\":'{{\"text\":\"Holographic {deck_type} Card\",\"color\":\"aqua\",\"italic\":false}}',\"lore\":['{{\"text\":\"Right click to reveal card.\"}}'],\"custom_model_data\":1,\"enchantment_glint_override\":true,\"custom_data\":{{{deck_type.lower()}_rares_{gen_string}:1b}}}}"
        deck_dict = add_to_deck(deck_dict, 1, 1, rare_card_string, "rare_card_dict")
        deck_dict = get_trainer_cards(deck_dict, gen)
        deck_dict = energy_cards(deck_type, sub_type, deck_dict)
        deck_dict = fix_dict(deck_dict)

        for deck in decks:
            if decks[deck] is None:
                decks[deck] = deck_dict
                break

    return decks


def promo(gen: str) -> str:
    biome_type = {
        'gen_1': 'swamp',
        'gen_2': 'savanna'
    }
    promo_dict = """{maxUses:9,buy:{id:"minecraft:emerald",count:1,components:{"minecraft:custom_name":\
    '{"color":"light_purple","italic":false,"text":"Star"}',"minecraft:custom_model_data":4,"minecraft:custom_data":\
    {redstar:1b}}},sell:{id:"minecraft:carrot_on_a_stick",count:1,components:{"minecraft:custom_name":\
    '{"bold":true,"italic":false,"text":"Promo Pack"}',"minecraft:lore":['{"color":"#9fd0e0","italic":false,"text":\
    "Wizards Black Star Promos"}','{"text":"July 1999 - March 2003","color":"dark_purple","italic":true}'],\
    "minecraft:custom_model_data":10,"minecraft:custom_data":{basep:1}}}}"""

    return data_strings["data_modify_dict"] % (biome_type[gen], "cleric") + promo_dict


def booster(total_boosters:int, gen: str) -> List[str]:
    trade_dict = """{maxUses:%s,buy:{id:"minecraft:emerald",count:1,components:{"minecraft:custom_name":\
    '{"color":"yellow","italic":false,"text":"Ruby"}',"minecraft:custom_model_data":2,"minecraft:custom_data":\
    {ruby:1b}}},sell:{id:"minecraft:carrot_on_a_stick",count:1,components:{"minecraft:custom_name":\
    '{"bold":true,"italic":false,"text":"Booster Pack"}',"minecraft:lore":['{"text":"%s","color":"%s","italic":false}',\
    '{"text":"%s","color":"dark_purple","italic":true}'],"minecraft:custom_model_data":%s,\
    "minecraft:custom_data":{%s:1}}}}"""

    biome_type = {
        'gen_1': 'swamp',
        'gen_2': 'savanna'
    }

    trades = []
    exclude_set_cmd = []
    selected_sets = {}
    booster_list = [b for b in sets.keys() if b in generations[gen]]
    booster_weight_list = [w for w in [sets[set_name]['weight'] for set_name in sets if set_name in generations[gen]]]

    while len(selected_sets) < total_boosters:
        random_set_key = random.choices(booster_list, weights=booster_weight_list, k=1)[0]
        random_set = sets[random_set_key]
        index = booster_list.index(random_set_key)
        booster_list.pop(index)  # Remove booster from list to avoid duplicates
        booster_weight_list.pop(index)  # Remove weight from list to avoid duplicates
        custom_model_data_list = random_set["custom_model_data"]
        available_custom_model_data = [item for item in custom_model_data_list if item not in exclude_set_cmd]
        custom_model_data = random.choice(available_custom_model_data)
        exclude_set_cmd.append(custom_model_data)
        selected_sets[custom_model_data] = random_set
    sorted_selected_sets = dict(sorted(selected_sets.items()))
    for cmd, ss in sorted_selected_sets.items():
        trade_str = trade_dict % (ss["max_uses"], ss["name"], ss["color"], ss["date"], cmd, ss["abbreviation"])
        trade_str = data_strings["data_modify_dict"] % (biome_type[gen], "cleric") + trade_str
        trade_str = trade_str.replace("\n", "").replace("    ", "")
        trades.append(trade_str)
    
    return trades


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


def fix_dict(deck_dict):
    # Convert deckDict to JSON string
    deckDictString = json.dumps(deck_dict)

    unquote = re.sub(r"\"maxUses\"", r"maxUses", deckDictString)
    unquote = re.sub(r"\"buy\"", r"buy", unquote)
    unquote = re.sub(r"\"id\"", r"id", unquote)
    unquote = re.sub(r"\"count\"", r"count", unquote)
    unquote = re.sub(r"\"ruby\"", r"ruby", unquote)
    unquote = re.sub(r"\"sapphire\"", r"sapphire", unquote)
    unquote = re.sub(r"\"1b\"", r"1b", unquote)
    unquote = re.sub(r"\"display\"", r"display", unquote)
    unquote = re.sub(r"\"tag\"", r"tag", unquote)
    unquote = re.sub(r"\"sell\"", r"sell", unquote)
    unquote = re.sub(r"\"CustomModelData\"", r"CustomModelData", unquote)
    unquote = re.sub(r"\"Items\"", r"Items", unquote)
    unquote = re.sub(r"\"Name\": \"\{\\\"text\\\":\\\"Sapphire\\\",\\\"italic\\\":false,\\\"color\\\":\\\"aqua\\\"\}\"", r"Name: '{\"text\":\"Sapphire\",\"italic\":false,\"color\":\"aqua\"}'", unquote)
    unquote = re.sub(r"\"Name\": \"\{\\\"text\\\":\\\"Ruby\\\",\\\"italic\\\":false,\\\"color\\\":\\\"aqua\\\"\}\"", r"Name: '{\"text\":\"Ruby\",\"italic\":false,\"color\":\"yellow\"}'", unquote)
    unquote = re.sub(r"\"Name\": \"\{\\\"text\\\":\\\"(.*?) Deck\\\",\\\"color\\\":\\\"(.*?)\\\",\\\"italic\\\":false\}\"",lambda match: f"Name: '{{\"text\":\"{match.group(1)} Deck\",\"color\":\"{match.group(2)}\",\"italic\":false}}'",unquote)
    unquote = re.sub(r"}\", \"{", r"},{", unquote)

    unquote = re.sub(r"\"components\"", r"components", unquote)
    unquote = re.sub(r"\"count\"", r"count", unquote)


    # Remove backslashes before the separators (',')
    deckDictString = unescape_string(unquote)
    escaped_string = deckDictString.encode('unicode_escape').decode()
    escaped_string = re.sub(r"([a-zA-Z])'", r"\1\\'", escaped_string)
    escaped_string = re.sub(r"}}\"]}}}", r"}}]}}}", escaped_string)
    escaped_string = re.sub(r"\[\"{id:", r"[{id:", escaped_string)
    escaped_string = re.sub(r"\\\\'", r"\\'", escaped_string)

    escaped_string = escaped_string.replace('"{"', '\'{"')
    escaped_string = escaped_string.replace('"}"', '"}\'')
    escaped_string = escaped_string.replace('"[{"', '\'[{"')
    escaped_string = escaped_string.replace('}]"', "}]'")
    escaped_string = escaped_string.replace('"lore": \'[{', '"lore": [\'{')
    escaped_string = escaped_string.replace('"lore": [""]', '"lore": []')
    escaped_string = escaped_string.replace(':True', ':true')
    escaped_string = escaped_string.replace(':False', ':false')
    escaped_string = escaped_string.replace(' 1"}\', "custom_model_data"', ' 1"}\'], "custom_model_data"')
    escaped_string = escaped_string.replace(' 2"}\', "custom_model_data"', ' 2"}\'], "custom_model_data"')

    return escaped_string


def construct_deck_files(total_files, total_decks, gen) -> None:
    total_files += 1
    gen_string = gen.replace('_', '')
    paths = [f'{gen}/{gen_string}_decks/function/decks1']
    for i in range(1, total_decks + 1):
        base_path = paths[0][:-1]
        new_path = base_path + f"{+ i}"
        if new_path not in paths:
            paths.append(new_path)
    for path in paths:
        if os.path.exists(path):
            shutil.rmtree(path)
        os.makedirs(path)

    biome_type = {
        'gen_1': 'swamp',
        'gen_2': 'savanna'
    }

    for i in range(1, total_files):
        print(f"Creating decks for set {i}")
        decks = deck(total_decks, gen)
        gen_string = gen.replace('_', '')
    
        link_template = (f"execute in the_nether as @p[x=-6363,y=90,z=13745,limit=1,sort=nearest]"
                         f" run function {gen_string}_decks:decks%s/")
        links = []
        for index in range(1, total_decks):
            links.append(link_template % int(index + 1))

        for n, path in enumerate(paths):
            deck_name = "Deck" + str(n + 1)
            file_path = path + f"/{i}"
            file_path = file_path + ".mcfunction"
            with open(file_path, "w") as file:
                file.write(data_strings["data_modify_dict"] % (biome_type[gen], "cartographer") + decks[deck_name] + "\n")
                if n < len(paths) - 1:
                    file.write(links[n] + str(i))
            print(f"    Created deck {n + 1}")
    
    replace_villager_trades(total_files, profession='cartographer', gen=gen)


def construct_booster_files(total_files, booster_amount, gen) -> None:
    total_files += 1
    gen_string = gen.replace('_', '')
    directory = f'{gen}/{gen_string}_boosters/function'
    if os.path.exists(directory):
        shutil.rmtree(directory)
    os.makedirs(directory)
    
    for i in range(1, total_files):
        promos = promo(gen)
        boosters = booster(booster_amount, gen)

        path = f'{directory}/{i}.mcfunction'

        with open(path, 'w') as file:
            file.write(promos + '\n')
            for b in boosters:
                file.write(b + '\n')
        print(f"Successfully created booster file {i}")
    
    replace_villager_trades(total_files, profession='cleric', gen=gen)


def replace_villager_trades(num_files:int, profession:str, gen:str) -> None:
    profession_dict = {
        'cleric': 'boosters',
        'cartographer': 'decks'
    }
    biome_dict = {
        'gen_1': 'swamp',
        'gen_2': 'savanna'
    }
    biome = biome_dict[gen]

    function_dict = {
        'min': 'scoreboard players set $min random 1',
        'max': f'scoreboard players set $max random {num_files - 1}',
        'function': 'function random:uniform',
        'execute': f'execute in the_nether as @p[x=-6363,y=90,z=13745,limit=1,sort=nearest] '
                   f'run data modify entity @e[type=villager,limit=1,sort=nearest,'
                   f'nbt={{VillagerData:{{type:"minecraft:{biome}", profession:"minecraft:{profession}"}}}}] '
                   f'Offers.Recipes set value []'
    }

    gen_string = gen.replace('_', '')
    function_path = f"{gen_string}_{profession_dict[profession]}:"
    path = f"{gen}/functions/replace_villager_{profession_dict[profession]}_{gen_string}.mcfunction"
    if not os.path.exists(f'{gen}/functions'):
        os.makedirs(f'{gen}/functions')
    with open(path, 'w') as file:
        for function in function_dict.values():
            file.write(function + '\n')
        file.write('\n')
        for n in range(1, num_files):
            function_path_dict = {'cartographer': f'decks1/{n}', 'cleric': str(n)}
            function_path_num = function_path + function_path_dict[profession]
            line = f'execute if score $out random matches {n} run function {function_path_num}'
            file.write(line + '\n')


if __name__ == "__main__":
    for gen in ['gen_1', 'gen_2']:
        gen_String = gen.replace('_', '')
        directories = [
            f'{gen}/{gen_String}_decks',
            f'{gen}/{gen_String}_boosters'
        ]
        for directory in directories:
            if os.path.exists(directory):
                shutil.rmtree(directory)
    
    # Populate pokemon cards
    populate_villager_data()
    populate_energy_cards()

    # Assign weight to cards
    card_weights = sort_card_weights()
    trainer_weights = sort_trainer_weights()

    for gen in ['gen_1', 'gen_2']:
        construct_deck_files(200, 4, gen)
        construct_booster_files(200, 4, gen)
