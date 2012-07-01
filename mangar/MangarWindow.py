# -*- Mode: Python; coding: utf-8; indent-tabs-mode: nil; tab-width: 4 -*-
### BEGIN LICENSE
# Copyright (C) 2012 Chris Triantafillis <christriant1995@gmail.com>
# This program is free software: you can redistribute it and/or modify it 
# under the terms of the GNU General Public License version 3, as published 
# by the Free Software Foundation.
# 
# This program is distributed in the hope that it will be useful, but 
# WITHOUT ANY WARRANTY; without even the implied warranties of 
# MERCHANTABILITY, SATISFACTORY QUALITY, or FITNESS FOR A PARTICULAR 
# PURPOSE.  See the GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License along 
# with this program.  If not, see <http://www.gnu.org/licenses/>.
### END LICENSE

import gettext
from gettext import gettext as _
gettext.textdomain('mangar')

from gi.repository import Gtk # pylint: disable=E0611
from gi.repository import Gio # pylint: disable=E0611
from gi.repository import Gdk

import logging
logger = logging.getLogger('mangar')

from mangar_lib import Window
from mangar.AboutMangarDialog import AboutMangarDialog
from mangar.PreferencesMangarDialog import PreferencesMangarDialog

import time
import urllib2
import os
import tempfile
import zipfile
import subprocess
import shutil
import pickle

home = os.getenv('HOME')
images_folder = home + "/.config/mangar/"
extensions = [ ".cbz", ".cbr", ".cb7" ]
collection = {}


