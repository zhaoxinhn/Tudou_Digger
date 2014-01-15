#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 2014/01/15 lwldcr@gmail.com

##########################
# Tudou video downloader #
##########################

import os,sys
import urllib,re

class videoHtml(object):
	def __init__(self,url):
		self.rs = ''
		self.html = ''
		self.vhtml = ''
		self.qs = []
		self.vurl = ''
		self.title = ''
		self.url = url
		#print "url:",self.url
	def fetchHtml(self):
		if not self.url:
			return
		try:
			self.html = urllib.urlopen(self.url).read()
		except:
			print "Html fetching failed!"
			return
		if self.html:
			self.rs = re.search(r'segs:\s*\'({.*?})\'', self.html)
			self.title = re.search(r',kw\:\"(.*?)\"', self.html).group(1)
		if self.title:
			self.title = self.title.decode('gbk')

	def parseKey(self):
		if not self.rs:
			return
		#print self.rs.group(1)
		self.qs = re.findall(r'\"(\d+)\":\[{.*?k\":(\d+),',self.rs.group(1))
		if not self.qs:
			return

		(self.q,self.k) = (self.qs[0][0],self.qs[0][1])
		for (q,k) in self.qs:
			if int(q) > int(self.q):
				(self.q, self.k) = (q,k)

	def parseUrl(self):
		"parse video url"
		if not self.q or not self.k:
			return
		baseUrl = 'http://v2.tudou.com/f?id='
		url = baseUrl + self.k
		try:
			self.vhtml = urllib.urlopen(url).read()
		except:
			pass

		if not self.vhtml:
			return
		self.vurl = re.search(r'\<f.*?\>(http\:\/\/.*?)\</f', self.vhtml).group(1)

def download(url,title):
	"Download video from internet"
	url = url.replace('amp;','')
	suffix = re.search(r'http:\/\/.*?\/(.*?)\/',url).group(1)
	filename = '.'.join([title,suffix])
	try:
		urllib.urlretrieve(url,filename)
		print "file \"%s\" has been saved!" % (filename)
	except:
		print "Downlaod failed!"

def Usage():
	"Usage function."
	usageInfo = '''
Usage:
%s [v(ideo)|l(ist)] video_url
	''' % (sys.argv[0])
	print usageInfo
	sys.exit(0)

def judgeUrl(url):
	"Judge if given url suitable."
	if not url.startswith("http://"):
		url = 'http://' + url
	if url.find('tudou') == -1:
		return 0
	return 1

def main():
	"main function"
	if len(sys.argv) != 3:
		Usage()
	elif sys.argv[1] not in ['v','l']:
		Usage()
	if not judgeUrl(sys.argv[2]):
		print '***Illegal url given***'
		print 'Currently only \"tudou.com\" supported!'
		Usage()

	vHtml = videoHtml(sys.argv[2])
	vHtml.fetchHtml()
	vHtml.parseKey()
	vHtml.parseUrl()
	download(vHtml.vurl,vHtml.title)

if __name__ == '__main__':
	main()