#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import webapp2
import os
from google.appengine.ext import db
from google.appengine.api import images
import jinja2
import base64

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir), autoescape=True)


class Surveys(db.Model):
	name = db.StringProperty(required = True)
	text = db.TextProperty(required = True)
	image = db.BlobProperty()
	created = db.DateTimeProperty(auto_now_add = True)

class Submission(db.Expando):
	image = db.BlobProperty()
	created = db.DateTimeProperty(auto_now_add = True)



class MainHandler(webapp2.RequestHandler):
    def get(self):
        self.response.write('Hello world!')

    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        t = jinja_env.get_template(template)
        return t.render(params)

    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))

class InputHandler(MainHandler):
	def get(self):
		surveys = Surveys.all()
		surveys = list(surveys)
		self.render('front.html', surveys = surveys)


	def post(self):
		name = self.request.get('name')
		text = self.request.get('text')
		
		if name and text:
			s = Surveys(name = name, text = text)
			s.put()
			self.response.write('true')


class PictureTester(MainHandler):
	def get(self):

		self.render("upload.html")

	def post(self):
		firstname = self.request.get('firstname')
		lastname = self.request.get('lastname')
		image = self.request.get('file')
		image = image.split(',')[1]
		image = str(image)
		image = base64.b64decode(image)
		
		if firstname and lastname:
			self.write(firstname + lastname)
			
			s = Surveys(name = firstname, text = lastname)
			s.image = db.Blob(image)
			s.put()
			#id = s.key().id()
			self.write("true")
		else:
			self.write("no submission")

class ImageHandler(MainHandler):
    def get(self):
        greeting = Submission.get_by_id(int(self.request.get('id')))
        if greeting.image:
        	self.response.headers['Content-Type'] = 'image/jpeg'
        	self.response.out.write(greeting.image)
        else:
            self.error(404)

class ResizeHandler(MainHandler):
	def get(self):
		self.render("surveys.html")

class TestHandler(MainHandler):
	def get(self):
		self.render("megapix.html")

class SubmitExpando(MainHandler):
	def get(self):
		variable_list = self.request.arguments()
		output = []
		for e in variable_list:
			query = self.request.get(e)
			result = (e,query)
			output.append(result)
		self.write(output)




	def post(self):
		variable_list = self.request.arguments()
		if variable_list:
			output = []
			for e in variable_list:
				query = self.request.get(e)
				result = (e,query)
				output.append(result)
			se = Submission()
			for o in output:
				if o[0] == "file":
					continue
				setattr(se,o[0],o[1])
			image = self.request.get('file')
			if image:
				image = image.split(',')[1]
				image = str(image)
				image = base64.b64decode(image)
				se.image = db.Blob(image)
			se.put()
			self.write(se.key().id())



        






app = webapp2.WSGIApplication([
    ('/', ResizeHandler),
    ('/submissions', InputHandler),
    ('/pic', SubmitExpando),
    ('/image', ImageHandler),
    ('/resize', ResizeHandler),
    ('/test', TestHandler)
], debug=True)
