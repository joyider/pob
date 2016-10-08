BACKUP INCREMENTAL LEVEL 0 DATABASE PLUS ARCHIVELOG;

crosscheck backup;
crosscheck archivelog all;
delete expired archivelog all;
delete noprompt obsolete;