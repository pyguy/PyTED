#!/usr/bin/python

from urllib2 import Request, urlopen, URLError, HTTPError
import os, sys
import string, re
import subprocess, commands

help_message = '''Uasag: python dl-ted.py [OPTIONS=]

[OPTIONS=] :
  <url>
		the url of the video!
	--best-quality, -bq
		to download with the best quality availabel! (480p)
	--show-subtitles, -ssub
		to show the list of available subtitles for this video
		you can also choose one of them to download!
	-sub[=OPTION]
		to download with an specific subtitle
	-feed
		to fix the url got from feedproxy!
	--to-dir, -d
		to specify the exact location to be downloaded video to
	--help
		displays this help :)
'''
def download_file_notposix(url, fn):
	"""'Native' python downloader -- slower than axel or wget."""
	print "Downloading %s -> %s" % (url, fn)
	urlfile = urlopen(url)
	chunk_sz = 1048576
	bytesread = 0
	f = open(fn, "wb")
	while True:
		data = urlfile.read(chunk_sz)
		if not data:
			print "."
			break
		f.write(data)
		bytesread += len(data)
		print "\r%d bytes read" % bytesread,
		sys.stdout.flush()
	urlfile.close()

def download_file(app, url, fn):
	"""Downloads a file using wget.  Could possibly use python to stream files to
	disk, but wget is robust and gives nice visual feedback."""
	if app == 'wget':
		cmd = ['wget', url, '-O', fn, "--no-check-certificate"]
	else:
		cmd = ['axel', url, '-an7', '-o', fn]
	print "Executing %s:" %app, cmd
	retcode = subprocess.call(cmd)

def getsubtitle(text):
	#req = Request(link)
	#f = urlopen(req)
	lang_list = {}
	flag = False
	for line in text.split('\n'):
		if flag:
			op = re.search('<option value="(\w\w)">([\w+]+)</option>', line)
			if op:
				lang_list[op.group(1)] = op.group(2)
			elif '</select>' in line:
				#f.close()
				return lang_list
		if 'id="subtitles_language_select"' in line:
			flag = True

def downloadVideo(link):
	try:
		if '-feed' in sys.argv:
			link = 'http://www.ted.com/talks/' + link.split('/')[-1]
		req = Request(link)
		f = urlopen(req)
		text = f.read()

		## set directory, quality and subtitle of the video
		qualityTag = ''
		subTag = ''
		dirTag = ''
		if len(sys.argv) > 2:
			if '--best-quality' in sys.argv or '-bq' in sys.argv:
				qualityTag = '-480p'
			elif '--show-subtitles' in sys.argv or '-ssub' in sys.argv:
				print "\nAvailabel subtitles for this video are: "
				sub_list=getsubtitle(text)
				print sub_list, '\n'
				op = raw_input('which subtitle do you choose? [n=none of them]: ')
				if not op == 'n' and op in sub_list:
					subTag = '-' + op
			elif '-d' in sys.argv or '--to-dir' in sys.argv:
				try:
					index = sys.argv.index('-d')
				except:
					index = sys.argv.index('--to-dir')
				dirTag = sys.argv[index+1]
			else:
				for arg in sys.argv:
					if '-sub=' in arg:
						subTag = '-' + arg[-2:]
						if qualityTag == '': qualityTag = '-low'

		### find title of the video => filename
		filename = re.search(r'<title>([\S+\s.]+)</title>', text)
		filename = filename.group(1).replace(' ', '_')
		index = string.find(filename, '|')
		filename = filename[:index] + qualityTag + subTag + '.mp4'
		filename = dirTag + filename

		### find video downlaod link
		dl_link = re.search(r'(http://download.ted.com/talks/\S+)">', text)
		dl_link = dl_link.group(1)[:-4] + qualityTag + subTag + '.mp4'

		print filename, dl_link

		## downloading video
		if 'posix' in os.name:
			if 'Axel' in commands.getoutput('axel -V'):
				download_file('axel', dl_link, filename)
				pass
			else:
				download_file('wget', dl_link, filename)
		else:
			download_file_notposix(dl_link, filename)
		f.close()

	except HTTPError, e:
		print "HTTP Error:", e.code, link
	except URLError, e:
		print "URL Error:", e.reason, link
	except AttributeError, e:
		print "AttributeError:", e

def main():
	valid = ['-bq', '--best-quality', '--show-subtitles',
			 '-ssub','-sub', '-d', '--to-dir', '-feed']
	for arg in sys.argv[2:]:
		if not arg.split('=')[0] in valid:
			if '-d' or '--to-dir' in sys.argv[2:]:
				break
			print help_message
			exit(0)

	downloadVideo(sys.argv[1])

if __name__ == '__main__':
    main()

