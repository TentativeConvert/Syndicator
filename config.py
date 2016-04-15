#!/usr/bin/python

# first two icons still hand-coded in classes/Indicator
#ICONS_WORKING = ["network-transmit","network-receive"]#ubuntu-client-updating
#ICON_WAITING =  "network-idle"    #ubuntuone-client-paused"
ICON_GOOD = "emblem-default"      #ubuntuone-client-idle
ICON_ERROR = "process-stop"       #ubuntuone-client-error

backup_command = "backintime --profile-id 2 -b"
sync_command = "unison XPS12-reh -repeat watch"

backup_patterns=[]
sync_patterns=[]
sync_patterns.append({
    'pattern':r"\[END\]\s+Updating file\s+(.*/)*([^/]+)", 
    'log_text':r" \2"})
sync_patterns.append({
    'pattern':r"\[END\]\s+Copying\s+(.*/)*([^/]+)", 
    'log_text':r"*\2"})
sync_patterns.append({
    'pattern':r"\[END\]\s+yDeleting\s+(.*/)*([^/]+)", 
    'log_text':r"[\2]"})
sync_patterns.append({
    'pattern':r"(Synchronization complete).* \((\d+[^)]*)\)", 
    'notify_heading':r"\1",
    'notify_text':r"\2",
    'icon':ICON_GOOD})
sync_patterns.append({
    'pattern':r"Nothing to do: replicas have not changed",
    'icon':ICON_GOOD})
sync_patterns.append({
    'pattern':r"(Fatal error): (.*)",
    'notify_heading':r"\1",
    'notify_text':r"\2",
    'error_text':r"\g<0>",
    'icon':ICON_ERROR})
sync_patterns.append({
    'pattern':r"(Error): (.*)",
    'notify_heading':r"\1",
    'notify_text':r"\2",
    'error_text':r"\g<0>",
    'icon':ICON_ERROR})
sync_patterns.append({
    'pattern':r"(Error) (.*)",
    'notify_heading':r"\1",
    'notify_text':r"\g<0>",
    'error_text':r"\g<0>",
    'icon':ICON_ERROR})
sync_patterns.append({
    'pattern':r"File name too long",
    'notify_heading':r"Fatal error",
    'notify_text':r"\g<0>",
    'error_text':r"\g<0>",
    'icon':ICON_ERROR})
