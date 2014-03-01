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
from collections import OrderedDict
import jinja2
import base64
import json
import logging
import urllib

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir), autoescape=True)


class Submissions(db.Expando):
	form_id = db.IntegerProperty()
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
	form_order = db.IntegerProperty(indexed = True)
	created = db.DateTimeProperty(auto_now_add = True)

	@classmethod
	def get_by_form_id(cls,form_id):
		return FormComponents.all().filter('form_id =', form_id).order('form_order')

def gql_json_parser(query_obj, form_id):
    all_components = []
    for e in query_obj:
    	if e.input_type == 'radiobuttons' or e.input_type == 'checkbox' and e.options:
    		logging.error(e.options)
    		opts = json.loads(e.options)
    		radio_values = []
    		for elm in opts:
    			if e.input_type == 'radiobuttons':
    				field = {"type": "radio"}
    			if e.input_type == 'checkbox':
    				field = {"type": "checkbox"}
    			field["name"] = str(e.key().id())
    			field["caption"] = elm.capitalize()
    			field["value"] = elm
    			field["id"] = elm
    			radio_values.append(field)
    		form_components = { "type": 'div',"data-role": 'fieldcontain',
    							"html": { "type": 'fieldset',"data-role": "controlgroup", "caption": e.caption, "data-type": "horizontal", "data-mini": "true", "html":  radio_values }}
    	elif e.input_type == "h2":
    		form_components = { "type": e.input_type, "html": e.caption}
    	else:
    		form_components = {"name": str(e.key().id()), "id": str(e.key().id()), "type": e.input_type, "caption": e.caption}
    	if e.input_type == 'file':
    		form_components['class'] = 'image_file'
    	all_components.append(form_components)
    all_components.append({"type": "hidden","name": "form_id", "value": str(form_id)})
    all_components.append({"type": "submit", "value": "Spara checklistan!"})
    return all_components

def generate_frmb_json(query_obj):
    all_components = []
    for e in query_obj:
        form_components = {"required": "undefined", "id": str(e.key().id())} #, 
        if e.input_type == 'radiobuttons':
        	form_components['title'] = e.caption
        	form_components['cssClass'] = "radio"
        	#transforming the options array to something jQuery Formbuilder can understand
    		opts = json.loads(e.options)
    		values = {}
    		i = 1
    		for elm in opts:
    			i += 1
    			values[i] = {"value": elm, "baseline": "false"}
    		form_components['values'] = values
    		logging.error(values)
    	if e.input_type == 'checkbox':
        	form_components['title'] = e.caption
        	form_components['cssClass'] = "checkbox"
        	#transforming the options array to something jQuery Formbuilder can understand
    		opts = json.loads(e.options)
    		values = {}
    		i = 1
    		for elm in opts:
    			i += 1
    			values[i] = {"value": elm, "baseline": "false"}
    		form_components['values'] = values
    		logging.error(values)
    	if e.input_type == 'text':
    		form_components['cssClass'] = "input_text"
    		form_components['values'] = e.caption
    	if e.input_type == 'file':
    		form_components['cssClass'] = "file"
    		form_components['values'] = e.caption
    	if e.input_type == 'h2':
    		form_components['cssClass'] = "headline"
    		form_components['values'] = e.caption
    	if e.input_type == 'textarea':
    		form_components['cssClass'] = "textarea"
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
		fields = FormComponents.all().filter("input_type", "radiobuttons")
		if fields:
			i = 0
			for f in fields:
				d = json.loads(f.options)
				if type(d) == dict:
					self.write(f.key().id())
					#self.write(d)
					opts = []
					for k,v in d.items():
						opts.append(v)
					self.write(opts)
					self.write('<br>')
					i += 1
				f.options = json.dumps(opts)
				f.put()
			self.write(i)

def generate_form_json(form_id_path):
	if form_id_path:
		form_id = int(form_id_path)
		logging.error(form_id)
		query_data = FormComponents.get_by_form_id(form_id)
		form = Forms.get_by_id(form_id)
		if form:
			logging.error(form.name)
			form_name = form.name
	else:
		form_id = ""
		logging.error("No form ID")
		query_data = FormComponents.all().order('form_order')
	json_query_data = gql_json_parser(query_data, form_id)
	result = {'action': '/submit', 'method': 'post', 'html': json_query_data}
	if form_name:
		result['name'] = form_name
	return(json.dumps(result, sort_keys=True, indent=4, separators=(',', ': ')))


