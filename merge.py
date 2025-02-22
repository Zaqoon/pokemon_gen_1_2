import os
import shutil


def copy_and_merge(source, destination):
    """
    Copy files and directories from source to destination,
    merging directories and overwriting files without deleting other existing files.
    """
    # Check if the source path exists
    if not os.path.exists(source):
        print(f"Source path {source} does not exist. Skipping.")
        return

    # Check if source is a directory
    if os.path.isdir(source):
        # If destination doesn't exist, create it
        if not os.path.exists(destination):
            os.makedirs(destination)

        # Recursively copy each item in the source directory
        for item in os.listdir(source):
            source_item = os.path.join(source, item)
            destination_item = os.path.join(destination, item)
            if os.path.isdir(source_item):
                # Recursively merge directories
                copy_and_merge(source_item, destination_item)
            else:
                # Overwrite files in the destination
                shutil.copy2(source_item, destination_item)
    else:
        # If source is a file, ensure the parent directory of the destination exists
        destination_dir = os.path.dirname(destination)
        if not os.path.exists(destination_dir):
            os.makedirs(destination_dir)

        # Copy and overwrite the file
        shutil.copy2(source, destination)


def import_decks():
    base_directory = 'C:/Users/Andreas/AppData/Roaming/.minecraft/saves/Naraka/datapacks/tcg/data'

    for gen in ['gen_1', 'gen_2']:
        gen_string = gen.replace('_', '')

        # Create a dictionary for source-destination pairs
        directory_dict = {
            f'{gen}/{gen_string}_boosters': f'{base_directory}/{gen_string}_boosters',
            f'{gen}/{gen_string}_decks': f'{base_directory}/{gen_string}_decks',
            f'{gen}/functions/replace_villager_decks_{gen_string}.mcfunction':
                f'{base_directory}/expansions/function/replace_villager_decks_{gen_string}.mcfunction',
            f'{gen}/functions/replace_villager_boosters_{gen_string}.mcfunction':
                f'{base_directory}/expansions/function/replace_villager_boosters_{gen_string}.mcfunction',
            f'{gen}/functions/type_rares_{gen_string}': f'{base_directory}/type_rares_{gen_string}',
        }

        # Add all folders from gen/functions/ to the dictionary
        functions_dir = f'{gen}/functions'
        for item in os.listdir(functions_dir):
            item_path = os.path.join(functions_dir, item)
            if os.path.isdir(item_path):
                directory_dict[item_path] = os.path.join(base_directory, item)

        for source, destination in directory_dict.items():
            # Copy and merge contents from source to destination
            copy_and_merge(source, destination)

            print(f'Successfully copied and merged from {source} to {destination}')


def copy_paste_folder(source: str, destination: str):
    try:
        shutil.copytree(source, destination)
        print(f'    Successfully transferred {source} to {destination}.')
    except FileExistsError:
        print(f'    {destination} already exists.')
    except Exception as e:
        print(f'    An error occurred: {e}')


def export_loot_tables():
    print('Exporting loot tables...')
    path = f'C:/Users/Andreas/AppData/Roaming/.minecraft/saves/Naraka/datapacks/tcg/data/tcg/loot_table'
    for gen in ['gen_1', 'gen_2']:
        source = f'{gen}/loot_tables'
        for set_id in os.listdir(source):
            dest = f'{path}/{set_id}'
            if os.path.exists(dest):
                shutil.rmtree(dest)

            # Paste folder
            s = f'{source}/{set_id}'
            copy_paste_folder(s, dest)
            print(f'    Successfully transferred loot_tables/{set_id} to {path}/{set_id}.')


if __name__ == '__main__':
    import_decks()
    export_loot_tables()
