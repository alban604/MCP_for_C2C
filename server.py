from mcp.server import MCPServer
import httpx
import sys
from selenium import webdriver
from selenium.webdriver.common.by import By
import csv
import time
from ddgs import DDGS
import requests
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import os
from google import genai
import time
import requests
import pandas as pd
from datetime import date, timedelta
import concurrent.futures
from markdownify import markdownify as md
import pdfkit
from dotenv import load_dotenv


load_dotenv()

mcp = MCPServer("ServeurDemo")

def recherche_listes_url(mot_cle,nb_lien_renvoye=20):
    """renvoie la liste d'url obtenu après une recherche avec le mot clé

    Args:
        mot_cle (str): _description_
        nb_lien_renvoye (int, optional): _description_. Defaults to 20.

    Returns:
        _type_: _description_
    """
    print(f"--- Recherche pour : '{mot_cle}' ---\n")

    with DDGS() as ddgs:
        
        resultats = ddgs.text(mot_cle, region='fr-fr', max_results=nb_lien_renvoye)
        
        if not resultats:
            print("Aucun résultat trouvé ou requête bloquée.")
            return
    
    return [r["href"] for r in resultats]

def scrap_content_from_url_c2c(url):
    """Renvoie le contenu texte d'une page web à partir de l'url mais enlève les bordures de C2C. 

    Args:
        url (str): url de la page web

    Returns:
        str : contenu de la page web
    """
    with sync_playwright() as p:
        # Lance un navigateur Chromium (invisible par défaut)
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # Va sur la page et ATTEND que le site ait fini de charger ses scripts
        page.goto(url)
        page.wait_for_load_state("networkidle") 

        element = page.locator(".is-12-print")
        l_boite = page.locator(".box").all()
        html_content = [b.inner_html() for b in l_boite]
        browser.close()

    soup =""
    for elt in html_content[4:6]: #ne récupère que le contenu intéressant
        soup += BeautifulSoup(elt, "html.parser").text
    return soup

@mcp.tool()
def recherche_l_url_de_l_itineraire_C2C(itineraire,lieu=None):
    """Renvoie l'url camptocamp de l'itinéraire à partir du nom de l'itinéraire et du lieu (optionnel)
    Recherche seulement les urls d'itinéraires (routes).
    Args:
        itineraire (str): nom de l'itinéraire à rechercher

    Returns:
        str : url camptocamp à utiliser
    """
    if not(lieu):
        mot_cle=itineraire + "CampToCamp"
    else:
        mot_cle = itineraire + " " +lieu + " " +"CampToCamp"

    l_url = recherche_listes_url(mot_cle,20)
    l_url_c2c = [url for url in l_url if "www.camptocamp.org" in url and "/routes/" in url]
    print(l_url_c2c[0])
    return l_url_c2c[0]

def save_topo_as_pdf(url, nom_de_dossier):
    """Sauvegarde le topo dont l'url est passé en paramètre en pdf dans le dossier nom_de_dossier

    Args:
        url_topo (str) : url du topo de l'itinéraire que l'on souhaite sauvegarder 
        nom_de_dossier : nom du dossier dans laquelle doit être sauvegarder le document. Met le nom de l'itinéraire par défaut si aucune précision ne t'es donné par l'utilisateur
                        Ce dossier sera créer si pas existant
    Returns:
        None
    """
    os.makedirs(nom_de_dossier,exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, wait_until="networkidle")
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(1000)
        page.pdf(path=f"{nom_de_dossier}/topo_c2c.pdf", format="A4", print_background=True)
        
        browser.close()

@mcp.tool()
def scrap_content_from_url(url):
    """Renvoie le contenu texte d'une page web à pstr(soup)artir de l'url. 

    Args:
        url (str): url de la page web

    Returns:
        str : contenu de la page web
    """
    with sync_playwright() as p:
        # Lance un navigateur Chromium (invisible par défaut)
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # Va sur la page et ATTEND que le site ait fini de charger ses scripts
        page.goto(url)
        page.wait_for_load_state("networkidle") 
        
        # Récupère le code HTML complet (une fois le JavaScript exécuté)
        html_complet = page.content()
        browser.close()

    soup = BeautifulSoup(html_complet, "html.parser")
    texte_markdown = soup.text
    return texte_markdown


@mcp.tool()
def get_mon_niveau():
    """Renvoie un texte qui explique mon niveau en alpinisme, en escalade et en cascade de glace

    Returns:
        str:
    """
    return "Escalade : 6b à vue en couenne (max) ; 6a à l'aise \n Alpinsime : j'ai réussi le pilier sud de la barre des écrins et la voie Pierre-Alain à la Meije"

