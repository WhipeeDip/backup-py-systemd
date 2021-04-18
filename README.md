# backup-py-systemd

A configurable Python script to backup multiple folders/files to multiple destinations. Includes systemd files.

Requires Python 3.6+. Tested only on Linux but in theory should work on Windows and macOS if you change `TMP_ROOT`.

## Install

1. Put `backup.py` in `/usr/local/bin`.

2. `chmod +x /usr/local/bin/backup.py`.

3. Edit and put `config.json` somewhere. Make sure to update `CONFIG_LOCATION` appropriately.

4. Put `backup-py.service` and `backup-py.timer` in `/etc/systemd/system/`, configuring as wanted. Timer runs at 3:00:00 AM and 3:00:00 PM by default.

5. `sudo systemctl enable backup-py.timer`

6. `sudo systemctl start backup-py.timer`

## `config.json`

* `enabled`: Bool whether this backup entry is enabled.

* `strftime` string format: [https://docs.python.org/3/library/datetime.html#strftime-and-strptime-format-codes](https://docs.python.org/3/library/datetime.html#strftime-and-strptime-format-codes)

* `format`: [https://docs.python.org/3/library/shutil.html#archiving-operations](https://docs.python.org/3/library/shutil.html#archiving-operations)

* `min_space_pct`: How much free space needs to be free on both `TMP_ROOT` and dest drives. Nothing happens if there isn't enough space on `TMP_ROOT`. Archived output is not copied to the destinations if there isn't enough space on thme.

* `backups`: A bunch of objects, with the key being the name.

  * `source` and `dest`: Array of paths to backup, and where to copy archive output to.

  * `follow_symlinks`: Whether to follow symlinks when backing up, or to just backup the symlink itself.

  * `archive_*`: Sets the permissions and owner/group of the resulting archive. Can be `null` if not wanted.

  * `cmd_start` and `cmd_end`: Shell command(s) run at the start/end of this specific backup. For example, can be used to stop a service beforehand and restart it after. Can be empty array. Beware, systemd will by default run this as root!

## Warnings

* Using the tar archive formats seems to result in weird archive hierarchy where tmp and stuff gets prepended before the tar (KDE Dolphin was suppressing this, while 7-Zip was showing this). I don't see this same behavior with zip. It doesn't really affect the actual backup.

* While I have tested this as working on my setup, you should always validate that you can backup **and restore**!

* Make sure to check systemctl status and journalctl for logs periodically, since this script won't do anything beyond non-zero exit codes and logging errors to stdout!

* If you are backing up sensitive data, this script does copy files to `/tmp` before compressing them and finally deleting them. In addition, archives produced by this script currently do not support any sort of encryption. If you don't want this sensitive data to exist anywhere universally readable such as `/tmp` even for a moment or need encrypted archives, perhaps this script may not be for you.
