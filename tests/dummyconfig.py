#!/usr/bin/python
# -*- coding: utf-8 -*-

backup_command = "~/uniIT/Scripts/Syndicator/tests/dummybackup.sh"
sync_command = "~/uniIT/Scripts/Syndicator/tests/dummysync.sh"

icon_paused = "ubuntuone-client-paused"
icon_default = "ubuntuone-client-idle"

backup_icon_working = "network-transmit,network-receive,network-idle"
sync_icon_working = "ubuntuone-client-idle,ubuntuone-client-updating"

sync_patterns = []
ICON_GOOD = "emblem-default"
ICON_ERROR = "ubuntuone-client-error"
sync_patterns.append({
    'pattern':r"Sync -- (special status _good_)",
    'icon':ICON_GOOD
})
sync_patterns.append({
    'pattern':r"Sync -- (special status _info_)",
    'notify-heading':"Sync",
    'notify-text':r"\1",
    'icon':"gtk-info"
})
sync_patterns.append({
    'pattern':r"Sync -- (error [0-9]*)",
    'error-text':r"\1",
    'icon':ICON_ERROR
})
sync_patterns.append({
    'pattern':r"Sync -- (file [0-9]*)",
    'file-text':r"\1"
})
sync_patterns.append({
    'pattern':r"Sync -- (fatal error [0-9]*)",
    'error-text':r"\1",
    'notify-heading':"Sync Error",
    'notify-text':r"\1",
    'icon':ICON_ERROR
})

backup_patterns = []
ICON_ERROR = "process-stop"
ICON_GOOD = "gtk-home"
backup_patterns.append({
    'pattern':r"Backup -- (special status _home_)",
    'icon':ICON_GOOD
})
backup_patterns.append({
    'pattern':r"Backup -- (special status _info_)",
    'notify-heading':"Backup",
    'notify-text':r"\1",
    'icon':"gtk-info"
})
backup_patterns.append({
    'pattern':r"Backup -- (error [0-9]*)",
    'error-text':r"\1",
    'icon':ICON_ERROR
})
backup_patterns.append({
    'pattern':r"Backup -- (fatal error [0-9]*)",
    'error-text':r"\1",
    'notify-heading':"Backup Error",
    'notify-text':r"\1",
    'icon':ICON_ERROR
})
