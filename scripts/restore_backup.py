from pymongo import MongoClient
from rich.pretty import pprint
from rich.progress import track, Progress
import rich.prompt
import datetime

def run():
    ''' Rename collections as backups '''
    client = MongoClient('localhost', 27017)

    print('Please select a backup to restore:')
    possible_backups = client.r_table.list_collection_names()
    for i, possible in enumerate(possible_backups):
        print(f'{i:2}: {possible}', flush=True)
    get_choice = rich.prompt.IntPrompt('Selection:')
    choice = get_choice.ask()
    chosen = possible_backups[choice]
    suffix = chosen.split('r_table_')[-1]

    if rich.prompt.Confirm('Please confirm the restoration.'):
        # First, back up the existing content
        now = datetime.datetime.now()
        backup_key = f'backup_{now.replace(microsecond=0)}'
        client.r_table.r_table.rename(f'r_table_{backup_key}_auto')
        for ref_key in client.inferred.list_collection_names():
            client.inferred[ref_key].rename(f'{ref_key}_{backup_key}_auto')
        # Second, restore the desired content
        client.r_table[chosen].rename(f'r_table')
        for ref_key in client.reference_sets_group_lookup.list_collections():
            client.inferred[f'{ref_key}_{backup_key}{backup_name}'].rename(f'{ref_key}')