@mcp.tool()
def explainning_how_to_get_condition():
    """Donnes la méthode (les tools à utiliser) pour récupérer les conditions pour un itinéraire (les outils que tu devras utiliser)
    OBLIGATOIRE A UTILISER EN PREMIER SI L'UTILISATEUR DEMANDE LES CONDITIONS D'UN ITINERAIRE
    """
    return "1. Tu récupereras les dernières sorties (get_dernières_sorties) en regardant si il y en a qui sont récentes. Tu ignoreras les sorties datant d'une autre année et tu ne regarderas que la plus récente et celle qui sont à une semaine d'intervalle de la plus récente (max). \n 2. Tu détermineras le lieu de l'itinéraire. Pour cela tu peux utiliser la fonction get_location_from_itinerary. \n 3. Tu consulteras les conditions météo des jours précédents grace à la fonction get_weather_from_few_days_ago. Tu en déduiras les conditions actuelles et fournira en conséquence un bilan et un prognostic sur la faisabilité de l'itinéraire en ce moment.  \n 4. Tu consulteras la météo pour les jours prochains et estimera aussi les conditions à ce moment-là"
@mcp.tool()
def get_dernieres_sorties(url_c2c):
    """Récupères les dernières sorties de l'itinéraires dont l'url camptocamp est url_c2c et les renvoie sous forme de texte.

    Args:
        url_c2c (str): L'url camptocamp de l'itinéraire. ATTENTION TU DOIS IMPER: évalue si le rocher d'une voie sera sec, ou, dans le cas d'un couloir alpin, si le remplissage en neige sera suffisant et en bonne condition.ATIVEMENT UTILISER recherche_l_url_de_l_itineraire_C2C avant d'utiliser cette fonction pour récupérer l'url et la rentrer en paramètre

    Returns:
        str: chaine de caractère qui contient le contenu des dernières sorties 
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url_c2c)
        page.wait_for_load_state("networkidle", timeout=60000) 

        liens = page.get_by_role("link").all()
        all_url = []
        for lien in liens:
            url = lien.get_attribute("href")
            if url:
                if "outings" in url:
                    all_url.append(url)

        browser.close()

    if len(all_url)>9:
        all_url=all_url[-9:]


    arg = iter(["https://www.camptocamp.org"+url for url in all_url])
    with concurrent.futures.ThreadPoolExecutor() as executor:
        resultats = list(executor.map(scrap_content_from_url_c2c, arg))

    txt_return = ""
    for i in range(0,len(resultats)):
        txt_return+=f"[Sortie {i+1}] "+ resultats[i] +"\n"
    return txt_return

@mcp.tool()
def get_weather_from_few_days_ago(latitude,longitude):
    """Renvoie les données météos des 7 derniers jours à la localisation localisation sous la forme d'un DataFrame (transformé en string)

    Args:
        latitude (int): latitude du lieu duquel on veut récupérer la météo
        longitude (int): longitude du lieu duquel on veut récupérer la météo
    
    SI TU NE CONNAIS PAS LA LATITUDE ET LA LONGITUDE du lieu tu peux appeler la fonction get_coordonnee_from_localisation()
    """
    #obtenir la date d'aujourd'hui

    aujourd_hui = date.today()
    end_date = aujourd_hui.strftime("%Y-%m-%d")

    start_date = aujourd_hui - timedelta(days=7)

    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": start_date,
        "end_date": end_date,
        "hourly": "temperature_2m,precipitation",
        "timezone": "Europe/Paris"
    }

    response = requests.get(url, params=params)
    data = response.json()

    df = pd.DataFrame(data["hourly"])
    df["time"] = pd.to_datetime(df["time"])
    return df.to_markdown(index=False)

def get_weather_for_following_days():
    pass

@mcp.tool()
def get_coordonnee_from_itineraire(itinéraire):
    """
    Renvoie les coordonnées gps de l'itinéraire passé en paramètre.
    """
    CLE_API = os.getenv("GEMINI_API_KEY")

    client = genai.Client(api_key=CLE_API)

    response = client.models.generate_content(
        model='gemini-3.1-flash-lite',
        contents=f"Quelles sont les coordonnées GPS de {itinéraire}. "
    )
    return response.text

if __name__ == "__main__":
    # Lance la boucle d'écoute sur stdin/stdout
    #url = recherche_l_url_de_l_itineraire_C2C("Eperon Frendo","Chamonix")
    #print("check")
    #scrap_content_from_url(url)
    mcp.run()
    #url_frendo = "https://www.camptocamp.org/routes/53824/fr/barre-des-ecrins-pilier-s"
    #print(scrap_content_from_url_c2c(url_frendo))

    #save_topo_as_pdf(url_frendo,"test")

    #print(get_weather_from_few_days_ago(6.8858,45.8775))

    #print(get_coordonnee_from_itineraire("Eperon Frendo Chamonix"))