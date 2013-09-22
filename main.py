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
import json
import logging
import urllib

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

class Forms(db.Model):
	user_id = db.IntegerProperty()
	name = db.StringProperty()


class FormComponents(db.Model):
	form_id = db.IntegerProperty()
	component_type = db.StringProperty()
	input_type = db.StringProperty()
	caption = db.StringProperty()
	options = db.StringProperty()
	form_order = db.IntegerProperty()

def gql_json_parser(query_obj):
    all_components = []
    for e in query_obj:
    	form_components = {"name": str(e.key().id()), "id": str(e.key().id()), "type": e.input_type, "caption": e.caption}
    	if e.options:
    		form_components['options'] = json.loads(e.options)
    	all_components.append(form_components)
    all_components.append({"type": "submit", "value": "Spara checklistan!"})
    return all_components




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
class TestHandler(MainHandler):
	def get(self):
		newform = FormComponents()
		newform.form_id = 1
		newform.component_type = "input_field"
		newform.input_type = "text"
		newform.caption = "What is your name?"
		newform.form_order = 1
		newform.put()

		
		self.write(newform.key().id())

class FormHandler(MainHandler):
	def get(self,form_id_path=""):
		if form_id_path:
			form_id = int(form_id_path)
			logging.error(form_id)
			query_data = FormComponents.all().filter('form_id =', form_id).order('form_order')
		else:
			form_id = ""
			logging.error("No form ID")
			query_data = FormComponents.all()
		json_query_data = gql_json_parser(query_data)
		result = {'action': '/pic', 'method': 'post', 'html': json_query_data}
		self.response.headers['Content-Type'] = 'application/json'
		self.response.out.write(json.dumps(result, sort_keys=True, indent=4, separators=(',', ': ')))



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
        if greeting.imagefile1:
        	self.response.headers['Content-Type'] = 'image/jpeg'
        	self.response.out.write(greeting.imagefile1)
        else:
            self.error(404)

class ResizeHandler(MainHandler):
	def get(self):
		self.render("surveys.html")





class DformHandler(MainHandler):
	def get(self, form_id_path=""):
		if form_id_path:
			form_id = int(form_id_path)
			logging.error(form_id)
		else:
			form_id = ""
			logging.error("No form ID")

		self.render("testar-dform.html", form_id = form_id)

class BuilderHandler(MainHandler):
	def get(self):
		self.render("formbuilder.html")

	def post(self):
		new_form = Forms()
		new_form.user_id = 1
		new_form.put()

		form_id = new_form.key().id()

		form_elements = json.loads(urllib.unquote_plus(self.request.body))
		logging.error('Opened JSON: ')
		logging.error(form_elements)
		logging.error(type(form_elements))
		if isinstance(form_elements, list) and form_elements != []:
			logging.error("It is a list, and it's not empty")
			i = 0
			for elm in form_elements:
				logging.error(type(elm))
				i += 1
				newfc = FormComponents()
				newfc.component_type = 'input_field'
				newfc.form_id = form_id
				if elm['input_type'] == 'input_text':
					newfc.input_type = 'text'
				if elm['input_type'] == 'radio':
					newfc.input_type = 'radiobuttons'
				newfc.caption = elm['caption']
				if elm['input_type'] == 'file':
					newfc.input_type = 'file'
				newfc.caption = elm['caption']

				newfc.form_order = i
				if 'options' in elm.keys():
					newfc.options = json.dumps(elm['options'])
				logging.error("Option i dict?")
				logging.error('options' in elm.keys())
				newfc.put()


		#for elm in form_elements

		logging.error(self.request.body)
		
		self.write(form_id)


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
			imagelist = ['imagedata1','imagedata2','imagedata3','imagedata4','imagedata5']
			for o in output:
				if o[0] in imagelist:
					continue
				setattr(se,o[0],o[1])
			image1 = self.request.get('imagedata1')
			image2 = self.request.get('imagedata2')
			image3 = self.request.get('imagedata3')
			image4 = self.request.get('imagedata4')
			image5 = self.request.get('imagedata5')

			if image1:
				image1 = image1.split(',')[1]
				image1 = str(image1)
				image1 = base64.b64decode(image1)
				se.imagefile1 = db.Blob(image1)
			if image2:
				image2 = image2.split(',')[1]
				image2 = str(image2)
				image2 = base64.b64decode(image2)
				se.imagefile2 = db.Blob(image2)
			if image3:
				image3 = image3.split(',')[1]
				image3 = str(image3)
				image3 = base64.b64decode(image3)
				se.imagefile3 = db.Blob(image3)
			if image4:
				image4 = image4.split(',')[1]
				image4 = str(image4)
				image4 = base64.b64decode(image4)
				se.imagefile4 = db.Blob(image4)
			if image5:
				image5 = image5.split(',')[1]
				image5 = str(image5)
				image5 = base64.b64decode(image5)
				se.imagefile5 = db.Blob(image5)
			se.put()
			self.write(se.key().id())



        






app = webapp2.WSGIApplication([
    ('/', ResizeHandler),
    ('/submissions', InputHandler),
    ('/pic', SubmitExpando),
    ('/image', ImageHandler),
    ('/resize', ResizeHandler),
    ('/getform/?', FormHandler),
    ('/getform/([0-9]+)', FormHandler),
    ('/test', TestHandler),
    ('/formbuilder', BuilderHandler),
    ('/dform/?', DformHandler),
    ('/dform/([0-9]+)', DformHandler)
], debug=True)
