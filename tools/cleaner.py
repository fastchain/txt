import requests


class FlarumCleaner:
    def __init__(self, baseUrl,username,password):
        """
        Initialize the FlarumCleaner with configuration from a YAML file.
        """


        self.base_url = baseUrl
        self.admin_username = username
        self.admin_password = password
        self.session = requests.Session()
        self.token = None

    def login(self):
        """
        Logs in to the Flarum instance and obtains the authentication token.
        """
        url = f"{self.base_url}/api/token"
        payload = {
            "identification": self.admin_username,
            "password": self.admin_password,
            "remember": True
        }

        try:
            response = self.session.post(url, json=payload)
            response.raise_for_status()
            self.token = response.json()['token']
            print("Login successful.")
            return True
        except requests.exceptions.RequestException as e:
            print(f"Login failed: {e}")
            return False

    def get_discussions(self):
        """
        Retrieves a list of all discussions from the Flarum instance.
        """
        url = f"{self.base_url}/api/discussions?page[limit]=1000"
        headers = {'Authorization': f'Bearer {self.token}'}
        try:
            response = self.session.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            discussions = data['data']
            return discussions
        except requests.exceptions.RequestException as e:
            print(f"Failed to get discussions: {e}")
            return []

    def delete_discussion(self, discussion_id):
        """
        Deletes a single discussion from the Flarum instance.
        """
        url = f"{self.base_url}/api/discussions/{discussion_id}"
        headers = {'Authorization': f'Token {self.token}'}
        try:
            response = self.session.delete(url, headers=headers)
            response.raise_for_status()
            print(f"Discussion {discussion_id} deleted successfully.")
            return True
        except requests.exceptions.RequestException as e:
            print(f"Failed to delete discussion {discussion_id}: {e}")
            return False

    def delete_all_discussions(self):
        """
        Deletes all discussions from the Flarum instance.
        """
        discussions = self.get_discussions()
        if not discussions:
            print("No discussions found.")
            return

        for discussion in discussions:
            self.delete_discussion(discussion['id'])

        print("All discussions deleted successfully.")
    def get_users(self):
      """
      Retrieves a list of all users from the Flarum instance.
      """
      url = f"{self.base_url}/api/users"
      headers = {'Authorization': f'Token {self.token}'}
      try:
        response = self.session.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        users = data['data']
        return users
      except requests.exceptions.RequestException as e:
        print(f"Failed to get users: {e}")
        return []

    def delete_user(self, user_id):
      """
      Deletes a single user from the Flarum instance.
      """
      url = f"{self.base_url}/api/users/{user_id}"
      headers = {'Authorization': f'Token {self.token}'}
      try:
        response = self.session.delete(url, headers=headers)
        response.raise_for_status()
        print(f"User {user_id} deleted successfully.")
        return True
      except requests.exceptions.RequestException as e:
        print(f"Failed to delete user {user_id}: {e}")
        return False

    def delete_all_users(self):
      """
      Deletes all users from the Flarum instance.
      """
      users = self.get_users()
      if not users:
        print("No users found.")
        return

      for user in users:
        self.delete_user(user['id'])

      print("All users deleted successfully.")


    def run(self):
        """
        Runs the Flarum cleaner: logs in, gets discussions, and deletes them.
        """
        if self.login():
            self.delete_all_discussions()
            #self.delete_all_users()
        else:
            print("Failed to run Flarum cleaner.")

if __name__ == "__main__":
    cleaner = FlarumCleaner("http://127.0.0.1","admin","xxxxxxxxxx")
    while True:
      cleaner.run()
