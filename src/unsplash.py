import requests, time

NPOINT = "https://api.npoint.io/9e625c836edf8e4047a8"
ACCESS = "3rCvegfHPdPLT7BxDyMEY3nP3FXwr6do-GkTqeOIq4o"
SECRET = "-cpt2H1q-GDk7mvP-TrEMuwGHCqvAZvQ2d39ISPSOIc"
ID = "596454"

UNSPLASH = "https://api.unsplash.com/search/photos"


headers = {
      "Accept-Version": "v1",
      "Authorization": f"Client-ID {ACCESS}"
}

data = requests.get(NPOINT).json()
images_dict = {}
countries = data['countries']

for country in countries[195:]:
      name = country['country']
      images_list = []
      parameters = {
            "query": name,
            "orientation": "landscape"
      }

      while True:
            try:
                  img_data = requests.get(UNSPLASH, params=parameters, headers=headers).json()
                  break  # Break out of the loop if request succeeds
            except requests.RequestException as e:
                  print(f"An error occurred: {e}")
                  print(f"Retrying in 1 hour...")
                  time.sleep(3600)

      for i in range(3):
            try:
                  url = img_data["results"][i]["urls"]["raw"]
            except IndexError:
                  continue
            images_list.append(url)

      images_dict[name] = images_list
      print(images_dict)
      time.sleep(1)




# Now images_dict will contain image URLs for each country, with rate limiting and error handling




