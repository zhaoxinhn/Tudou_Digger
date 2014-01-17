#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 2014/01/15 lwldcr@gmail.com

##########################
# Tudou video downloader #
##########################

import os,sys
import urllib,re
from time import time

outputDir = '/Volumes/HDD_OSX_Data/Video'

class videoHtml(object):
	def __init__(self,url='',vcode='',title=''):
		# setting initial variables
		self.rs = ''
		self.html = ''
		self.vhtml = ''
		self.qs = []
		self.vurl = ''
		self.title = title
		self.vcode = vcode
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
        	for stream in ['hd3','hd2','mp4','flv']:
            		try:
                		ids = d[stream].split('*')[:-1]
				break
            		except:
                		continue
		if stream == 'mp4':
			f_type = 'mp4'
		else:
			f_type = 'flv'
		
		s = list("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ/\\:._-1234567890")
        	mixed = ''
        	while s:
			seed = (seed * 211 + 30031) & 0xFFFF
        		index = seed * len(s) >> 16
        		c = s.pop(index)
        		mixed += c
        	vid = ''.join(mixed[int(i)] for i in ids)

		pattern = r'\"%s\"\:\[\{(\"no\".*?)}]' % (stream)
		partinfos = re.search(pattern,tempHtml,re.S).group(1).split('},{')

		for partinfo in partinfos:
			info = partinfo.replace('"','').split(',')
			partno = info[0].split(':')[1]
			key = info[3].split(':')[1]
			no = '%02x' % int(partno)
			self.vurls.append('http://f.youku.com/player/getFlvPath/sid/00_00/st/%s/fileid/%s?K=%s' % (f_type, vid[:8]+no.upper()+vid[10:],key))
		return

def getFullname(partname):
	"""Get merged file name."""
	ns = re.search(r'(.*?)\-\d+\.([a-zA-Z0-9]+)', partname)
	try:
                (name, suffix) = ns.group(1), ns.group(2)
        except:
                print "Filename parsing error!"
                return
        fullname = name + '.' + suffix
	return (fullname, suffix)

class Printer():
	def __init__(self,data):
		sys.stdout.write("\r\x1b[K" + data.__str__())
		sys.stdout.flush()
	
def cbk(a, b, c): 
	'''回调函数 @a: 已经下载的数据块  @b: 数据块的大小  @c: 远程文件的大小'''
	per = 100.0 * a * b / c 
    	if per > 100: 
        	per = 100 
	text = '------Completed percentage: %.2f%%-------' % per
	Printer(text)

def judgeAvailable(filename, url):
	"""Judge if existing filename correctly downloaded from url."""
	fLen = os.path.getsize(filename)
	p = urllib.urlopen(url)
	tLen = int(p.info().getrawheader('Content-Length').replace('\r\n',''))
	p.close()
	
	if fLen == tLen:
		return True
	else:
		return False
	
def download(url,title,type,i=0):
	"Download video from internet"
	url = url.replace('amp;','')
	if type == 0:
		suffix = re.search(r'http:\/\/.*?\/(.*?)\/',url).group(1)
	elif type == 1:
		suffix = re.search(r'http:\/\/.*?st\/(.*?)\/fileid', url).group(1)
	else:
		suffix = ''
	filename = ''.join([title,'-','%02d' % i,'.',suffix])
	try:
		text_info = "Trying to download \"%s\"..." % (filename)
		print text_info
		fullname = getFullname(filename)[0]
		if os.path.exists(fullname):
			print "File \"%s\" downloaded already, omitted." % (fullname)
			return
		elif os.path.exists(filename):
			if judgeAvailable(filename, url):
				print "File \"%s\" downloaded already, omitted." % (filename)
				return filename
			else:
				os.remove(filename)

		urllib.urlretrieve(url,filename, cbk)
		print "\nFile \"%s\" has been saved!" % (filename)
		return filename
	except KeyboardInterrupt:
		print "\nManually interupted,cleaning..."
		if os.path.exists(filename):
			os.remove(filename)
		print "Done!"
		sys.exit(1)
	except:
		print "Downlaod failed!"
		return

def merge(files):
	"""Merge files into one."""
	(fullname, suffix) = getFullname(files[0])
	if suffix == 'flv':
		from flv_join import concat_flvs as concat
		
	elif suffix == 'mp4':
		from mp4_join import concat_mp4s as concat
	else:
		concat = ''
	
	if concat:
		concat(files, fullname)
		print "File:\"%s\" have been merged!" % (fullname)
        	print "Deleting temp files...",
        	for fp in files:
                	os.remove(fp)
        	print "Done"
       	else:
		print "File type not supported!"

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
	assert len(sys.argv) == 3, Usage()
	if len(sys.argv) != 3:
		Usage()
	elif sys.argv[1] not in ['v','l']:
		Usage()
	if not judgeUrl(sys.argv[2]):
		print '***Illegal url given***'
		print 'Currently only \"tudou.com\" supported!'
		Usage()
	if not os.path.exists(outputDir):
		os.mkdir(outputDir)
	print '***Changing working directory to:\"%s\"' % (outputDir),
	try:
		os.chdir(outputDir)
		print "Done!"
	except:
		print "Failed! Will use \"%s\" as working directory." % (os.getcwd())
	print '--------Misson Launched---------'
	if sys.argv[1] == 'v':
		singleDownload(sys.argv[2])
	else:
		albumDownload(sys.argv[2])
	print '------Misson Accomplished-------'

def albumDownload(url):
	try:
		fs = urllib.urlopen(url).read().decode('utf-8')
	except:
		fs = urllib.urlopen(url).read().decode('gbk')
	
	if not fs:
		print "Cannot download given album!"
		return
	title = re.search(r'title:\s*\'(.*)\'\s*,',fs).group(1).encode('utf-8')
	try:
		print 'Entering list directory:\"%s\"' % (title),
		if not os.path.exists(title):
			os.mkdir(title)
		os.chdir(title)
		print 'Done!'
	except:
		print 'Failed!Use \"%s\" instead!"' % (os.getcwd())

	soku_url = 'http://www.soku.com/v?keyword=' + repr(title).replace(r'\x','%')[1:-1]

	try:
		fs = urllib.urlopen(soku_url).read().decode('utf-8')
	except:
		fs = urllib.urlopen(soku_url).read().decode('gbk')
	if not fs:
		print "Cannot download given album!"
		return

	pattern = r'<a\s+href=\'(http\:\/\/.*?tudou.com/.*?.html)\'.*?\>(\d+)\<'
	vs = re.findall(pattern, fs, re.S)

	for (url,seq) in vs:
		singleDownload(url)#,title=str(cs.index(c)+1))

def singleDownload(url='',code='',title=''):
	assert url or code, "Argument error!"
	if code:
		assert title
	if url:
		vHtml = videoHtml(url)	
		vHtml.fetchHtml()
	else:
		vHtml = videoHtml(vcode=code,title=title)
	vHtml.parse()
	files = []
	if vHtml.vurls:
		i = 0
		for url in vHtml.vurls:
			filename = download(url,vHtml.title, vHtml.type,i)
			if filename:
				files.append(filename)
			i += 1
	if files:
		merge(files)
		
if __name__ == '__main__':
	main()
