#!/usr/bin/env python2
# -*- coding: utf-8 -*-

########################################################################
# Configuration properties.

#-----------------------------------#
# Bland mirror preset.

# do_filter = False

#-----------------------------------#
# Preset for sup/tg/ 'Magical Girl Noir'

# Enable filtered save by nametag.
do_filter = True
# Names to consider top-level when filtering.
filter_names = [ "Deculture", "Protoculture" ]
# If filter is enabled, level of filter.
filter_level = -1
# Delete images unrelated to saved export when filtering.
remove_unrelated_images = True
#-----------------------------------#

########################################################################

import json
from pprint import pprint
import os
import re
import sys
from subprocess import call
import shutil
from lxml.html import parse, tostring
import requests
import datetime

if len(sys.argv) < 2:
	sys.exit("Required ID argument missing.")

########################################################################
# Fetch the URL, js and css, and all images (not thumbs) from sup/tg/
def fetch_suptg(post_url, post_id):
	os.mkdir(post_id)
	os.mkdir(post_id + "/t")
	os.mkdir(post_id + "/t/images")

	open(post_id + "/t/index.html", 'wb').write(requests.get(post_url).content)

	page_html = parse(post_id + "/t/index.html").getroot()
	posts = page_html.find_class("post")
	for p in posts:
		img = ""
		try:
			href = p.find_class("fileThumb")[0].get("href")
			img_url = post_url + href

			open(post_id + "/t/" + href, 'wb').write(requests.get(img_url).content)
		except:
			pass

########################################################################
# Fetch the URL, js and css, and all images (not thumbs) from 4chan
def fetch_4c(post_url, post_id):
	os.mkdir(post_id)
	os.mkdir(post_id + "/t")
	os.mkdir(post_id + "/t/images")

	img_re = re.compile("//i.4cdn.org/[a-zA-Z]+/")

	page_html = parse(post_url)
	posts = page_html.getroot().find_class("post")
	for p in posts:
		img = ""
		try:
			href = p.find_class("fileThumb")[0].get("href")
			img_url = "http:" + href
			img_out = post_id + "/t/images/" + img_re.sub("", href)

			p.find_class("fileThumb")[0].set("href", "images/" + img_re.sub("", href))

			open(img_out, 'wb').write(requests.get(img_url).content)
		except:
			pass
	open(post_id + "/t/index.html", 'wb').write(tostring(page_html.getroot()))

########################################################################
# Extract posts from HTML (replaces dump.sh)
def post_split(thr_id):
    ret = []
    page_html = parse("index.html").getroot()
    posts = page_html.find_class("post")
    for p in posts:
		data = {'id':"",'subj':"",'name':"",'time':"",'img':"",'msg':""}

		data['id']   = p.find_class("postInfo")[0].get("id").replace("pi", "")
		try:
			data['subj'] = p.find_class("subject")[0].text_content()
		except:
			pass
		data['name'] = p.find_class("name")[0].text_content()
		data['time'] = p.find_class("dateTime")[0].get("data-utc")
		try:
			data['img']  = p.find_class("fileThumb")[0].get("href").replace("images/", "")
		except:
			pass
		data['msg']  = p.find_class("postMessage")[0]
		for e in list(data['msg'].iter()):
			if e.tag == "br":
				if e.tail:
					e.tail = "\n" + e.tail
				else:
					e.tail = "\n"

		data['msg'] = data['msg'].text_content()

		ret.append(data)
    return ret

########################################################################
# Dumps post list from post_split as text.
def dump_text(out_file, post_list):
	f = open(out_file, "wb")
	for p in post_list:
		header = p['name'] + " | " + p['time'] + " | No." + p['id']
		if p['subj'] != "":
			header = p['subj'] + " | " + header
		f.write(header + "\n")
		if p['img'] != "":
			f.write(p['img'] + "\n")
		f.write(p['msg'] + "\n")
		f.write("----------------------------------\n")

