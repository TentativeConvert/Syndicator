#!/usr/bin/python
# -*- coding: utf-8 -*-

#backup_command = "/usr/bin/udisksctl mount -b /dev/disk/by-uuid/ae81b5b0-0b83-4f21-a0ea-9b2c370cff04 ; backintime --profile-id 2 -b" # <--- old
# unfortunately, udisksctl returns an ERROR if disk is already mounted! 
backup_command = "backintime --profile-id 1 -b"
sync_command = "pkill -x unison-fsmonito; ssh zibrowius@reh.math.uni-duesseldorf.de pkill -x unison-fsmonito; ~/bin/unison/unison-2.48 Beaver-reh.prf -repeat watch"
icon_paused = "sync-paused"
icon_default = "sync-default"

sync_patterns=[]
sync_icon_working = "sync1,sync2"   #"ubuntuone-client-idle,ubuntuone-client-updating"
ICON_GOOD = "sync-good"
ICON_ERROR = "sync-error"
sync_patterns.append({
    'pattern':r"\[END\]\s+Updating file\s+(.*/)*([^/]+)", 
    'file-text':r" \2"})
sync_patterns.append({
    'pattern':r"\[END\]\s+Copying\s+(.*/)*([^/]+)", 
    'file-text':r"*\2"})
sync_patterns.append({
    'pattern':r"\[END\]\s+Deleting\s+(.*/)*([^/]+)", 
    'file-text':r"[\2]"})
sync_patterns.append({
    'pattern':r"(Synchronization complete).* \((\d+[^)]*)\)", 
    'notify_heading':r"\1",
    'notify-text':r"\2",
    'icon':ICON_GOOD})
sync_patterns.append({
    'pattern':r"Nothing to do: replicas have not changed",
    'icon':ICON_GOOD})
sync_patterns.append({
    'pattern':r"(Fatal error): (.*)",
    'notify_heading':r"\1",
    'notify-text':r"\2",
    'error-text':r"\g<0>",
    'icon':ICON_ERROR})
sync_patterns.append({
    'pattern':r"(Error): (.*)",
    'notify_heading':r"\1",
    'notify-text':r"\2",
    'error-text':r"\g<0>",
    'icon':ICON_ERROR})
sync_patterns.append({
    'pattern':r"(Error) (.*)",
    'notify_heading':r"\1",
    'notify-text':r"\g<0>",
    'error-text':r"\g<0>",
    'icon':ICON_ERROR})
sync_patterns.append({
    'pattern':r"File name too long",
    'notify_heading':r"Fatal error",
    'notify-text':r"\g<0>",
    'error-text':r"\g<0>",
    'icon':ICON_ERROR})

backup_patterns=[]
backup_icon_working = "backup1,backup2"
ICON_ERROR = "sync-error"
backup_patterns.append({
    'pattern':r"(Fatal error): (.*)",
    'notify_heading':r"\1",
    'notify-text':r"\2",
    'error-text':r"\g<0>",
    'icon':ICON_ERROR})
backup_patterns.append({
    'pattern':r"(Error): (.*)",
    'notify_heading':r"\1",
    'notify-text':r"\2",
    'error-text':r"\g<0>",
    'icon':ICON_ERROR})
backup_patterns.append({
    'pattern':r"(Error) (.*)",
    'notify_heading':r"\1",
    'notify-text':r"\g<0>",
    'error-text':r"\g<0>",
    'icon':ICON_ERROR})
