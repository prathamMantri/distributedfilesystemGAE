"""
File-Name - distdb.py
File-info - contains logic for file storage in Google app engine
Author    - Nirmal kumar Ravi
"""

"""
imports used
"""
import os
import urllib
import webapp2
import datetime
import re
from google.appengine.ext import blobstore
from google.appengine.ext.webapp import blobstore_handlers
from google.appengine.ext.webapp import template
from google.appengine.ext import db
from google.appengine.api import memcache



"""
MainHandler - main page to handle initial requset
"""
class MainHandler(webapp2.RequestHandler):
  def get(self):
    option = self.request.get('option')
    message = self.request.get('message')
    template_values={
        'message':message
      }
    if option == 'C':
      self.redirect('/create')
    elif option == 'R':
      self.redirect('/read')
    elif option == 'D':
      self.redirect('/delete')
    elif option == 'L':
      self.redirect('/list')
    elif option == 'S':
      self.redirect('/search')
    elif option == 'T':
      self.redirect('/stats')
    elif option == 'X':
      self.redirect('/removeall')
    elif option == 'I':
      self.redirect('/findinfile')
      
    path = os.path.join(os.path.dirname(__file__), 'home.html')
    self.response.out.write(template.render(path, template_values))

"""
FileInfo - stores metadata of files
"""
class FileInfo(db.Model):
  blog_key = db.StringProperty(required=True)
  file_name = db.StringProperty(required=True)
  file_size = db.IntegerProperty(required=True)

"""
Helper - helper class to help other methods
"""
class Helper:
  #check file exists or not
  def isFileExists(self,fileName):
    key = db.Key.from_path('FileInfo', fileName)
    file_info = db.get(key)
    return file_info
  
  #delete file in blob
  def deleteBlob(self,blog_key):
    resource = str(urllib.unquote(blog_key))
    blob_info = blobstore.BlobInfo.get(resource)
    if blob_info:
      blob_info.delete()
      return True
    return False
  
  #delete file metadata
  def deleteFileMetaData(self,fileName):
    key = db.Key.from_path('FileInfo', fileName)
    if key:
      db.delete(key)
    return key

  #get all file info
  def getAllFilesMetaData(self):
    q = FileInfo.all()
    file_metadata=[]
    for f in q.run():
      file_metadata.append(f)
    return file_metadata

  #find match 
  def exact_Match(self,phrase, word):
    b = r'(\s|^|$)' 
    res = re.match(b + word + b, phrase, flags=re.IGNORECASE)
    return bool(res)
  
    

"""
CreateFile -used to upload the file from GAE
"""
class CreateFile(webapp2.RequestHandler):
  def get(self):
      #template_values={'upload_url':upload_url}
      template_values ={}
      fileName = self.request.get('fileName')
      if fileName:
        h = Helper()
        #check file name exists or not
        file_info = h.isFileExists(fileName)
        if file_info:
          val= self.request.get('overwrite')
          if val == 'overwrite':
            #delete existing blob and create new blob to upload if overwrite is checked
            h.deleteBlob(file_info.blog_key)
            #redirect to upload
            upload_url = blobstore.create_upload_url('/upload')
            template_values={'upload_url':upload_url}
            path = os.path.join(os.path.dirname(__file__), 'create.html')
            self.response.out.write(template.render(path, template_values))
          else:
            template_values['message'] = 'file name already exists !'
            path = os.path.join(os.path.dirname(__file__), 'create_pre.html')
            self.response.out.write(template.render(path, template_values))
        else:
          upload_url = blobstore.create_upload_url('/upload')
          template_values={'upload_url':upload_url}
          path = os.path.join(os.path.dirname(__file__), 'create.html')
          self.response.out.write(template.render(path, template_values))

      else:
        path = os.path.join(os.path.dirname(__file__), 'create_pre.html')
        self.response.out.write(template.render(path, template_values))
      


"""
ReadFile - used to download the file from GAE
"""
class ReadFile(webapp2.RequestHandler):
  def get(self):
      file_name = self.request.get('fileName')
      message =""
      #search in datastore
      if file_name:
        h = Helper()
        file_info = h.isFileExists(file_name)
        if file_info:
          #chk file in memcache
          if file_info.file_size <= 100000:
            val= memcache.get('%s' % file_info.file_name)
            if val:
              #return from cache
              self.response.out.write(val)
          message='file found'+str(file_info.blog_key)
          self.redirect('/serve/%s' % file_info.blog_key)
        else:
          message='file not found. check the file name'
        
      template_values = {'message':message}
      path = os.path.join(os.path.dirname(__file__), 'read.html')
      self.response.out.write(template.render(path, template_values))

"""
DeleteFile - delete the file from GAE
"""
class DeleteFile(webapp2.RequestHandler):
  def get(self):
      file_name = self.request.get('fileName')
      message =""
      #search in datastore
      if file_name:
        h = Helper()
        file_info = h.isFileExists(file_name)
        if file_info:
          #delete file in blob
          h.deleteBlob(file_info.blog_key)
          #delete file metadata
          h.deleteFileMetaData(file_name)
          #delete cache
          memcache.delete('%s' % file_info.file_name)
          message='file found and deleted'
        else:
          message='file not found. check the file name'
        
      template_values = {'message':message}
      path = os.path.join(os.path.dirname(__file__), 'delete.html')
      self.response.out.write(template.render(path, template_values))

"""
ListFiles - used to list all files
"""
class ListFiles(webapp2.RequestHandler):
  def get(self):
    h = Helper()
    metadatas = h.getAllFilesMetaData()
    #to get filename from file metadata
    file_list = [metadata.file_name for metadata in metadatas]
    template_values={
      'file_list':file_list
      }
    path = os.path.join(os.path.dirname(__file__), 'listfiles.html')
    self.response.out.write(template.render(path, template_values))

