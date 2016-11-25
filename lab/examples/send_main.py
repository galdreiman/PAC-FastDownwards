#!/usr/bin/python

import smtplib
import base64

filename = "/home/shahar/outfile.csv"

# Read a file and encode it into base64 format
fo = open(filename, "rb")
filecontent = fo.read()
encodedcontent = base64.b64encode(filecontent)  # base64

sender = 'gal.dreiman@outlook.com'
reciever = 'gal.dreiman@gmail.com'

marker = "AUNIQUEMARKER"

body ="""
This is a test email to send an attachement.
"""
# Define the main headers.
part1 = """From: From Person <gal.dreiman@gmail.com>
To: To Person <gal.dreiman@gmail.com>
Subject: Sending Attachement
MIME-Version: 1.0
Content-Type: multipart/mixed; boundary=%s
--%s
""" % (marker, marker)

# Define the message action
part2 = """Content-Type: text/plain
Content-Transfer-Encoding:8bit

%s
--%s
""" % (body,marker)

# Define the attachment section
part3 = """Content-Type: multipart/mixed; name=\"%s\"
Content-Transfer-Encoding:base64
Content-Disposition: attachment; filename=%s

%s
--%s--
""" %(filename, filename, encodedcontent, marker)
message = part1 + part2 + part3

try:
	server = smtplib.SMTP("smtp.live.com", 587)
	# server.ehlo()
	# server.starttls()
	server.login('gal.dreiman@outlook.com', 'mpZnva5o')
	server.sendmail(sender, reciever, message)
	server.close()
	print "Successfully sent email"
except Exception:
	print "Error: unable to send email"