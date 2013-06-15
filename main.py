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
import jinja2

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir), autoescape=True)


class Surveys(db.Model):
	name = db.StringProperty(required = True)
	text = db.TextProperty(required = True)
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
		self.render('front.html')


	def post(self):
		name = self.request.get('name')
		text = self.request.get('text')
		
		if name and text:
			s = Surveys(name = name, text = text)
			s.put()
			self.response.write('Submission accepted!')



app = webapp2.WSGIApplication([
    ('/', MainHandler),
    ('/input', InputHandler)
], debug=True)
