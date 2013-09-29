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

class Submissions(db.Expando):
	form_id = db.IntegerProperty()
	image = db.BlobProperty()
	created = db.DateTimeProperty(auto_now_add = True)


class Forms(db.Model):
	user_id = db.IntegerProperty()
	name = db.StringProperty()
	created = db.DateTimeProperty(auto_now_add = True)


class FormComponents(db.Model):
	form_id = db.IntegerProperty()
	component_type = db.StringProperty()
	input_type = db.StringProperty()
	caption = db.StringProperty()
	options = db.StringProperty()
	form_order = db.IntegerProperty()

	@classmethod
	def get_by_form_id(cls,form_id):
		return FormComponents.all().filter('form_id =', form_id).order('form_order')

def gql_json_parser(query_obj, form_id):
    all_components = []
    for e in query_obj:
    	form_components = {"name": str(e.key().id()), "id": str(e.key().id()), "type": e.input_type, "caption": e.caption}
    	if e.options:
    		form_components['options'] = json.loads(e.options)
    	if e.input_type == 'file':
    		form_components['class'] = 'image_file'
    	all_components.append(form_components)
    all_components.append({"type": "hidden","name": "form_id", "value": str(form_id)})
    all_components.append({"type": "reset", "value": "Aterstall checklistan"})
    all_components.append({"type": "submit", "value": "Spara checklistan!"})
    return all_components

def generate_frmb_json(query_obj):
    all_components = []
    for e in query_obj:
        form_components = {"required": "undefined", "id": str(e.key().id())} #, 
        if e.input_type == 'radiobuttons':
        	form_components['title'] = e.caption
        	form_components['cssClass'] = "radio"
        	#transforming the dictionary to something jQuery Formbuilder can understand
    		d = json.loads(e.options)
    		logging.error(d)
    		values = {}
    		i = 1
    		for k,v in d.items():
    			i += 1
    			values[i] = {"value": v, "baseline": "false"}
    		form_components['values'] = values
    		logging.error(values)
    	if e.input_type == 'text':
    		form_components['cssClass'] = "input_text"
    		form_components['values'] = e.caption
    	if e.input_type == 'file':
    		form_components['cssClass'] = "file"
    		form_components['values'] = e.caption
    	


    	all_components.append(form_components)
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
			query_data = FormComponents.get_by_form_id(form_id)
		else:
			form_id = ""
			logging.error("No form ID")
			query_data = FormComponents.all().order('form_order')
		json_query_data = gql_json_parser(query_data, form_id)
		result = {'action': '/pic', 'method': 'post', 'html': json_query_data}
		self.response.headers['Content-Type'] = 'application/json'
		self.response.out.write(json.dumps(result, sort_keys=True, indent=4, separators=(',', ': ')))

class LoadFormHandler(MainHandler):
	def get(self,form_id_path=""):
		if form_id_path:
			form_id = int(form_id_path)
			logging.error(form_id)
			query_data = FormComponents.get_by_form_id(form_id)

		else:
			form_id = ""
			logging.error("No form ID")
			query_data = FormComponents.all().order('form_order')
		result = generate_frmb_json(query_data)
		output = {}
		output['form_id'] = form_id
		output['form_structure'] = result
		self.response.headers['Content-Type'] = 'application/json'
		self.response.out.write(json.dumps(output, sort_keys=True, indent=4, separators=(',', ': ')))

class SubmissionsHandler(MainHandler):
	def get(self,form_id_path=""):
		if form_id_path:
			form_id = int(form_id_path)
			logging.error(form_id)
			submitted_entries = Submissions.all().filter('form_id =', form_id).order('created')
			if submitted_entries:
				submitted_entries = list(submitted_entries)
			query_data = FormComponents.get_by_form_id(form_id)
			if query_data:
				query_data = list(query_data)
			headers = [e.caption for e in query_data]
			question_ids = [ e.key().id() for e in query_data]
			se = [ s.key().id() for s in submitted_entries]
			output = []
			for e in submitted_entries:
				result = []
				for q in question_ids:
					try:
						result.append(getattr(e, str(q)))
					except AttributeError:
						result.append("---")
				output.append(result)
			#self.write(str(headers) + "\n" + str(output))
			self.render("front.html", output = output, headers = headers)
		else:
			form_id = ""
			logging.error("No form ID")
			self.write("No form ID")
			query_data = FormComponents.all().order('form_order')