# See mangar_lib.Window.py for more details about how this class works
class MangarWindow(Window):
    __gtype_name__ = "MangarWindow"
    
    def finish_initializing(self, builder): # pylint: disable=E1002
        """Set up the main window"""
        super(MangarWindow, self).finish_initializing(builder)
        self.AboutDialog = AboutMangarDialog
        self.PreferencesDialog = PreferencesMangarDialog
		self.settings = Gio.Settings("net.launchpad.mangar")
		self.collection_folder = self.settings.get_string("collectionfolder")
		self.output_folder = self.settings.get_string("outputfolder")
        
        collection = self.load_collection()
        self.set_collection_to_collectiontreeview(collection)
        
        modecombo = self.builder.get_object("modecombobox")
        modecombo.set_active(0)
        self.notebook = self.builder.get_object("notebook")
        self.notebook.set_current_page(0)
                
        self.tempfolder = tempfile.mkdtemp()
        print self.tempfolder
        self.images = []
		
        # Code for other initialization actions should be added here.

    def my_on_mangatreeview_cursor_changed(self, widget, user_param=None):
        waitlabel = self.builder.get_object("waitlabel")
        waitlabel.show()
		manga = self.get_selected_manga(0)
		url = self.get_manga_url(manga)
		episode = self.get_last_episode(url)
		self.set_episodes_to_treeview(manga, episode)
        waitlabel.hide()
        
    def my_on_episodetreeview_row_activated(self, widget, path, user_param=None):
        waitlabel = self.builder.get_object("waitlabel")
        waitlabel.show()
        time.sleep(2)
		manga = self.get_selected_manga(0)
		manga_url = self.get_manga_url(manga)
		episode_number = self.get_selected_episode()
		first_episode_line = self.find_first_episode_line(manga, manga_url)

		episode_line = ""
		if manga == "High School of the Dead":
			episode_line = self.get_episode_line(manga, manga_url, first_episode_line, episode_number, True)
		elif manga == "Kimi Ni Todoke":
			episode_line = self.get_episode_line(manga, manga_url, first_episode_line, episode_number, True)
		else:
			episode_line = self.get_episode_line(manga, manga_url, first_episode_line, episode_number, False)
			
		episode_url = self.get_episode_url(manga_url, episode_line)
		final_episode_url = "http://www.mangareader.net" + episode_url
		pages_number = self.get_pages(final_episode_url)
		self.set_pages_to_combobox(pages_number)
		i = 1
		episodes_url = final_episode_url
		self.images = []
		while ( i != pages_number + 1):
			self.download_image(episodes_url, manga, episode_number, i)
			episodes_url = final_episode_url
			i = i + 1
			episodes_url = episodes_url + "/" + str(i)
		self.ui.mangaimage.set_from_file(self.images[0])
		scrolledwindow = self.builder.get_object("imagescrolledwindow")
		scrolledwindow.set_property("min-content-width", 900)
        time.sleep(1)
        waitlabel.hide()
		
	def my_on_previousbutton_clicked(self, button, user_param=None):
		page = self.ui.pagescellrenderer.get_property("text")
		page = int(page)
		print("page is {0}".format(page))
		mangaimage = self.builder.get_object("mangaimage")
		combobox = self.builder.get_object("pagecombobox")
		if page != 1:
			previous_page = page - 1
			self.notebook = self.builder.get_object("notebook")
			notebookpage = self.notebook.get_current_page()
			if notebookpage == 0:
				ppage = previous_page - 1
				print self.images[ppage]
				self.ui.mangaimage.set_from_file(self.images[ppage])
				combobox.set_active(ppage)
			else:
				manga = self.get_selected_manga(1)
				ppage = previous_page - 1
				image = self.images[page]
				path = self.tempfolder + "/" + manga + "/" + image
				mangaimage.set_from_file(path)
				combobox.set_active(ppage)
				
		
	def my_on_nextbutton_clicked(self, button, user_param=None):
		page = self.ui.pagescellrenderer.get_property("text")
		page = int(page)
		print("page is {0}".format(page))
		mangaimage = self.builder.get_object("mangaimage")
		combobox = self.builder.get_object("pagecombobox")
		pages_number = combobox.get_row_span_column()
		if page != pages_number:
			next_page = page + 1
			print("next page is {0}".format(next_page))
			self.notebook = self.builder.get_object("notebook")
			notebookpage = self.notebook.get_current_page()
			if notebookpage == 0:
				image = self.images[page]
				print("image is {0}".format(image))
				mangaimage.clear()
				mangaimage.set_from_file(image)
			else:
				manga = self.get_selected_manga(1)
				image = self.images[page]
				path = self.tempfolder + "/" + manga + "/" + image
				mangaimage.clear()
				mangaimage.set_from_file(path)
			combobox.set_active(page)
				
	def my_on_pagecombobox_changed(self, combobox, param=None):
		self.notebook = self.builder.get_object("notebook")
		notebookpage = self.notebook.get_current_page()
		imagewidget = self.builder.get_object("mangaimage")		
		page = int(combobox.get_active())
		if notebookpage == 0:
			imagewidget.set_from_file(self.images[page])
		else:
			manga = self.get_selected_manga(1)
			page = int(page)
			image = self.images[page]
			path = self.tempfolder + "/" + manga + "/" + image
			imagewidget.set_from_file(path)
			scrolledwindow = self.builder.get_object("imagescrolledwindow")
			scrolledwindow.set_property("min-content-width", 900)
			
	def my_on_modecombobox_changed(self, combobox, param=None):
		self.notebook = self.builder.get_object("notebook")
		mode = combobox.get_active()
		if mode == 0:
			self.notebook.set_current_page(0)
		else:
			self.notebook.set_current_page(1)
			
	def my_on_collectiontreeview_row_activated(self, widget, path, param=None):
		collectiontree = self.builder.get_object("collectiontreeview")
		treeselection = collectiontree.get_selection()
		treemodel, treeiter = treeselection.get_selected()
		manga = treemodel.get_value(treeiter, 0)
		#location = collection[manga]
		location = self.collection_folder + "/" + manga
		folder = self.tempfolder + "/" + manga
		if not os.path.exists(folder):
			os.mkdir(folder, 0700)
		self.uncompress_manga(location, folder)
		images = self.scan_images(folder)
		pages = len(images)
		self.set_pages_to_combobox(pages)
		path = folder + "/" + self.images[0]
		imagewidget = self.builder.get_object("mangaimage")
		imagewidget.set_from_file(path)
			
	def my_on_scan_menuitem_activate(self, item , param=None):
		collection = self.scan_collection(self.collection_folder)
		collection_array = []
		for key in collection:
			collection_array.append(key)
		self.store_collection(collection)
		self.set_collection_to_collectiontreeview(collection_array)
	
	def my_on_hidemenuitem_toggled(self, checkitem, param=None):
		checkitem = self.builder.get_object("hidemenuitem")
		button = self.builder.get_object("hidebutton")
		box = self.builder.get_object("box3")
		if checkitem.get_active() is True:
			box.hide()
			button.set_active(True)
		else:
			box.show()
			button.set_active(False)
			
	def my_on_hidebutton_toggled(self, button, param=None):
		button = self.builder.get_object("hidebutton")
		checkitem = self.builder.get_object("hidemenuitem")
		box = self.builder.get_object("box3")
		if button.get_active() is True:
			box.hide()
			checkitem.set_active(True)
		else:
			box.show()
			checkitem.set_active(False)
		
	def my_on_fullscreenbutton_toggled(self, button, param=None):
		button = self.builder.get_object("fullscreenbutton")
		window = self.builder.get_object("mangar_window")
		toolbar = self.builder.get_object("toolbar1")
		checkitem = self.builder.get_object("fullscreenmenuitem")
		if button.get_active() is True:
			window.fullscreen()
			checkitem.set_active(True)
		else:
			window.unfullscreen()
			checkitem.set_active(False)
		
	def my_on_fullscreenmenuitem_toggled(self, checkitem, param=None):
		checkitem = self.builder.get_object("fullscreenmenuitem")
		button = self.builder.get_object("fullscreenbutton")
		window = self.builder.get_object("mangar_window")
		toolbar = self.builder.get_object("toolbar1")
		if checkitem.get_active() is True:
			window.fullscreen()
			button.set_active(True)
		else:
			window.unfullscreen()
			button.set_active(False)
		
	def my_on_mangar_window_key_press_event(self, widget, event, param=None):
		window = self.builder.get_object("mangar_window")
		button = self.builder.get_object("fullscreenbutton")
		checkitem = self.builder.get_object("fullscreenmenuitem")
		scrolled = self.builder.get_object("imagescrolledwindow")
		viewport = self.builder.get_object("viewport1")
		keyname = Gdk.keyval_name(event.keyval)
		if keyname == "Right":
			button = self.builder.get_object("nextbutton")
			self.my_on_nextbutton_clicked(button, None)
		elif keyname == "Left":
			button = self.builder.get_object("previousbutton")
			self.my_on_previousbutton_clicked(button, None)
		elif keyname == "Escape" and button.get_active() is True:
			button.set_active(False)
			checkitem.set_active(False)
		
	def my_on_mangar_window_destroy(self, widget, param=None):
		shutil.rmtree(self.tempfolder)
	
	def get_page_source(self, page):
		usock = urllib2.urlopen(page)
		data = usock.read()
		usock.close()
		return data
		
	def get_selected_manga(self, mode):
		mangatree = self.builder.get_object("mangatreeview")
		collectiontree = self.builder.get_object("collectiontreeview")
		
		if mode == 0:
			treeselection = mangatree.get_selection()
		else:
			treeselection = collectiontree.get_selection()
			
		treemodel, treeiter = treeselection.get_selected()
		value = treemodel.get_value(treeiter, 0)
		return value
		
	def get_selected_episode(self):
		treeselection = self.ui.episodetreeview.get_selection()
		treemodel, treeiter = treeselection.get_selected()
		value = treemodel.get_value(treeiter, 0)
		return value
		
	def get_manga_url(self, manga):
		if manga == "1/2 Prince":
			url = "http://www.mangareader.net/278/12-prince.html"
			return url 
		elif manga == "Ao No Exorcist":
			url = "http://www.mangareader.net/406/ao-no-exorcist.html"
			return url
		elif manga == "Bakuman":
			url = "http://www.mangareader.net/219/bakuman.html"
			return url
		elif manga == "Beelzebub":
			url = "http://www.mangareader.net/222/beelzebub.html"
			return url
		elif manga == "Black Bird":
			url = "http://www.mangareader.net/1003/black-bird.html"
			return url
		elif manga == "Bleach":
			url = "http://www.mangareader.net/94/bleach.html"
			return url
		elif manga == "Boku kara Kimi ga Kienai":
			url = "http://www.mangareader.net/798/boku-kara-kimi-ga-kienai.html"
			return url
		elif manga == "Claymore":
			url = "http://www.mangareader.net/485/claymore.html"
			return url
		elif manga == "Deadman Wonderland":
			url = "http://www.mangareader.net/666/deadman-wonderland.html"
			return url
		elif manga == "Dengeki Daisy":
			url = "http://www.mangareader.net/123/dengeki-daisy.html"
			return url
		elif manga == "D.Gray-Man":
			url = "http://www.mangareader.net/210/dgray-man.html"
			return url
		elif manga == "Fairy Tail":
			url = "http://www.mangareader.net/135/fairy-tail.html"
			return url
		elif manga == "Faster than a Kiss":
			url = "http://www.mangareader.net/148/faster-than-a-kiss.html"
			return url
		elif manga == "Freezing":
			url = "http://www.mangareader.net/400/freezing.html"
			return url
		elif manga == "Gantz":
			url = "http://www.mangareader.net/97/gantz.html"
			return url
		elif manga == "Hadashi De Bara Wo Fume":
			url = "http://www.mangareader.net/374/hadashi-de-bara-wo-fume.html"
			return url
		elif manga == "Hapi Mari":
			url = "http://www.mangareader.net/436/hapi-mari.html"
			return url
		elif manga == "High School of the Dead":
			url = "http://www.mangareader.net/170/high-school-of-the-dead.html"
			return url
		elif manga == "Historys Strongest Disciple Kenichi":
			url = "http://www.mangareader.net/337/historys-strongest-disciple-kenichi.html"
			return url
		elif manga == "Kaichou wa Maid-sama!":
			url = "http://www.mangareader.net/147/kaichou-wa-maid-sama.html"
			return url
		elif manga == "Katekyo Hitman Reborn!":
			url = "http://www.mangareader.net/284/katekyo-hitman-reborn.html"
			return url
		elif manga == "Kimi Ni Todoke":
			url = "http://www.mangareader.net/280/kimi-ni-todoke.html"
			return url
		elif manga == "Kuroshitsuji":
			url = "http://www.mangareader.net/102/kuroshitsuji.html"
			return url
		elif manga == "Kyou Koi wo Hajimemasu":
			url = "http://www.mangareader.net/145/kyou-koi-wo-hajimemasu.html"
			return url
		elif manga == "Love Berrish":
			url = "http://www.mangareader.net/550/love-berrish.html"
			return url
		elif manga == "Love So Life":
			url = "http://www.mangareader.net/652/love-so-life.html"
			return url
		elif manga == "My Boyfriend is a Vampire":
			url = "http://www.mangareader.net/1699/my-boyfriend-is-a-vampire.html"
			return url
		elif manga == "Naruto":
			url = "http://www.mangareader.net/93/naruto.html"
			return url
		elif manga == "Obaka-chan Koigatariki":
			url = "http://www.mangareader.net/718/obaka-chan-koigatariki.html"
			return url
		elif manga == "One Piece":
			url = "http://www.mangareader.net/103/one-piece.html"
			return url
		elif manga == "Pandora Hearts":
			url = "http://www.mangareader.net/350/pandora-hearts.html"
			return url
		elif manga == "Rosario-Vampire II":
			url = "http://www.mangareader.net/319/rosario-vampire-ii.html"
			return url
		elif manga == "Say I love You":
			url = "http://www.mangareader.net/1145/say-i-love-you.html"
			return url
		elif manga == "Sekirei":
			url = "http://www.mangareader.net/163/sekirei.html"
			return url
		elif manga == "Skip Beat":
			url = "http://www.mangareader.net/117/skip-beat.html"
			return url
		elif manga == "Soul Eater":
			url = "http://www.mangareader.net/157/soul-eater.html"
			return url
		elif manga == "Stardust Wink":
			url = "http://www.mangareader.net/594/stardust-wink.html"
			return url
		elif manga == "The Breaker: New Waves":
			url = "http://www.mangareader.net/the-breaker-new-waves"
			return url
		elif manga == "Vampire Knight":
			url = "http://www.mangareader.net/104/vampire-knight.html"
			return url
		elif manga == "Watashi ni xx Shinasai!":
			url = "http://www.mangareader.net/440/watashi-ni-xx-shinasai.html"
			return url
		
		
	def get_last_episode(self, url):
		data = self.get_page_source(url)
		lines = data.split("\n")
		line = lines[127]
		lastindex = line.index('">')
		firstindex = lastindex - 4
		result = line[firstindex:lastindex]
		final = ""
		for i in result:
			if i.isdigit():
				final += i
		return final
		
	def set_episodes_to_treeview(self, manga, episode):
	    self.ui.episodestore.clear()
		episode_int = int(episode)
		while ( episode_int != 0 ):
			if manga == "One Piece":
				if episode_int == 265:
					episode_int = (episode_int - 1)
					continue
				elif episode_int == 309:
					episode_int = (episode_int - 1)
					continue
			elif manga == "Freezing" and episode_int == 71:
				episode_int = (episode_int - 1)
				continue
			elif manga == "High School of the Dead":
				if episode_int == 1:
					self.ui.episodestore.append([1])
					self.ui.episodestore.append([0])
					break
			elif manga == "Kimi Ni Todoke":
				if episode_int == 1:
					self.ui.episodestore.append([1])
					self.ui.episodestore.append([0])
					break
            self.ui.episodestore.append([episode_int])
			episode_int = (episode_int - 1)
			
	def find_first_episode_line(self, manga, manga_url):
		if manga == "Bakuman":
			return 169
		elif manga == "Stardust Wink":
			return 168
		else:
			data = self.get_page_source(manga_url)
			lines = data.split("\n")
			line = ""
			for i in range(156, 166):
				if lines[i].startswith("<a") is True:
					line = i
			return line
	
	def get_episode_line(self, manga, manga_url, first_episode_line, episode, has_episode_zero):
		if has_episode_zero is True:
			episode_line = first_episode_line + ((episode)*6)
			return episode_line
		elif ( manga == "One Piece" and episode > 265 ):
			if episode > 309:
				episode_line = first_episode_line + ((episode - 3)*6)
				return episode_line
			else:
				episode_line = first_episode_line + ((episode - 2)*6)
				return episode_line
		elif ( manga == "Freezing" and episode > 71 ):
				episode_line = first_episode_line + ((episode - 2)*6)
				return episode_line
		else:
			episode_line = first_episode_line + ((episode - 1)*6)
			return episode_line
			
	def get_episode_url(self, manga_url, episode_line):
		data = self.get_page_source(manga_url)
		lines = data.split("\n")
		episode_line = lines[episode_line]
		first_index =  episode_line.index('/')
		last_index = episode_line.index('">')
		episode_url = episode_line[first_index:last_index]
		return episode_url
		
	def get_pages(self, episode_url):
		data = self.get_page_source(episode_url)
		lines = data.split("\n")
		line = ""
		for i in range( 115, 199 ):
			if lines[i].startswith("</select") is True:
				line = lines[i]
		last_index = line.index("</div>")
		first_index = last_index - 2
		pages_number = line[first_index:last_index]
		pages_number_int = int(pages_number)
		return pages_number_int

	def set_pages_to_combobox(self, pages_number):
		self.ui.pagesstore.clear()
		while ( pages_number != 0 ):
			self.ui.pagesstore.prepend([pages_number])
			if pages_number == 1:
				break
			pages_number = pages_number - 1
		self.ui.pagecombobox.set_active(0)
		
	def download_image(self, url, manga, episode, page):
		data = self.get_page_source(url)
		lines = data.split("\n")
		line = ""
		image_url = ""
		for i in range(136, 199):
			if lines[i].startswith('<div id="imgholder">') is True:
				line = lines[i]
				try:
					first_index = line.index("http://")
					last_index = line.index('" alt')
					image_url = line[first_index:last_index]
				except ValueError:
					i = i + 1
					line = lines[i]
					first_index = line.index("http://")
					last_index = line.index('" alt')
					image_url = line[first_index:last_index]
		episode = str(episode)
		page = str(page)
		image_path = self.tempfolder +"/" + manga + "-" + episode + "-" + page + ".jpg"
		f = open(image_path, 'wb')
		f.write(urllib2.urlopen(image_url).read())
		f.close()
		self.images.append(image_path)
		
	def scan_collection(self, collection_folder):
		for path, subdirs, files in os.walk(collection_folder):
			for name in files:
				manga = os.path.join(path, name)
				extension = os.path.splitext(manga)[1]
				if extension in extensions:
					name = os.path.basename(manga)
					collection[name] = manga
				else:
					pass
		return collection
		
	def set_collection_to_collectiontreeview(self, collection):
		collectionstore = self.builder.get_object("collectionstore")
		collectionstore.clear()
		for key in collection:
			collectionstore.append([key])
			
	def uncompress_manga(self, manga, folder):
		subprocess.call(["file-roller", "-e", folder, manga])
				 
			
	def scan_images(self, location):
		files = os.listdir(location)
		for i in files:
			self.images.append(i)
		self.images = sorted(self.images)
		return self.images

	def store_collection(self, collection):
		collection_file = images_folder + "collection"
		f = open(collection_file, 'wb')
		pickle.dump(collection, f)
		f.close()
		
	def load_collection(self):
		collection = []
		collection_file = images_folder + "collection"
		f = open(collection_file, 'rb')
		try:
			collection = pickle.load(f)
		except EOFError:
			 return collection
		f.close()
		return collection
