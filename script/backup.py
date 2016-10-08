#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
# POB (c) 2016 by Andre Karlsson<andre.karlsson@protractus.se>

# Filename: backup by: andrek
# Timesamp: 2016-04-08 :: 20:43

import os
from sys import exit
import subprocess
import time
from ConfigParser import SafeConfigParser
import smtplib
import mimetypes
import email
import email.mime.application

conf_file = '../config.ini'

currentdate = time.strftime("%Y-%m-%d_%H%M%S")
bkplog = os.path.realpath('../logs/backup_' + currentdate + '.log')
logfile = os.path.realpath('../logs/rman_' + currentdate + '.log')

print('Log files for current session can be found at: ' + bkplog + ' and ' + logfile)


def getNodeText(node):
	nodelist = node.childNodes
	result = []
	for node in nodelist:
		if node.nodeType == node.TEXT_NODE:
			result.append(node.data)

	return ''.join(result)


def backup_db(log):
	sid = config.get('db', 'sid')
	cmdfile = config.get('db', 'pob_script')

	log.write('Oracle backup settings: - SID: ' + sid + ' - cmdFile: ' + cmdfile + '\n')

	rmanCMD = 'rman cmdfile="' + cmdfile + '" log="' + logfile + '" target /'

	os.putenv('NLS_DATE_FORMAT', 'DD-MM-YYYY HH24:MI:SS')
	os.putenv('ORACLE_SID', sid)

	output = subprocess.check_output(rmanCMD, shell=True)

	log.write(output)


def send_mail(conf, log, rmanLog, date):
	fromaddr = conf.get('smtp', 'from')
	toaddr = conf.get('smtp', 'to')
	ccaddr = conf.get('smtp', 'cc')

	server = conf.get('smtp', 'server')
	port = conf.get('smtp', 'port')
	useSSL = conf.get('smtp', 'ssl')
	username = conf.get('smtp', 'user')
	passwd = conf.get('smtp', 'password')

	msg = email.mime.Multipart.MIMEMultipart()
	msg['Subject'] = 'RMAN log ' + date
	msg['From'] = fromaddr
	msg['To'] = toaddr
	msg['Cc'] = ccaddr

	body = email.mime.Text.MIMEText('The log files were attached.')
	msg.attach(body)

	filename = os.path.basename(log)
	with open(log, 'rb') as f:
		att = email.mime.application.MIMEApplication(f.read(), _subtype="txt")
		att.add_header('Content-Disposition', 'attachment; filename=%s' % filename)
		msg.attach(att)

	filename = os.path.basename(rmanLog)
	with open(rmanLog, 'rb') as f:
		att = email.mime.application.MIMEApplication(f.read(), _subtype="txt")
		att.add_header('Content-Disposition', 'attachment; filename=%s' % filename)
		msg.attach(att)

	if (len(server) == 0 or len(port) == 0):
		return

	server = smtplib.SMTP(server + ':' + port)

	if useSSL.lower() == 'true':
		server.starttls()

	if (len(username) > 0 and len(passwd) > 0):
		server.login(username, passwd)

	rcpt = ccaddr.split(",") + [toaddr]
	server.sendmail(fromaddr, rcpt, msg.as_string())

	server.quit()


# end

if __name__ == "__main__":
	with open(bkplog, 'w') as log:
		if not os.path.exists(conf_file):
			log.write('The config file (' + conf_file + ') does not exist...\n')
			log.write('Backup process was abandoned.\n')
			exit(0)
		config = SafeConfigParser()
		config.read(conf_file)
		backup_db(log)
	send_mail(config, bkplog, logfile, currentdate)
