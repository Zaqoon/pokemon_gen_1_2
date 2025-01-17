import os
import shutil
from typing import List
from poke_data import card_amount
from poke_data import generations
from poke_data import energy_types
from fetch_api_data import target_set_list


pull_rate_dict = card_amount

booster_score = {
    "base1": 2100, "base2": 2200, "base3": 2300, "base4": 2400, "base5": 2500,
    "gym1": 2600, "gym2": 2700, "neo1": 2800, "neo2": 2900, "neo3": 3000,
    "neo4": 3100, "base6": 3200, "ecard1": 3300, "ecard2": 3400, "ecard3": 3500,
    "basep": 3600
}

template = {
    "set_score": "scoreboard players set @s booster %s",
    "add_score": "scoreboard players add @a[scores={booster=%s}] booster 1",
    "spawn_loot_table": "execute as @a[scores={booster=%s}] at @s run loot spawn ~ ~ ~ loot tcg:%s/%s",
    "playsound": "execute as @s run playsound pokesound.booster_pack_open master @s ~ ~ ~ 10 1",
    "clear_booster": "execute as @s if items entity @s weapon.* minecraft:carrot_on_a_stick[custom_data={%s}] run clear @s minecraft:carrot_on_a_stick[custom_data={%s}] 1",
    "reset_score": "scoreboard players reset @a[scores={booster=%s}] booster",
    "que_next_card": "execute as @a[scores={booster=%s}] at @s run schedule function %s:%s 4t",
    "flip_card": "execute as @a[scores={right_click_carrot=1..}] at @s if items entity @s weapon.mainhand minecraft:carrot_on_a_stick[custom_data={%s}] run function %s:%s",
    "flipped_card": "execute as @s run loot give @s loot tcg:%s/%s"
}

type_rares_template = {
    'loot': 'execute as @a[scores={right_click_carrot=1..}] at @s if items entity @s weapon.* carrot_on_a_stick[custom_data={%s_rares_%s:1b}] run loot give @s loot tcg:type_rares_%s/%s',
    'clear': 'execute as @a[scores={right_click_carrot=1..}] at @s if items entity @s weapon.* carrot_on_a_stick[custom_data={%s_rares_%s:1b}] run clear @s minecraft:carrot_on_a_stick[custom_data={%s_rares_%s:1b}] 1',
    'reset': 'scoreboard players reset @a[scores={right_click_carrot=1..}] right_click_carrot'
}


def insert_functions(directory: str, rarity: str, pull_rate: int, start: int, booster: int, lines: List[str]) -> tuple:
    for n in range(start, pull_rate):
        file_directory = f"{directory}/{n}.mcfunction"
        with open(file_directory, "w") as file:
            lines.append(template["add_score"] % booster)
            booster += 1
            lines.append(template["spawn_loot_table"] % (booster, set, rarity.lower()))
            lines.append(template["que_next_card"] % (booster, set, n + 1))
            mcfunction = "\n".join(lines)
            file.write(mcfunction)
            lines = []

    return lines, booster


def type_rares_functions():
    for gen in generations:
        gen_string = gen.replace('_', '')
        for energy_type in energy_types:
            loot = type_rares_template['loot'] % (energy_type.lower(), gen_string, gen_string, energy_type.lower())
            clear = type_rares_template['clear'] % (energy_type.lower(), gen_string, energy_type.lower(), gen_string)
            reset = type_rares_template['reset']

            type_rare_directory = f'{gen}/functions/type_rares_{gen_string}/function/'
            if not os.path.exists(type_rare_directory):
                os.makedirs(type_rare_directory)

            type_rare_directory += f'{energy_type.lower()}_rares.mcfunction'
            with open(type_rare_directory, 'w') as file:
                for line in [loot, clear, reset]:
                    file.write(line + '\n')