class ImageHandler(MainHandler):
    def get(self):
        greeting = Submissions.get_by_id(int(self.request.get('id')))
        if greeting.imagefile1:
        	self.response.headers['Content-Type'] = 'image/jpeg'
        	self.response.out.write(greeting.imagefile1)
        else:
            self.error(404)

class FrontHandler(MainHandler):
	def get(self, form_id_path=""):
		if form_id_path:
			form_id = int(form_id_path)
			logging.error(form_id)
		else:
			form_id = ""
			logging.error("No form ID")
		self.render("mainfile.html", form_id = form_id)





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
	def get(self, form_id_path=""):
		if form_id_path:
			form_id = int(form_id_path)
			logging.error(form_id)
		else:
			form_id = ""
			logging.error("No form ID")
			#self.write("No form with that ID number")
		self.render("formbuilder.html", form_id = form_id)


	def post(self):
		log = logging.error
		form_data = json.loads(urllib.unquote_plus(self.request.body))
		
		if form_data["form_id"] and form_data["form_id"].isdigit():
			log("yay we have an ID")
			form = Forms.get_by_id(int(form_data["form_id"]))
			if form:
				form_id = int(form_data["form_id"])
			else:
				self.write("No such ID in DB")
		else:
			log("we have to get a new form ID")
			new_form = Forms()
			new_form.user_id = 1
			new_form.put()
			form_id = new_form.key().id()
		log(str(form_id))
		form_elements = form_data['html']
		if isinstance(form_elements, list) and form_elements != []:
			logging.error("It is a list, and it's not empty")
			i = 0
			for elm in form_elements:
				if elm['id'] == "undefined":
					log("ID is undef")
					newfc = FormComponents()
				elif elm['id'].isdigit():
					log("This element has an ID: " + elm['id'])
					newfc = FormComponents.get_by_id(int(elm['id']))
					if not newfc:
						log("not in DB. create new Form Compontent entity")
						newfc = FormComponents()
				i += 1
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
				newfc.put()
		self.write(form_id)

class OverviewHandler(MainHandler):
	def get(self):
		forms = Forms.all()
		self.render("forms.html", forms = forms)


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
			se = Submissions()
			imagelist = ['imagedata1','imagedata2','imagedata3','imagedata4','imagedata5']
			for o in output:
				if o[0] in imagelist:
					continue
				if o[0] == "form_id":
					logging.error("Form ID is: " + o[1])
					se.form_id = int(o[1])
					continue
				if o[0][:9] == "imagedata":
					logging.error("image file: " + str(o[1]))
					imagefile = o[1]
					imagefile = imagefile.split(',')[1]
					imagefile = str(imagefile)
					imagefile = base64.b64decode(imagefile)
					a = "image"
					se.file[a] = db.Blob(imagefile)
					continue
				setattr(se,o[0],o[1])
			se.put()
			self.write(se.key().id())


class DrawHandler(MainHandler):
	def get(self):
		self.render("drawingboard.html")
        






app = webapp2.WSGIApplication([
    ('/?', FrontHandler),
    ('/([0-9]+)', FrontHandler),
    ('/submissions', SubmissionsHandler),
    ('/submissions/([0-9]+)', SubmissionsHandler),
    ('/pic', SubmitExpando),
    ('/image', ImageHandler),
    ('/getform/?', FormHandler),
    ('/getform/([0-9]+)', FormHandler),
    ('/loadform/?', LoadFormHandler),
    ('/loadform/([0-9]+)', LoadFormHandler),
    ('/test', TestHandler),
    ('/formbuilder', BuilderHandler),
    ('/formbuilder/([0-9]+)', BuilderHandler),
    ('/dform/?', DformHandler),
    ('/dform/([0-9]+)', DformHandler),
    ('/draw', DrawHandler),
    ('/forms', OverviewHandler)

], debug=True)