class FormHandler(MainHandler):
	def get(self,form_id_path=""):
		if form_id_path:
			self.response.headers['Content-Type'] = 'application/json'
			self.write(generate_form_json(form_id_path))
		"""
		if form_id_path:
			form_id = int(form_id_path)
			logging.error(form_id)
			query_data = FormComponents.get_by_form_id(form_id)
			form = Forms.get_by_id(form_id)
			if form:
				logging.error(form.name)
				form_name = form.name
		else:
			form_id = ""
			logging.error("No form ID")
			query_data = FormComponents.all().order('form_order')
		json_query_data = gql_json_parser(query_data, form_id)
		result = {'action': '/submit', 'method': 'post', 'html': json_query_data}
		if form_name:
			result['name'] = form_name
		self.response.headers['Content-Type'] = 'application/json'
		self.response.out.write(json.dumps(result, sort_keys=True, indent=4, separators=(',', ': ')))"""

class LoadFormHandler(MainHandler):
	def get(self,form_id_path=""):
		if form_id_path:
			form_id = int(form_id_path)
			logging.error(form_id)
			query_data = FormComponents.get_by_form_id(form_id)
			form = Forms.get_by_id(form_id)
			if form:
				logging.error(form.name)
				form_name = form.name

		else:
			form_id = ""
			logging.error("No form ID")
			query_data = FormComponents.all().order('form_order')
		result = generate_frmb_json(query_data)
		output = {}
		if form_name:
			output['form_name'] = form_name
		output['form_id'] = form_id
		output['form_structure'] = result
		self.response.headers['Content-Type'] = 'application/json'
		self.response.out.write(json.dumps(output, sort_keys=True, indent=4, separators=(',', ': ')))

class SubmissionsHandler(MainHandler):
	def get(self,form_id_path=""):
		if form_id_path:
			form_id = int(form_id_path)
			form_data = Forms.get_by_id(form_id)
			form_name = form_data.name

			submitted_entries = Submissions.all().filter('form_id =', form_id).order('created')
			if submitted_entries:
				submitted_entries = list(submitted_entries)
			query_data = FormComponents.all().filter('form_id =', form_id).filter('component_type =','input_field').order('form_order')
			if query_data:
				query_data = list(query_data)
			image_list = FormComponents.all().filter('form_id =', form_id).filter('component_type =','image').order('form_order')
			if image_list:
				image_list = list(image_list)
			images = [il.key().id() for il in image_list]
			headers = [e.caption for e in query_data]
			headers.append("Ta bort")
			question_ids = [e.key().id() for e in query_data]
			se = [ s.key().id() for s in submitted_entries]
			output = []
			image_output = []
			for e in submitted_entries:
				result = []
	
				for q in question_ids:
					try:
						result.append(getattr(e, str(q)))
					except AttributeError:
						result.append("---")
				result.append(str(e.key().id()))		
				output.append(result)
				for img in images:
					try:
						if getattr(e, str(img)):
							image_output.append([e.key().id(),img])
					except AttributeError:
						continue
			logging.error(image_output)
			self.render("front.html", output = output, headers = headers, image_output = image_output, name = form_name)
		else:
			form_id = ""
			logging.error("No form ID")
			self.write("No form ID")