"""
SearchFile - search file exists or not 
"""
class SearchFile(webapp2.RequestHandler):
  def get(self):
    file_name = self.request.get('fileName')
    regex =  self.request.get('regex')
    message =""
    match_names = []
    if file_name:
      h=Helper()
      file_info = h.isFileExists(file_name)
      if file_info:
        message="File found in datastore "
        val= memcache.get('%s' % file_info.file_name)
        if val:
          message = message + "and in memcache"
      elif regex == 'regex':  #check for regex flag
        metadatas = h.getAllFilesMetaData()
        file_names = [metadata.file_name for metadata in metadatas]
        for name in file_names:
          if name.find(file_name) != -1:
            match_names.append(name)
        if len(match_names) == 0:
          message="File not found and no mach in regex"
        else:
          message ="Some files match given filename"
      else:
        message="File not found"

    template_values={'message':message,
                     'match_names':match_names}
    path = os.path.join(os.path.dirname(__file__), 'search.html')
    self.response.out.write(template.render(path, template_values))
    
"""
UploadHandler - handles the uploaded file
mainly to upload file to url created by CreateFile
"""
class UploadHandler(blobstore_handlers.BlobstoreUploadHandler):
  def post(self):
    upload_files = self.get_uploads('file')  # 'file' is file upload field in the form
    blob_info = upload_files[0]
    message = 'file ' + str(blob_info.filename) + ' uploaded sucessfully!'
    
    #save file metadata to datastore
    blogkey = blob_info.key()
    file_name = str(blob_info.filename)
    file_size = blob_info.size
    file_info = FileInfo(key_name = file_name,blog_key=str(blogkey),file_name=file_name,file_size=file_size)
    file_info.put()

    #save it in memcache if file size is <= 100000 bytes
    #take file from blob and save it to mem cache as well
    if file_size <= 100000:
      blob_reader = blob_info.open()
      if blob_reader :
        value = blob_reader.read()
        memcache.set('%s'%file_name,value)
        message = message +' and also cached'

    template_values={
      'message':message
      }
    path = os.path.join(os.path.dirname(__file__), 'home.html')
    self.response.out.write(template.render(path, template_values))
    
"""
ServeHandler - serves the content of particular file requsted by
ReadFile
"""
class ServeHandler(blobstore_handlers.BlobstoreDownloadHandler):
  def get(self, resource):
    resource = str(urllib.unquote(resource))
    blob_info = blobstore.BlobInfo.get(resource)
    self.send_blob(blob_info)

"""
Stats - gives various stats of distributed storage
"""
class Stats(webapp2.RequestHandler):
  
  def get(self):
    h = Helper()
    #stats for datastore
    metadatas = h.getAllFilesMetaData()
    file_sizes = [float(metadata.file_size) for metadata in metadatas] #retrive file sizes from metadata
    file_count = len(file_sizes)#get file count
    file_size = sum(file_sizes)#get total file size
    file_size = file_size/(1000.*1000.)
    #stats for memcache
    d = memcache.get_stats()
    
    template_values={
      'file_size':file_size,
      'file_count':file_count,
      'mem_file_size':d['bytes']/(1000.*1000.),
      'mem_file_count':d['items']
      }
    path = os.path.join(os.path.dirname(__file__), 'stats.html')
    self.response.out.write(template.render(path, template_values))

"""
Remove All - remove all elements from cache and datastore
"""
class RemoveAll(webapp2.RequestHandler):
  def get(self):
    message =""
    fromCache = self.request.get('fromCache')
    fromDB = self.request.get('fromDB')
    if fromCache == 'fromCache':
      memcache.flush_all()
      message= message+"Removed all from cache "

    if fromDB == 'fromDB':
      h=Helper()
      #fulsh memcache
      memcache.flush_all()
      #get metada
      metadatas = h.getAllFilesMetaData()
      file_list = [metadata.file_name for metadata in metadatas]
      #remove file and delete blob
      for file_name in file_list:
        h.deleteBlob(file_name)
        h.deleteFileMetaData(file_name)
      message = message +" Removed all from DB"

    template_values={
      'message':message
    }
    path = os.path.join(os.path.dirname(__file__), 'removeall.html')
    self.response.out.write(template.render(path, template_values))

"""
used to find a word in a text
"""
class FindInFile(webapp2.RequestHandler):
  def get(self):
    message =""
    fileName = self.request.get('fileName')
    searchWord = self.request.get('searchWord')
    if fileName and searchWord:
      h=Helper()
      file_info = h.isFileExists(fileName)
      if file_info:
        resource = str(urllib.unquote(file_info.blog_key))
        blob_info = blobstore.BlobInfo.get(resource)
        blob_reader = blob_info.open()
        if blob_reader :
          phrase = blob_reader.read()
          if phrase.find(searchWord) != -1:
            message += "match found!"
          else:
            message += "match not found! "
      else:
        message += "check the file name"

    template_values={
      'message':message
    }
    path = os.path.join(os.path.dirname(__file__), 'findinfile.html')
    self.response.out.write(template.render(path, template_values))
    
"""
url mappings to corresponding classes
"""
app = webapp2.WSGIApplication([('/', MainHandler),
                               ('/create',CreateFile),
                               ('/upload', UploadHandler),
                               ('/read',ReadFile),
                               ('/delete',DeleteFile),
                               ('/list',ListFiles),
                               ('/search',SearchFile),
                               ('/stats',Stats),
                               ('/removeall',RemoveAll),
                               ('/findinfile',FindInFile),
                               ('/serve/([^/]+)?', ServeHandler)],
                              debug=True)
