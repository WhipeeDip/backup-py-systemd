#!/usr/bin/env python3

from datetime import datetime
import json
import os
from pathlib import Path
import shutil
import sys
import traceback

# CHANGE THIS!
CONFIG_LOCATION = '/root/backup-py/config.json'

# assuming linux with /tmp
TMP_ROOT = '/tmp'
TMP_DIR = os.path.join(TMP_ROOT, 'backup-py',
    datetime.now().strftime('%Y-%m-%d_%H-%m-%f'))
TMP_ARCHIVE_DIR = os.path.join(TMP_DIR, 'archives')


def main():
    print('Starting main()')

    if sys.version_info < (3, 6):
        print('You need Python 3.6 or higher')
        sys.exit(1)

    print('Reading config')
    try:
        with open(CONFIG_LOCATION, 'r') as file:
            config = json.load(file)
    except Exception as ex:
        print(f'ERROR while reading config:\n{traceback.format_exc()}')
        sys.exit(1)

    settings = config['settings']
    backups = config['backups']

    usage = shutil.disk_usage(TMP_ROOT)
    free_space = 1.0 - (usage.used / usage.total)
    print(f'Free space on {TMP_ROOT} is {free_space * 100}%')
    if float(settings['min_space_pct']) >= free_space:
        print(f'ERROR Not enough space in {TMP_ROOT}; have {free_space * 100}% free. Ending backup')
        sys.exit(1)

    print('Beginning backup loop')
    for key, value in backups.items():
        print(f'[{key}] Starting backup')

        if not value['enabled']:
            print(f'[{key}] Not enabled, skipping')
            continue

        try:
            if value['cmd_start']:
                cmd_start = value["cmd_start"]
                for cmd in cmd_start:
                    print(f'[{key}] Running start command: {cmd}')
                    ret_val = os.system(cmd)
                    print(f'[{key}] Got return code: {ret_val}')

            time_str = datetime.now().strftime(settings['strftime'])
            bkup_name = f'{time_str}_{key}'
            bkup_path = os.path.join(TMP_DIR, bkup_name)
            os.makedirs(bkup_path)
            print(f'[{key}] Created tmp backup dir at {bkup_path}')

            for src_bkup in value['source']:
                print(f'[{key}] Backing up {src_bkup}')

                if os.path.isdir(src_bkup):
                    tmp_path = Path(src_bkup)
                    dir_name = tmp_path.name
                    shutil.copytree(src_bkup, os.path.join(bkup_path, dir_name), symlinks=value['follow_symlinks'],
                        copy_function=shutil.copy2, dirs_exist_ok=True)
                elif os.path.isfile(src_bkup):
                    shutil.copy2(src_bkup, bkup_path, follow_symlinks=value['follow_symlinks'])
                else:
                    print(f'[{key}] ERROR {src_bkup} doesn\'t exist, is not a file, or is not a dir. Not copying')
                    continue

            print(f'[{key}] Making archive')
            archive_base_name = os.path.join(TMP_ARCHIVE_DIR, bkup_name)
            archive_path = shutil.make_archive(archive_base_name, settings['format'],
                root_dir=TMP_DIR, base_dir=bkup_name)
            tmp_path = Path(archive_path)
            archive_name = tmp_path.name
            print(f'[{key}] Archive created at: {archive_path}')

            for dest_bkup in value['dest']:
                print(f'[{key}] Copying archive to {dest_bkup}')

                os.makedirs(dest_bkup, exist_ok=True)
                usage = shutil.disk_usage(dest_bkup)
                free_space = 1.0 - (usage.used / usage.total)
                print(f'[{key}] Free space on {dest_bkup} is {free_space * 100}%')
                if float(settings['min_space_pct']) >= free_space:
                    print(f'[{key}] ERROR Not enough space in {dest_bkup}; have {free_space * 100}% free. Not copying archive')
                    sys.exit(1)

                dest_path_full = os.path.join(dest_bkup, archive_name)
                shutil.copy2(archive_path, dest_path_full)

                # shutil.copy2() doesn't copy permissions?
                if value['archive_permissions']:
                    print(f'[{key}] Applying permissions to archive')
                    os.chmod(dest_path_full, int(value['archive_permissions'], 8))

                if value['archive_owner']:
                    print(f'[{key}] Applying owner to archive')
                    shutil.chown(dest_path_full, user=value['archive_owner'])

                if value['archive_group']:
                    print(f'[{key}] Applying group to archive')
                    shutil.chown(dest_path_full, group=value['archive_group'])

            print(f'[{key}] Finished backup!')
        except Exception as ex:
            print(f'[{key}] ERROR while backing up:\n{traceback.format_exc()}')
            print(f'[{key}] Skipping')
        finally:
            try:
                if value["cmd_end"]:
                    cmd_end = value["cmd_end"]
                    for cmd in cmd_end:
                        print(f'[{key}] Running end command: {cmd}')
                        ret_val = os.system(cmd)
                        print(f'[{key}] Got return code: {ret_val}')
            except Exception as ex:
                print(f'[{key}] ERROR in finally block:\n{traceback.format_exc()}')

    print('Finished backup loop.')

    print(f'Deleting tmp dir: {TMP_DIR}')
    if os.path.exists(TMP_DIR):
        shutil.rmtree(TMP_DIR)

    print('Exiting main()')

if __name__ == "__main__":
    main()
