import json
from collections import defaultdict
import traceback
from http.cookiejar import debug

import requests
from markdownify import markdownify as md
import json

import requests
from markdownify import markdownify as md
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import desc, asc
Base = declarative_base()

class Posts(Base):
  __tablename__ = 'posts'
  id = Column(Integer, primary_key=True,autoincrement=True )
  num = Column(Integer)
  subject = Column(Text)
  timestamp = Column(Integer)
  comment = Column(Text)
  posts_count = Column(Integer)
  images = Column(Integer)
  status = Column(Text)
  parent = Column(Integer)
  topic_id=Column(Integer,default=0)
  tag_ids=Column(Text)
  board=Column(String)
  board_topic=Column(String)

# def debug_print(...):
#   if DEBUG:
#     print(...)


class TwoChannelClient:
  def __init__(self):
    self.token=""
    self.session = requests.Session()
    self.base_url = 'http://flarum:8888'
    #self.base_url = 'http://127.0.0.1/'
    self.headers = {
      'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:143.0) Gecko/20100101 Firefox/143.0',
    }
    self.cookies = {

    }


    # Set headers and cookies
    self.session.headers.update(self.headers)
    self.session.cookies.update(self.cookies)
    self.db_url = 'postgresql://parser:parser@postgres:5432/parser'

  def read_posts_from_db(self, ):
    """
    Read data from PostgreSQL 'posts' table using ORM

    Args:
        db_url (str): Database connection URL

    Returns:
        list: List of Post objects or empty list if error
    """
    db_url=self.db_url
    try:
      engine = create_engine(db_url)
      Session = sessionmaker(bind=engine)
      session = Session()

      posts = session.query(Posts).all()

      session.close()
      return posts

    except Exception as e:
      print(f"Error reading posts from database: {e}")
      return []

  def login(self, username, password):
    """
    Authenticate user and obtain session cookies

    Args:
        username (str): Admin username
        password (str): Admin password

    Returns:
        bool: True if login successful, False otherwise
    """
    url = f'{self.base_url}/login'


    auth_data = self.extract_auth_info()
    # Set headers for login request
    login_headers = {
      'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:143.0) Gecko/20100101 Firefox/143.0',
      'X-CSRF-Token': auth_data[1],

    }

    # Set cookies for login request
    # login_okiesco = {
    #   'flarum_session': 'jUmPt2645wYxJUa4CmFcU98kQYtf3fGUrc06l7Fl'
    # }
    #self.cookies

    payload = {
      "identification": username,
      "password": password,
      "remember": True
    }

    try:
      # Set headers and cookies for this request
      self.session.headers= login_headers

      #self.session.cookies.update(self.cookies)

      response = self.session.post(url, json=payload)
      response.raise_for_status()

      # If login successful, update session with new cookies
      # The response should contain the updated cookies
      #print(response.cookies)
      #self.session.cookies.update(response.cookies)
      self.cookies= response.cookies
      #self.session.cookies=requests.Session().cookies
      #self.session.cookies.update(self.cookies)
      #print(username,self.session.cookies)
      return response.cookies

    except requests.exceptions.RequestException as e:
      print(f"Error during login: {e}")
      return False

  def get_token(self, username, password):
    """
    Authenticate user and obtain session cookies

    Args:
        username (str): Admin username
        password (str): Admin password

    Returns:
        bool: True if login successful, False otherwise
    """
    url = f'{self.base_url}/api/token'


    auth_data = self.extract_auth_info()
    # Set headers for login request
    login_headers = {
      'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:143.0) Gecko/20100101 Firefox/143.0',
      'X-CSRF-Token': auth_data[1],

    }

    # Set cookies for login request
    # login_okiesco = {
    #   'flarum_session': 'jUmPt2645wYxJUa4CmFcU98kQYtf3fGUrc06l7Fl'
    # }
    #self.cookies

    payload = {
      "identification": username,
      "password": password,
      "remember": True
    }

    try:
      # Set headers and cookies for this request
      self.session.headers.update(login_headers)
      self.session.cookies.update(self.cookies)

      response = self.session.post(url, json=payload)
      response.raise_for_status()

      # If login successful, update session with new cookies
      # The response should contain the updated cookies
      self.token=response.json()['token']

      return response.json()

    except requests.exceptions.RequestException as e:
      print(f"Error during login: {e}")
      return False

  def get_board_data(self, board='po', page=2):
    """
    Fetch board data from 2ch.su

    Args:
        board (str): Board name (default: 'po')
        page (int): Page number (default: 2)

    Returns:
        dict: JSON response data
    """
    url = f'{self.base_url}/{board}/{page}.json'

    try:
      response = self.session.get(url, stream=True)
      response.raise_for_status()

      # The response is already decompressed by requests
      # but we can still check if it's gzip encoded
      if response.headers.get('content-encoding') == 'gzip':
        # requests handles gzip automatically
        pass

      return response.json()

    except requests.exceptions.RequestException as e:
      print(f"Error fetching data: {e}")
      return None

  def extract_auth_info(self):
    """
    Extract authentication cookie and X-CSRF-Token from response

    Returns:
        tuple: (cookie, csrf_token) or (None, None) if error
    """
    url = f'{self.base_url}/'

    # Set headers for the request
    headers = {
      'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:143.0) Gecko/20100101 Firefox/143.0',

    }

    try:
      response = self.session.get(url, headers=headers)
      response.raise_for_status()

      # Extract cookie from response
      cookie = None
      if response.cookies.get('flarum_session'):
        cookie = response.cookies.get('flarum_session')

      # Extract X-CSRF-Token from response headers
      csrf_token = response.headers.get('X-CSRF-Token')

      self.cookies["flarum_session"]=cookie
      return [cookie, csrf_token]

    except requests.exceptions.RequestException as e:
      print(f"Error extracting auth info: {e}")
      return None, None




  def add_user(self, username, password, email ):
    """
    Add a user via the API

    Args:
        username (str): Username
        email (str): Email address
        password (str): Password

    Returns:
        dict: JSON response data or None if error
    """
    url = f'{self.base_url}/api/users'
    auth_data= self.extract_auth_info()
    # Set headers for POST request
    headers = {
      'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:143.0) Gecko/20100101 Firefox/143.0',
      'X-CSRF-Token': auth_data[1],
      'Authorization': 'Token '+self.token,

    }

    payload = {
      "data": {
        "attributes": {
          "username": username,
          "email": email,
          "password": password,
          "isEmailConfirmed":True,
        }
      }
    }

    try:
      # Set headers and cookies for this request
      self.session.headers.update(headers)
      self.session.cookies.update(self.cookies)

      response = self.session.post(url, json=payload)
      response.raise_for_status()

      return response.json()

    except requests.exceptions.RequestException as e:
      print(f"Error adding user: {e}", payload)
      return None


  def user_post_exists(self, user_id, offset=0, limit=20):
    """
    Retrieves posts made by a specific user.

    Args:
        user_id (str): The ID of the user whose posts to retrieve.
        offset (int): The starting offset for pagination.
        limit (int): The maximum number of posts to retrieve.

    Returns:
        dict: JSON response data containing the user's posts, or None if an error occurs.
    """
    url = f'{self.base_url}/api/posts?filter%5Bauthor%5D={user_id}&filter%5Btype%5D=comment&page%5Boffset%5D={offset}&page%5Blimit%5D={limit}&sort=-createdAt'

    auth_data = self.extract_auth_info()

    headers = {
      'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:143.0) Gecko/20100101 Firefox/143.0',
      'X-CSRF-Token': auth_data[1],
    }

    self.session.headers.update(headers)
    self.session.cookies.update(self.cookies)
    response = self.session.get(url)
    rsp = response.json()
    #print(rsp["data"])
    if len(rsp["data"]) == 0:
      return 0
    else:
      return rsp["data"]


  def check_user_exists(self, username):
    """
    Checks if a user exists by attempting to access their profile page.

    Args:
        username (str): The username to check.

    Returns:
        bool: True if the user exists (status code 200), False otherwise.
    """
    url = f'{self.base_url}/u/{username}'

    headers = {
      'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:143.0) Gecko/20100101 Firefox/143.0',
    }

    try:
      response = self.session.get(url, headers=headers, allow_redirects=False)
      # A 200 status code indicates the user profile page was found.
      # A 404 status code indicates the user does not exist.
      return response.status_code
    except requests.exceptions.RequestException as e:
      print(f"Error checking user existence for {username}: {e}")
      return False

  def multi_poster(self,post,token,session):

    #creating thread
    posted_messages =[]
    if post.parent == 0:
      #try:
      client = TwoChannelClient()
      client.token = token
      #print(client.check_user_exists(str(post.num)))
      if  client.check_user_exists(str(post.num)) == 404:
         print("CREATING OP USER:",str(post.num))
         client.add_user(username=str(post.num),password="correcthorsebatterystaple",email=str(post.num)+"@gmail.com")
      user_data=client.login(username=str(post.num),password="correcthorsebatterystaple")
      print("OP USER AUTHENTICATED:",str(post.num),user_data)
      #if post.subject =="":
      if len(post.subject)<3:
        subject="***"
      else:
        subject=post.subject

      if md(str(post.comment),heading_style="ATX")  =="":
        comment="_"
      else:
        comment=post.comment

      checked_post = client.user_post_exists(str(post.num))
      #print(checked_post)
      if checked_post==0:
        #print(post.tag_ids)
        rsp=client.post_discussion(title=str(subject)[0:80],content=md(str(comment),heading_style="ATX"),tags=post.tag_ids.replace("'", "\""))

        print(rsp)
        #print(checked_post)
        post_id=rsp['data']['id']
        print("new_thread",post.num,post_id)
      else:
        post_id=checked_post[0]["relationships"]["discussion"]["data"]["id"]
        print("posts_exists",post_id)



        # if post.subject =="":
        #   post.subject = "X"
        # if post.comment == "":
        #   rsp=client.post_discussion(title=str(post.subject)[0:80],content=md(" ",heading_style="ATX"),tags=post.tag_ids)
        # else:
        #   rsp=client.post_discussion(title=str(post.subject)[0:80],content=md(str(post.comment),heading_style="ATX"),tags=post.tag_ids)
        #
        # topic_id=rsp['data']['id']
        # print("new_thread",post.num,topic_id)
        # topic=session.query(Posts).filter(Posts.num==post.num).first()
        # topic.topic_id = int(topic_id)

      #post.topic_id = int(1)
        # except:
        #
        #   try:
        #     client.login(username=str(post.num),password="correcthorsebatterystaple")
        #     if post.comment == "":
        #       rsp=client.post_discussion(title=" ",content=md(" ",heading_style="ATX"),tags=json.loads(post.tag_ids.replace("'", "\"")))
        #     else:
        #       rsp=client.post_discussion(title=" ",content=md(str(post.comment),heading_style="ATX"),tags=json.loads(post.tag_ids.replace("'", "\"")))
        #
        #     topic_id=rsp['data']['id']
        #     print("new_thread",post.num,topic_id)
        #     topic=session.query(Posts).filter(Posts.num==post.num).first()
        #     topic.topic_id = int(topic_id)
      # except:
      #     traceback.print_exc()
      #     print("new_thread_error",post.num)




      #session.commit()


      #adding  messages created thread

      #print("POSTERS")
      post_messages =session.query(Posts).filter(Posts.parent == post.num).order_by(asc(Posts.timestamp)).all()
      print("POSTERS",len(post_messages))
      for m in post_messages:
        client2 = TwoChannelClient()
        client2.token = token
        if  client2.check_user_exists(str(m.num)) == 404:
          print("CREATING POST USER:",str(m.num), "PARENT:",(post.num))
          client2.add_user(username=str(m.num),password="correcthorsebatterystaple",email=str(m.num)+"@gmail.com")
        user_data=client2.login(username=str(m.num),password="correcthorsebatterystaple")
        print("POST USER AUTHENTICTED:",str(m.num),user_data)
        checked_comment = client2.user_post_exists(str(m.num))
        #print(checked_comment,post_id)
        if   checked_comment==0:
          print(m.num,post_id)
          if m.subject =="":
            subject="_"
          else:
            subject=m.subject

          if md(str(m.comment),heading_style="ATX") =="":
            comment="_"
          else:
            comment=m.comment
          rsp=client2.post_discussion(title=str(subject)[0:80],content=md(str(comment),heading_style="ATX"),parent=post_id)
          #print(rsp)
          topic_id=rsp["data"]["id"]
          print("new_comment",post.num,topic_id)

        else:
          print("comment_exists",checked_comment[0]['id'])

    # else:
    #     parent_post=session.query(Posts).filter(Posts.num==post.parent).first()
    #     post_update_messages =session.query(Posts).filter(Posts.parent == parent_post.num).order_by(asc(Posts.timestamp)).all()

        #m.topic_id = int(2)
      #session.commit()
      #return 0
        # #parent_topic=session.query(Posts).filter(Posts.num==m.parent).first()
        # print("thread_messages",m.parent,m.num,parent_topic.topic_id)
        # #client.login(username="admin",password=" ")
        # #client.get_token(username="admin",password="xxxxxxxxxx")
        # client2.token = token
      #   #if  client2.check_user_exists(str(post.num)) == 404:
      #   client2.add_user(username=str(n.num),password="correcthorsebatterystaple",email=str(post.num)+"@gmail.com")
      #   #client2.add_user(username=str(m.num),password="correcthorsebatterystaple",email=str(m.num)+"@gmail.com")
      #   client2.login(username=str(m.num),password="correcthorsebatterystaple")
      #   if m.comment == "":
      #     rsp=client2.post_discussion(title=" ",content=md(" ",heading_style="ATX"),parent=parent_topic.topic_id)
      #   else:
      #     rsp=client2.post_discussion(title=" ",content=md(str(m.comment),heading_style="ATX"),parent=parent_topic.topic_id)
      #     #rsp=self.post_discussion(title=str(m.subject)[0:80],content=md(str(m.comment),heading_style="ATX"),parent=parent_topic.topic_id)
      #   try:
      #     topic_id=rsp['data']['id']
      #     print("new_thread_msg",m.num, topic_id)
      #     m.topic_id = int(topic_id)
      #   except:
      #     print("error_update_msg",m.num,rsp)
      #   session.commit()
    # else:
    #   #adding new messages to existing threads
    #
    #   client3 = TwoChannelClient()
    #   parent_post=session.query(Posts).filter(Posts.num==post.parent).first()
    #
    #   post_update_messages =session.query(Posts).filter(Posts.parent == parent_post, Posts.topic_id==0).order_by(asc(Posts.timestamp)).all()
    #   for um in post_update_messages:
    #     print("thread_updates",um.parent,um.num,parent_post.topic_id)
    #     client3.token = token
    #     if not self.check_user_exists(str(post.num)):
    #       client3.add_user(username=str(post.num),password="correcthorsebatterystaple",email=str(post.num)+"@gmail.com")
    #     #client3.add_user(username=str(um.num),password="correcthorsebatterystaple",email=str(um.num)+"@gmail.com")
    #     client3.login(username=str(um.num),password="correcthorsebatterystaple")
    #     if um.comment == "":
    #       rsp=client3.post_discussion(title=str(um.subject)[0:80],content=md(" ",heading_style="ATX"),parent=parent_post.topic_id)
    #     else:
    #       rsp=client3.post_discussion(title=str(um.subject)[0:80],content=md(str(um.comment),heading_style="ATX"),parent=parent_post.topic_id)
    #       #rsp=self.post_discussion(title=str(m.subject)[0:80],content=md(str(m.comment),heading_style="ATX"),parent=parent_topic.topic_id)
    #     try:
    #       topic_id=rsp['data']['id']
    #       print("new_update_msg",um.num, topic_id)
    #       um.topic_id = int(topic_id)
    #     except:
    #       print("error_update_msg",um.num,rsp)
    #     session.commit()

    #session.close()
    # except Exception as e:
    #   print("FAILED",post.num,e)
    #   session.close()


  def sync_discussion(self):


    db_url=self.db_url
    try:
      engine = create_engine(db_url)
      Session = sessionmaker(bind=engine)
      session = Session()

      #posts = session.query(Posts).all()
      #session.query(Posts).filter_by(num=int(post['num'])).first()
      posts =session.query(Posts).filter_by(topic_id=0).order_by(desc(Posts.timestamp)).all()

      #session.close()


    except Exception as e:
      print(f"Error reading posts from database: {e}")
      return []


    from concurrent.futures import ThreadPoolExecutor, as_completed
    import time
    session.expunge_all()
    #posts = session.scalars(posts).all()
    results = []
    self.login(username="admin",password="xxxxxxxxxx")
    self.get_token(username="admin",password="xxxxxxxxxx")
    token = self.token
    print(len(posts))
    # for post in posts:
    #   self.multi_poster(post,token,session)
    # die()
    with ThreadPoolExecutor(max_workers=5) as executor:
      futures = [executor.submit(self.multi_poster, post,token,session) for post in posts]
      # Process results as they complete
      # for future in as_completed(future_to_item):
      #     item = future_to_item[future]
      #     try:
      #         result = future.result()
      #         results.append(result)
      #     except Exception as e:
      #         print(f"Error processing {item}: {e}")
      #
      # # Process results as they complete
      # for future in as_completed(future_to_item):
      #     item = future_to_item[future]
      #     try:
      #         result = future.result()
      #         results.append(result)
      #     except Exception as e:
      #         print(f"Error processing {item}: {e}")

    print("All tasks complete.")
    #print("Results:", futures)
    die()

    #syncync topics
    messages_by_parent = defaultdict(list)
    for post in posts:
      if post.parent == 0:
        self.login(username="admin",password="xxxxxxxxxx")
        self.get_token(username="admin",password="xxxxxxxxxx")
        self.add_user(username=str(post.num),password="correcthorsebatterystaple",email=str(post.num)+"@gmail.com")


        self.login(username=str(post.num),password="correcthorsebatterystaple")
        if post.comment == "":
          rsp=self.post_discussion(title=str(post.subject)[0:80],content=md(" ",heading_style="ATX"),tags=json.loads(post.tag_ids.replace("'", "\"")))
        else:
          rsp=self.post_discussion(title=str(post.subject)[0:80],content=md(str(post.comment),heading_style="ATX"),tags=json.loads(post.tag_ids.replace("'", "\"")))
        try:
          topic_id=rsp['data']['id']
          print(topic_id)
          post.topic_id = int(topic_id)
        except:
          print(post.num)
        session.commit()


        messages =session.query(Posts).filter(Posts.parent == post.num, Posts.topic_id==0).order_by(asc(Posts.timestamp)).all()
        for m in messages:
          parent_topic=session.query(Posts).filter_by(num=post.num).first()
          print(m.parent,m.num,parent_topic.topic_id)
          self.login(username="admin",password="xxxxxxxxxx")
          self.get_token(username="admin",password="xxxxxxxxxx")
          self.add_user(username=str(m.num),password="correcthorsebatterystaple",email=str(m.num)+"@gmail.com")


          print(self.login(username=str(m.num),password="correcthorsebatterystaple"))
          if m.comment == "":
            rsp=self.post_discussion(title=str(m.subject)[0:80],content=md(" ",heading_style="ATX"),parent=parent_topic.topic_id)
          else:
            rsp=self.post_discussion(title=str(m.subject)[0:80],content=md(str(m.comment),heading_style="ATX"),parent=parent_topic.topic_id)
            #rsp=self.post_discussion(title=str(m.subject)[0:80],content=md(str(m.comment),heading_style="ATX"),parent=parent_topic.topic_id)
          try:
            topic_id=rsp['data']['id']
            print(topic_id)
            m.topic_id = int(topic_id)
          except:
            print(m.num,rsp)
          session.commit()

      else:
        #научиться игнорировать тех, которые были предыдущим блоком добавлены
        messages_by_parent[post.parent].append(post)

    # Sort each parent's posts by timestamp in Python
    for parent_id in messages_by_parent:
      messages_by_parent[parent_id].sort(key=lambda p: p.timestamp)

    # Example usage: print the grouped and sorted posts
    for parent_id, child_posts in messages_by_parent.items():
      print(f"Parent ID: {parent_id}")
      for m in child_posts:
        #print(dir(m))
        parent_topic=session.query(Posts).filter_by(parent=parent_id).first()
        print(m.parent,m.num,parent_topic.topic_id)
        self.login(username="admin",password="xxxxxxxxxx")
        self.get_token(username="admin",password="xxxxxxxxxx")
        self.add_user(username=str(m.num),password="correcthorsebatterystaple",email=str(m.num)+"@gmail.com")


        print(self.login(username=str(m.num),password="correcthorsebatterystaple"))
        if m.comment == "":
          rsp=self.post_discussion(title=str(m.subject)[0:80],content=md(" ",heading_style="ATX"),parent=parent_topic.topic_id)
        else:
          rsp=self.post_discussion(title=str(m.subject)[0:80],content=md(str(m.comment),heading_style="ATX"),parent=parent_topic.topic_id)
          #rsp=self.post_discussion(title=str(m.subject)[0:80],content=md(str(m.comment),heading_style="ATX"),parent=parent_topic.topic_id)
        try:
          topic_id=rsp['data']['id']
          print(topic_id)
          m.topic_id = int(topic_id)
        except:
          print(m.num,rsp)
        session.commit()
        #print(f"  Post ID: {post.id}, Timestamp: {post.timestamp}, Subject: {post.subject}")
    #
    #
    #


    session.close()




    # #syncying messages
    # for post in posts:
    #   if post.parent != 0:
    #     #self.login(username="admin",password="xxxxxxxxxx")
    #     parent_topic=session.query(Posts).filter_by(num=post.parent).first()
    #     print(post.parent,post.num,parent_topic.topic_id)
    #     rsp=self.post_discussion(title=str(post.subject)[0:80],content=md(str(post.comment),heading_style="ATX"),parent=parent_topic.topic_id)
    #     try:
    #       topic_id=rsp['data']['id']
    #       print(topic_id)
    #       post.topic_id = int(topic_id)
    #     except:
    #       print(post.num,rsp)
    # session.commit()
    # session.close()
    return True




  def post_discussion(self, title, content,tags=None,parent=None):
    if tags:
      tags=json.loads(tags.replace("'", "\""))
    """
    Create a discussion on the Flarum forum

    Args:
        title (str): Discussion title
        content (str): Discussion content
        tags (list): List of tag IDs (default: None)

    Returns:
        dict: JSON response data or None if error
    """


    auth_data= self.extract_auth_info()
    # Set headers for POST request
    post_headers = {
      'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:143.0) Gecko/20100101 Firefox/143.0',

      'X-CSRF-Token': auth_data[1],

    }

    # Set cookies from curl command
    # post_cookies = {
    #   'token': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6IjZhNTM0YzZiLTk1MjEtNDczYi04Y2VkLTY5ZGJhNWJmMzNjZiJ9.Lo85NjDx1344x4rP1HVvbJhCdeYnrzF9ZCdgeXnIGAo',
    #   'PGADMIN_LANGUAGE': 'en',
    #   'flarum_session': 'KSpa8Kf1lgxrjQcuazvs968uAsGtSj5OcTjtUEsy',
    #   'flarum_remember': '9qUMjObY5snmuwPj06bJhjmALY4st8i4UJBIyNxq'
    # }

    # Prepare JSON payload
    if not parent:
      url = f'{self.base_url}/api/discussions'
      payload = {
        "data": {
          "type": "discussions",
          "attributes": {
            "title": title,
            "content": content
          },
          "relationships": {
            "tags": {
              "data": tags or []
            }
          }
        }
      }
    else:
      url = f'{self.base_url}/api/posts'
      payload = {
        "data": {
          "type": "posts",
          "attributes": {
            "content":content
            #"content": content.encode('unicode_escape').decode('ascii')
            #"content": "SSSSS"
          },
          "relationships": {
            "discussion": {
              "data": {
                "type": "discussions",
                "id": str(parent)
              }
            }
          }
        }
      }
    #print(payload)
    #try:
    # Set headers and cookies for this request
    self.session.headers.update(post_headers)
    #self.session.cookies.update(self.cookies)
    print(self.session.headers)


    response = self.session.post(url, json=payload)
    #response.raise_for_status()

    return response.json()

    # except requests.exceptions.RequestException as e:
    #   print(f"Error creating discussion: {e} {payload}")
    #   traceback.print_exc()
    #   return None


