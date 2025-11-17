import time

import requests
import json
from sqlalchemy import create_engine, Column, String, Integer, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


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

PAGES=['index','1','2','3','4','5','6','7','8','9','10']

class ChParser:
  def __init__(self,board,tag_ids):
    self.base_url = 'https://www.2channel.moe'
    self.db_url = 'postgresql://parser:parser@127.0.0.1:5432/parser'
    self.board = board
    self.tag_ids = tag_ids



  def fetch_json(self,page):
        url = 'https://www.2channel.moe/'+self.board+'/'+page+'.json'
        headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:143.0) Gecko/20100101 Firefox/143.0',
            'Accept': 'text/html, */*; q=0.01',
            'Accept-Language': 'en-US,en;q=0.5',
            'X-Requested-With': 'XMLHttpRequest',
            'Connection': 'keep-alive',
            'Referer': 'https://https://www.2channel.moe/b/',
            'Cookie': '_ga=GA1.2.1011049934.1759506208; _ga_7NPYTX0FY3=GS2.2.s1759738178$o3$g1$t1759738186$j52$l0$h0; _gid=GA1.2.1079694359.1759728115; _gat=1',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'If-Modified-Since': 'Mon, 06 Oct 2025 08:09:39 GMT',
            'If-None-Match': 'W/"68e37943-14d22"',
            'TE': 'trailers'
        }

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching JSON: {e}")
            return None

  def parse_json_data(self, json_data):
        if not json_data or 'threads' not in json_data:
            return []

        parsed_threads = []
        for thread in json_data['threads']:
            parsed_thread = {
                'num': thread.get('thread_num', ''),
                'subject': thread.get('posts', '')[0]["subject"],
                'timestamp': thread.get('timestamp', 0),
                'comment': thread.get('posts', '')[0]["comment"],
                'posts_count': thread.get('posts_count', 0),
                'images': thread.get('images', 0),
                'name':thread.get('name', 0)
            }
            parsed_threads.append(parsed_thread)

        return parsed_threads

  def parse_json_thread(self, json_data):
    if not json_data or 'threads' not in json_data:
      return []

    parsed_posts = []
    for post in json_data['threads'][0]['posts']:
      #print(post)
      parsed_post = {
        'num': post.get('num', ''),
        'subject': post.get('subject', ''),
        'timestamp': post.get('timestamp', 0),
        'comment': post.get('comment', ''),
        'posts_count': post.get('posts_count', 0),
        'images': post.get('images', 0),
        'parent':post.get('parent', 0),
        'name':post.get('name', 0)
      }
      parsed_posts.append(parsed_post)

    return parsed_posts

  def get_threads(self):
    try:
      # Create database engine
      engine = create_engine(self.db_url)

      # Create session
      Session = sessionmaker(bind=engine)
      session = Session()

      # Query posts where parent is 0
      threads = session.query(Posts).filter(Posts.parent==0,Posts.status=="new").all()

      for thread in threads:
        time.sleep(1)
        print("\t\t++++"+str(thread.num))
        thread_data = self.fetch_json("/res/"+str(thread.num))
        if not thread_data:
          thread.status="404"
          session.commit()
          #session.close()
          continue
        thread_posts = self.parse_json_thread(thread_data)
        if thread_posts:
          #posts = parser.parse_json_data(thread_posts)
          self.save_to_postgres(thread_posts,thread.num)
          # for p in thread_posts:
          #   #pass
          #   print(p["num"])
        #thread.status="done"


      session.close()

      return threads

    except Exception as e:
      print(f"Error querying database: {e}")
      return []

  def save_to_postgres(self, posts,parent):
        try:
            # Create database engine
            engine = create_engine(self.db_url)

            # Create tables
            Base.metadata.create_all(engine)

            # Create session
            Session = sessionmaker(bind=engine)
            session = Session()

            # Insert or ignore duplicate threads
            for post in posts:
                # Check if thread already exists
                existing_thread = session.query(Posts).filter_by(num=int(post['num'])).first()
                if not existing_thread:
                    print(int(post['num']), ": NEW POST")
                    if parent==0:
                      tag_ids=str(self.tag_ids)
                    else:
                      tag_ids=""

                    new_thread = Posts(
                        num=int(post['num']),
                        subject=post['subject'],
                        timestamp=post['timestamp'],
                        comment=post['comment'],
                        posts_count=post['posts_count'],
                        images=post['images'],
                        status="new",
                        parent=parent,
                        tag_ids=tag_ids,
                        board="2chanell.moe",
                        board_topic="b"
                    )
                    session.add(new_thread)
                else:
                  print(int(post['num']), ": KNOWN POST")

            session.commit()
            session.close()

            #print(f"Successfully saved {len(posts)} posts to database")

        except Exception as e:
            print(f"Error saving to database: {e}")


def main():
    #parser = ChParser(board='po',tag_ids=[{"type":"tags","id":"2"},{"type":"tags","id":"7"}])
    parser = ChParser(board='b',tag_ids=[{"type":"tags","id":"5"},{"type":"tags","id":"6"}])
    for p in PAGES:
      json_data = parser.fetch_json(p)
      #print(json_data)
      if json_data:
          threads = parser.parse_json_data(json_data)
          parser.save_to_postgres(threads,0)
          # for thread in threads:
          #   pass
          #   print(thread.num)

    parser.get_threads()
    # for posts in parser.get_threads():
    #   print("\t\t++++"+str(posts.num))
    #   json_data = parser.fetch_json("/res/"+str(posts.num))
    #   time.sleep(1)
    #   thread_posts = parser.parse_json_thread(json_data)
    #   if thread_posts:
    #     #posts = parser.parse_json_data(thread_posts)
    #     parser.save_to_postgres(thread_posts,posts.num)
    #     for p in thread_posts:
    #       #pass
    #       print(p)

    # json_data = parser.fetch_json(p)
    # #print(json_data)
    # if json_data:
    #   threads = parser.parse_json_data(json_data)
    #   #parser.save_to_postgres(threads)
    #   for thread in threads:
    #     #pass
    #     print(thread)




if __name__ == "__main__":
    main()
