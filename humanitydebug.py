import requests
import datetime

app_id = 'your app id'
app_secret = 'your app secret'
user = 'your humanity user'
pwd = 'your humanity password'

class HumanityData:

  def __init__(self, app_id, app_secret, user, pwd):

    self.app_id = app_id
    self.app_secret = app_secret 
    self.user = user
    self.pwd = pwd
    self.token = ''
    self.refresh_token = ''
    self.today = 'Nobody'
    self.tomorrow = 'Nobody'
    self.data = None
    self.count = 0

    self.get_token()


  def get_token(self):
    """get access token from humanity api"""

    auth_url = 'https://www.humanity.com/oauth2/token.php'
    auth_data = {  "client_id": self.app_id, 
                   "client_secret": self.app_secret,
                   "grant_type": "password",
                   "username": self.user,
                   "password": self.pwd }
    try:
      r = requests.post( auth_url, data = auth_data )
      self.token = r.json()["access_token"]
      self.refresh_token = r.json()["refresh_token"]
      self.count = 0    
    except:
      print('couldnt get the access token. check config')

  def get_new_token(self):
  
    auth_url = 'https://www.humanity.com/oauth2/token.php'
    auth_data = {  "client_id": self.app_id, 
                   "client_secret": self.app_secret,
                   "grant_type": "refresh_token",
                   "refresh_token": self.refresh_token
                 }
    try:
      r = requests.post( auth_url, data = auth_data )
      self.token = r.json()["access_token"]
      self.refresh_token = r.json()["refresh_token"]
      self.count = 0    
    except:
      print('couldnt get access token from refresh_token')
      print(r.text)

  def check_count(self):
     """check if it's time to refresh token"""

     self.count +=1
     if self.count > 50:
     	self.get_new_token()

  
  def get_me(self):
  
    url = 'https://www.humanity.com/api/v2/me'
    payload = { 'access_token': self.token }

    try:
      self.check_count()
      r = requests.get( url, params = payload )
      print(r.text)
    except:
      print('something went wrong')

  def get_onnow(self):

    url = 'https://www.humanity.com/api/v2/dashboard/onnow'
    payload = { 'access_token': self.token }

    try:
      self.check_count()
      r = requests.get( url, params = payload )
      print(r.text)
    except:
      print('something went wrong')  	

  def get_shifts(self):
    """get shifts from humnanit"""

    url = 'https://www.humanity.com/api/v2/shifts'

    # limit to only 3 days from now. can be changed later
    start_date = "{:%Y-%m-%d}".format(datetime.datetime.now())
    end_date = "{:%Y-%m-%d}".format(datetime.datetime.now() + datetime.timedelta(days=3))
    payload = { 'start_date': start_date, 'end_date': end_date, 'access_token': self.token }

    try:
      self.check_count()
      r = requests.get( url, params = payload )
      shifts = r.json()['data']
    except:
      print('something went wrong while trying to get shifts')
      shifts = []

    return shifts  

  def get_date_shift(self, shifts, shift_date):

     employees = []
     for i in shifts:
      if i['start_date']['day'] == shift_date.day and i['start_date']['month'] == shift_date.month and i['start_date']['year'] == shift_date.year:
        for j in i['employees']:
          employees.append(j['name'])
     if len(employees) == 0:
          employees.append('Nobody')     
     return employees     

  def update(self):
     shifts = self.get_shifts()

     self.today = self.get_date_shift(shifts, datetime.datetime.now())
     self.tomorrow = self.get_date_shift(shifts, datetime.datetime.now() + datetime.timedelta(days=1))

     #print(self.today, self.tomorrow)

if __name__ == "__main__":

  h = HumanityData(app_id, app_secret, user, pwd)
  h.update()
  print(h.today, h.tomorrow)