# Usage example:
# client = TwoChannelClient()
# data = client.get_board_data('po', 2)
# if data:
#     print(data)

# Create client instance


# Fetch data from po board, page 2


# Or fetch from different board
#data = client.get_board_data('b', 1)

# Access the JSON data

#client.create_discussion(title="ZZZZ",content="YYYYYYY")
# if data:
#   #td= json.loads(data)
#   for t in data['threads']:
#       #print(t['posts'][0]['comment'])
#       client.create_discussion(title=str(t['posts'][0]['subject'])[0:80],content=str(t['posts'][0]['comment']),tags=["2ch"])

# u = client.get_token(username="admin",password="xxxxxxxxxx")
# print(u)
# u = client.add_user(username="asdasd2s2a",password="correcthorsebatterystaple", email="2aa2asdasa@aaa.com")
# print(u)
# z = client.login(username="asdasd2s2a",password="correcthorsebatterystaple")
# print(z)
# if lg:
#   #td= json.loads(data)
#   for p in data:
#     if p.parent==0:
#       print(str(p.subject)[0:80])
#       rsp = client.create_discussion(title=str(p.subject)[0:80],content=md(str(p.comment),heading_style="ATX"),tags=post.tag_ids)
#       print(rsp)
#++++++++++

# client = TwoChannelClient()
# data = client.read_posts_from_db()
# client.login(username="admin",password="xxxxxxxxxx")
# client.sync_discussion()