class ImageHandler(MainHandler):
    def get(self):
    	sub_id = int(self.request.get('sub_id'))
    	elm_id = str(self.request.get('elm_id'))
        entry = Submissions.get_by_id(sub_id)
        if entry:
        	image = getattr(entry, elm_id)
        	self.response.headers['Content-Type'] = 'image/jpeg'
        	self.response.out.write(image)
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
		log(form_data)
		if form_data["form_id"] and form_data["form_id"].isdigit():
			log("yay we have an ID")
			form = Forms.get_by_id(int(form_data["form_id"]))
			if form:
				form_id = int(form_data["form_id"])
				if form_data["name"]:
					form.name = form_data["name"]
					form.put()
			else:
				self.write("No such ID in DB")
		else:
			log("we have to get a new form ID")
			new_form = Forms()
			if form_data["name"]:
				new_form.name = form_data["name"]
			new_form.user_id = 1
			new_form.put()
			form_id = new_form.key().id()
		log(str(form_id))
		form_elements = form_data['html']

		if isinstance(form_elements, list) and form_elements != []:
			logging.error("It is a list, and it's not empty")
			i = 0
			element_ids = []
			for elm in form_elements:
				log(elm['id'])
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
				newfc.form_id = form_id
				if elm['input_type'] == 'input_text':
					newfc.input_type = 'text'
					newfc.component_type = 'input_field'
				if elm['input_type'] == 'radio':
					newfc.input_type = 'radiobuttons'
					newfc.component_type = 'input_field'
				if elm['input_type'] == 'checkbox':
					newfc.input_type = 'checkbox'
					newfc.component_type = 'input_field'
				if elm['input_type'] == 'file':
					newfc.input_type = 'file'
					newfc.component_type = 'image'
				if elm['input_type'] == 'textarea':
					newfc.input_type = 'textarea'
					newfc.component_type = 'input_field'
				if elm['input_type'] == 'headline':
					newfc.input_type = 'h2'
					newfc.component_type = 'info_field'
				newfc.caption = elm['caption']
				newfc.form_order = i
				if 'options' in elm.keys():
					log(elm['options'])
					newfc.options = json.dumps(elm['options'])
				newfc.put()
				elm_id = newfc.key().id()
				element_ids.append(elm_id)
		logging.error(element_ids)
		#delete removed form elements
		existing_elements = FormComponents.get_by_form_id(form_id)
		for ex_elm in existing_elements:
			logging.error(ex_elm.key().id())
			if ex_elm.key().id() in element_ids:
				logging.error("Yes!")
			else:
				logging.error("No! Deleting: " + str(ex_elm.key().id()))
				ex_elm.delete()
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
				query = self.request.get_all(e)
				if len(query) < 2:
					query = query[0]
				result = (e,query)
				output.append(result)
			se = Submissions()
			logging.error(output)
			for o in output:
				if isinstance(o[1], list):
					setattr(se,o[0],", ".join(o[1]))
					continue	
				if o[0] == "form_id":
					logging.error("Form ID is: " + o[1])
					se.form_id = int(o[1])
					continue
				if o[0][:9] == "imagedata":
					imagefile = o[1]
					imagefile = imagefile.split(',')[1]
					imagefile = str(imagefile)
					imagefile = base64.b64decode(imagefile)
					setattr(se,o[0][9:],db.Blob(imagefile))
					continue
				setattr(se,o[0],o[1])
			se.put()
			logging.error(variable_list)
			self.render("goback.html")


class DrawHandler(MainHandler):
	def get(self):
		self.render("drawingboard.html")

class AllFormsHandler(MainHandler):
	def get(self):
		all_forms = Forms.all()
		form_json = []
		for f in all_forms:
			form_json.append(json.loads(generate_form_json(f.key().id())))
		self.response.headers['Content-Type'] = 'application/json'
		self.response.out.write(json.dumps(form_json, sort_keys=True, indent=4, separators=(',', ': ')))

class DeleteHandler(MainHandler):
	def post(self):
		e_id = self.request.get("id")
		e_type = self.request.get("type")
		if e_id and e_type:
			if e_type == "submission":
				sub = Submissions.get_by_id(int(e_id))
				if sub:
					sub.delete()
			if e_type == "form":
				form = Forms.get_by_id(int(e_id))
				if form:
					form.delete()
					fc = FormComponents.get_by_form_id(int(e_id))
					if fc:
						for e in fc:
							e.delete()
			logging.error(e_id + " " + e_type)
			self.write(e_id + " " + e_type)


app = webapp2.WSGIApplication([
    ('/?', OverviewHandler),
    ('/([0-9]+)', FrontHandler),
    ('/submissions', SubmissionsHandler),
    ('/submissions/([0-9]+)', SubmissionsHandler),
    ('/submit', SubmitExpando),
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
    ('/forms', OverviewHandler),
    ('/listallforms', AllFormsHandler),
    ('/delete', DeleteHandler)

], debug=True)
