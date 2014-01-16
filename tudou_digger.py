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
		# setting initial variables
		self.rs = ''
		self.html = ''
		self.vhtml = ''
		self.qs = []
		self.vurl = ''
		self.title = ''
		self.vcode = ''
		self.q = ''
		self.k = ''
		self.parts = []
		self.ks = []
		self.vurls = []
		self.type = 0
		self.url = url

	def fetchHtml(self):
		if not self.url:
			return
		if not self.url.startswith("http://"):
			self.url = 'http://' + self.url
		
		try:
			self.html = urllib.urlopen(self.url).read()
		except:
			print "Html fetching failed!"
			return
		try:
			self.html = self.html.decode('utf-8')
		except:
			self.html = self.html.decode('gbk')

		if self.html:
			self.html = self.html
			self.rs = re.search(r'segs:\s*\'{(.*?)}]}\'', self.html)
			self.title = re.search(r',kw:\s*\"(.*?)\"', self.html)
		if not self.rs:
			self.vcode = re.search(r',vcode:\s*\'(.*?)\'', self.html)
			if not self.vcode:
				print "Cannot find proper video address!"
				return
			else:
				self.vcode = self.vcode.group(1)

		if self.title:
			self.title = self.title.group(1)

	def parse(self):
		if self.rs:
			# 原创类视频
			self.parseKey()
			self.parseUrl()
			self.type = 0
		else:
			# 影视剧类视频，来源为优酷
			self.parseVcode()
			self.type = 1

	def parseKey(self):
		lines = self.rs.group(1).replace('"','').split('}],')
		self.q = int(lines[0].split(':')[0])
		i = 0
		flag = 0
		for line in lines:
			if int(line.split(':')[0]) > self.q:
				self.q = int(line.split(':')[0])
				flag = i
			i = i + 1
		vString = lines[flag].split('[{')[1]
		vInfo = vString.split('},{')

		for info in vInfo:
			infoList = info.split(',')
			self.parts.append(infoList[1].split(':')[1])
			self.ks.append(infoList[3].split(':')[1])
		print self.parts,self.ks


	def parseUrl(self):
		"parse video url"
		if not self.q:
			return
		baseUrl = 'http://v2.tudou.com/f?id='
		for k in self.ks:
			url = baseUrl + k
			try:
				self.vhtml = urllib.urlopen(url).read()
			except:
				pass

			if not self.vhtml:
				continue
			self.vurls.append(re.search(r'\<f.*?\>(http\:\/\/.*?)\</f', self.vhtml).group(1))
		print self.vurls

	def parseVcode(self):
		"parse vcode"
		print self.vurl
		#url = 'http://v.youku.com/player/getPlayList/VideoIDS/' + self.vcode
		url = 'http://v.youku.com/player/getPlayList/VideoIDS/' + self.vcode + '/timezone/+08/version/5/source/out/Sc/2?n=3&ran=9109&password='
		tempHtml = ''
		try:
			tempHtml = urllib.urlopen(url).read()
		except:
			pass

		try:
			tempHtml.decode('gbk')
		except:
			tempHtml.decode('utf-8')

		seed = int(re.search(r'\"seed\":(\d+)',tempHtml).group(1))
		streamfs = re.search(r'\"streamfileids\":\{(.*?)\}', tempHtml).group(1)
        	d = {}
        	for stream in streamfs.replace('"','').split(','):
			(s,i) = stream.split(':')
			d[s] = i

        	ids = []
        	for stream in ['mp4','hd3','hd2','flv']:
            		try:
                		ids = d[stream].split('*')[:-1]
				break
            		except:
                		continue
		
		key = ''
		#if len(ids) ==3:
		#	key = '030008040152CA77D64D5A1468DEFE3119FD95-CA53-5025-B539-7AADE8B9AF57_'
		
		s = list("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ/\\:._-1234567890")
        	mixed = ''
		ins = []
        	while s:
			seed = (seed * 211 + 30031) & 0xFFFF
        		index = seed * len(s) >> 16
        		c = s.pop(index)
        		mixed += c
			ins.append(index)
		print mixed,''.join(mixed[int(i)] for i in ins)
		print len(ids), ids
		print len(ins), ins
        	vid = ''.join(mixed[int(i)] for i in ids)

		pattern = r'\"%s\"\:\[\{(\"no\".*?)}]' % (stream)
		partinfos = re.search(pattern,tempHtml,re.S).group(1).split('},{')

		for partinfo in partinfos:
			info = partinfo.replace('"','').split(',')
			partno = info[0].split(':')[1]
			key2 = info[3].split(':')[1]
			no = '%02x' % int(partno)
			if key:
				key1 = key + '%02d' % int(partno)
				self.vurls.append('http://f.youku.com/player/getFlvPath/sid/00_00/st/%s/fileid/%s?K=%s' % (stream, key1, key2))
			else:
				self.vurls.append('http://f.youku.com/player/getFlvPath/sid/00_00/st/%s/fileid/%s?K=%s' % (stream, vid[:8]+no.upper()+vid[10:],key2))
		print self.vurls
		

def download(url,title,type,i=0):
	"Download video from internet"
	url = url.replace('amp;','')
	if type == 0:
		suffix = re.search(r'http:\/\/.*?\/(.*?)\/',url).group(1)
	elif type == 1:
		suffix = re.search(r'http:\/\/.*?st\/(.*?)\/fileid', url).group(1)
	else:
		suffix = ''
	filename = ''.join([title,'-',str(i),'.',suffix])
	try:
		print "downloading \"%s\"..." % (filename)
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
	vHtml.parse()
	if vHtml.vurls:
		i = 0
		for url in vHtml.vurls:
			download(url,vHtml.title, vHtml.type,i)
			i += 1

if __name__ == '__main__':
	main()