if __name__ == '__main__':
    flip_card_lines = []
    initiate_set_lines = []
    for set in target_set_list:
        if set == 'basep':
            continue
        file_directory = None
        for gen, set_names in generations.items():
            if set in set_names:
                file_directory = gen
                break

        directory = f"{file_directory}/functions/{set}/function"
        if os.path.exists(directory):
            shutil.rmtree(directory)
        os.makedirs(directory)
        booster = booster_score[set]
        custom_data = set + ':1'

        lines = [template["set_score"] % booster_score[set], template["playsound"],
                 template["clear_booster"] % (custom_data, custom_data)]

        # Common cards
        pull_rate = pull_rate_dict[set]["Common"]
        start = 0
        lines, booster = insert_functions(directory=directory, rarity="Common", start=start, pull_rate=pull_rate,
                                          booster=booster, lines=lines)

        pull_rate = pull_rate_dict[set]["Uncommon"] + pull_rate_dict[set]["Common"]
        start = pull_rate_dict[set]["Common"]
        lines, booster = insert_functions(directory=directory, rarity="Uncommon", start=start, pull_rate=pull_rate,
                                          booster=booster, lines=lines)

        total_functions = pull_rate_dict[set]["Common"] + pull_rate_dict[set]["Uncommon"]
        if pull_rate_dict[set]['Reverse'] > 0:
            with open(f"{directory}/{total_functions}.mcfunction", "w") as file:
                lines.append(template["add_score"] % booster)
                booster += 1
                lines.append(template["spawn_loot_table"] % (booster, set, "reverse"))
                lines.append(template["que_next_card"] % (booster, set, total_functions + 1))
                mcfunction = "\n".join(lines)
                file.write(mcfunction)
        lines = []
        total_functions += pull_rate_dict[set]["Reverse"]
        if pull_rate_dict[set]["Rare"] > 0:
            with open(f"{directory}/{total_functions}.mcfunction", "w") as file:
                lines.append(template["add_score"] % booster)
                booster += 1
                lines.append(template["spawn_loot_table"] % (booster, set, "rare"))
                lines.append(template["que_next_card"] % (booster, set, total_functions + 1))
                mcfunction = "\n".join(lines)
                file.write(mcfunction)
        lines = []
        total_functions += pull_rate_dict[set]["Rare"]
        with open(f"{directory}/{total_functions}.mcfunction", "w") as file:
            lines.append(template["add_score"] % booster)
            booster += 1
            lines.append(template["spawn_loot_table"] % (booster, set, "premium"))
            if pull_rate_dict[set]['Energy'] == 0:
                lines.append(template["reset_score"] % booster)
            else:
                lines.append(template['que_next_card'] % (booster, set, total_functions + 1))
            mcfunction = "\n".join(lines)
            file.write(mcfunction)
        total_functions += pull_rate_dict[set]['Premium']
        if pull_rate_dict[set]['Energy'] > 0:
            for i in range(pull_rate_dict[set]['Energy']):
                lines = []
                with open(f'{directory}/{total_functions}.mcfunction', 'w') as file:
                    lines.append(template['add_score'] % booster)
                    booster += 1
                    lines.append(template['spawn_loot_table'] % (booster, set, 'energy'))
                    if i == pull_rate_dict[set]['Energy'] - 1:
                        lines.append(template['reset_score'] % booster)
                    else:
                        lines.append(template['que_next_card'] % (booster, set, total_functions + 1))
                    mcfunction = '\n'.join(lines)
                    file.write(mcfunction)
                total_functions += 1

        for card in ["reverse", "premium"]:
            lines = []
            custom_data = f'{set}_{card}_rare:1b'
            flip_card_lines.append(template["flip_card"] % (custom_data, set, card))
            with open(f"{directory}/{card}.mcfunction", "w") as file:
                lines.append(template["clear_booster"] % (custom_data, custom_data))
                lines.append(template["flipped_card"] % (set, f"{card}_rare"))
                mcfunction = "\n".join(lines)
                file.write(mcfunction)
        line = template['flip_card'] % (set + ':1', set, '0')
        initiate_set_lines.append(line)
    with open(f"{file_directory}/tick_function.mcfunction", "w") as file:
        mcfunction = "\n".join(flip_card_lines + initiate_set_lines)
        file.write(mcfunction)

    # Wizards Black Star Promos
    file_directory = 'gen_1'
    directory = f"{file_directory}/functions/basep/function"
    set = "basep"
    if os.path.exists(directory):
        shutil.rmtree(directory)
    os.makedirs(directory)
    booster = booster_score[set]
    custom_data = 'basep:1'
    lines = []
    lines.append(template["set_score"] % booster_score[set])
    lines.append(template["playsound"])
    lines.append(template["clear_booster"] % (custom_data, custom_data))
    for n in range(4):
        file_directory = f"{directory}/{n}.mcfunction"
        with open(file_directory, "w") as file:
            lines.append(template["add_score"] % booster)
            booster += 1
            lines.append(template["spawn_loot_table"] % (booster, set, "promos"))
            lines.append(template["que_next_card"] % (booster, set, n + 1))
            mcfunction = "\n".join(lines)
            file.write(mcfunction)
            lines = []

    # Generate type rare function files
    type_rares_functions()