########################################################################
# Dumps post list from post_split as mediawiki markup.
def dump_mediawiki_markup(out_file, post_list, post_id):
	f = open(out_file, "wb")
	f.write(("<mediawiki xml:lang=\"en\"><page><title>Thread " + post_id + "</title><revision><text>").encode('utf-8'))
	f.write(("&lt;!-- Autogenerated by 4ch-to-mw.py --&gt;\n").encode('utf-8'))
	for p in post_list:
		timestamp = datetime.datetime.fromtimestamp(int(p['time'])).strftime("%Y/%m/%d %H:%M:%S")
		header = p['name'] + " " + timestamp + " No." + p['id']
		if p['subj'] != "":
			header = p['subj'] + " " + header
		f.write(("&lt;b&gt;" + header + "&lt;/b&gt;\n").encode('utf-8'))
		if p['img'] != "":
			f.write("[[File:" + p['img'] + "|thumb|left|200x200px]]\n")
		f.write("&lt;pre style='font-family: sans-serif;'&gt;\n")
		encoded_msg = p['msg'].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
		f.write((encoded_msg + "\n").encode('utf-8'))
		f.write("&lt;/pre&gt;\n")
		f.write(("----------------------------------\n").encode('utf-8'))
	f.write(("</text></revision></page></mediawiki>").encode('utf-8'))

########################################################################
# Retrieves references from within text as a list.
def get_refs(post):
	ref_re = re.compile('>>[0-9]+')
	refs = ref_re.findall(post['msg'])
	ret = []
	if refs:
		for r in refs:
			ret.append(r.replace(">>", ""))
	return ret

########################################################################
# Filters post list by name, optionally also by references to a depth.
# If link_level is -1, this means 'resolve all'. If 0 or nil, no refs.
# Any positive number is interpreted as a depth.
def filter_posts(post_list, names, link_level):
	ret = []
	ids = []
	for p in post_list:
		done = False
		for n in names:
			if done:
				break
			if p['name'] == n:
				ids.append(p['id'])
				done = True

	while link_level > 0 or link_level == -1:
		changed = False
		for p in post_list:
			for i in ids:
				if p['id'] == i:
					refs = get_refs(p)
					length = len(ids)
					ids = ids + refs
					ids = list(set(ids))
					if length != len(ids):
						changed = True
		if changed == False:
			break
		if link_level > 0:
			link_level -= 1

	for p in post_list:
		for i in ids:
			if p['id'] == i:
				ret.append(p)
				break

	ret.sort(key=lambda x: x['id'])
	return ret

thr_url   = sys.argv[1]

eof_clip  = re.compile("/$")
head_clip = re.compile("http[s]?://")
suptg     = re.compile("suptg.thisisnotatrueending.com/archive/")
ch4       = re.compile("boards.4chan.org/[a-zA-Z]+/thread/")

foot_url  = eof_clip.sub ("", thr_url)
clip_url  = head_clip.sub("", foot_url)

ch4_id   = ch4.sub  ("", clip_url)
suptg_id = suptg.sub("", clip_url)

check_id  = re.compile("^[0-9]+$")

is_ch4   = check_id.match(ch4_id)
is_suptg = check_id.match(suptg_id)

thr_id = ""

if is_suptg != None:
	print("[4ch-dump] Type: sup/tg/ url")
	print("[4ch-dump] Fetching...")
	fetch_suptg(thr_url, suptg_id)
	thr_id = suptg_id
elif is_ch4 != None:
	print("[4ch-dump] Type: 4chan url")
	print("[4ch-dump] Fetching...")
	fetch_4c(thr_url, ch4_id)
	thr_id = ch4_id
else:
	print("ukn")

print("[4ch-dump] Splitting posts...")
os.chdir(thr_id + "/t")
post_list = post_split(thr_id)

if do_filter:
	print("[4ch-dump] Applying filter...")
	post_list = filter_posts(post_list, filter_names, filter_level)

print("[4ch-dump] Dumping mediawiki text...")
dump_mediawiki_markup(thr_id + ".xml", post_list, thr_id)

print("[4ch-dump] Removing unreferenced images...")
if do_filter and remove_unrelated_images:
	os.rename("images", "images.old")
	os.mkdir("images")
	for p in post_list:
		if p['img'] != "":
			os.rename("images.old/" + p['img'], "images/" + p['img'])

print("[4ch-dump] Deleting old shit...")
os.rename("images", "../images")
os.rename(thr_id + ".xml", "../" + thr_id + ".xml")
os.chdir("..")

shutil.rmtree("t")
