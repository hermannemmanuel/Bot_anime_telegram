import requests
import schedule
import time
import json
import os
import re
from html import unescape
from telegram import Bot

TOKEN = '7586107707:AAEB0StSNaWRjXNi2XI_82SK0YC3DMjPPTo'
CANAL = '@ANIMES_VF_VOSFR'
FICHIER_SORTIES = 'sorties.json'
bot = Bot(token=TOKEN)

if os.path.exists(FICHIER_SORTIES):
    with open(FICHIER_SORTIES, 'r') as f:
        dernieres_sorties = set(json.load(f))
else:
    dernieres_sorties = set()

def nettoyer_description(description):
    description = unescape(description or 'Pas de synopsis')
    description = re.sub('<[^<]+?>', '', description)
    return (description[:200] + '...') if len(description) > 200 else description

def publier_nouvelles():
    global dernieres_sorties
    query = '''
    query {
      Page(page: 1, perPage: 5) {
        media(type: ANIME, status: RELEASING, sort: UPDATED_AT_DESC) {
          id
          title {
            romaji
          }
          description
          episodes
        }
      }
    }
    '''
    url = 'https://graphql.anilist.co'

    try:
        response = requests.post(url, json={'query': query})
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print(f"[ERREUR] Requête échouée : {e}")
        return

    titres_actuels = {media['title']['romaji'] for media in data['data']['Page']['media']}
    nouvelles_sorties = titres_actuels - dernieres_sorties

    if nouvelles_sorties:
        for media in data['data']['Page']['media']:
            titre = media['title']['romaji']
            if titre in nouvelles_sorties:
                desc = nettoyer_description(media['description'])
                lien_episode_precedent = "🔁 Bientôt disponible"
                anilist_url = f"https://anilist.co/anime/{media['id']}"
                message = (
                    f"🎬 #New_Hebdo\n"
                    f"🌟 *{titre}*\n"
                    f"{desc}\n\n"
                    f"🔗 [Voir sur AniList]({anilist_url})\n"
                    f"🔁 Épisode précédent : {lien_episode_precedent}\n"
                    f"📣 Suivez 👉 {CANAL} pour ne rien rater !"
                )

                try:
                    bot.send_message(chat_id=CANAL, text=message, parse_mode='Markdown')
                    print(f"[OK] Publié : {titre}")
                except Exception as e:
                    print(f"[ERREUR] Envoi échoué pour {titre} : {e}")
    else:
        print("[INFO] Aucune nouvelle sortie.")

    dernieres_sorties = titres_actuels
    with open(FICHIER_SORTIES, 'w') as f:
        json.dump(list(dernieres_sorties), f)

schedule.every().hour.do(publier_nouvelles)
print("[INFO] Bot lancé...")

while True:
    schedule.run_pending()
    time.sleep(1)