import streamlit as st
import random
import time
import os
from groq import Groq
from dotenv import load_dotenv


load_dotenv()
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
load_dotenv(
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "nouveauchatbot", ".env")
    )
)


TRIPLETTES_PREMIERE = [
    [specialite.strip() for specialite in triplette.split("|") if specialite.strip()]
    for triplette in os.environ.get("TRIPLETTES_PREMIERE", "").split(";")
    if len([specialite for specialite in triplette.split("|") if specialite.strip()]) == 3
]
if not TRIPLETTES_PREMIERE:
    TRIPLETTES_PREMIERE = [["Mathématiques", "Physique-Chimie", "SVT"]]

SPECIALITES_SAVIO = [
    specialite.strip()
    for specialite in os.environ.get("SPECIALITES_SAVIO", "").split(",")
    if specialite.strip()
]
if not SPECIALITES_SAVIO:
    SPECIALITES_SAVIO = [
        "Mathématiques",
        "Physique-Chimie",
        "NSI",
        "SVT",
        "LLCE",
        "SES",
        "AMC",
        "HGEOSP",
        "HLP",
    ]

# =============================================================================
# 1. CONFIGURATION DE L'INTERFACE ET STYLE (SESSIONS SÉCURISÉES & ANONYMES)
# =============================================================================
st.set_page_config(page_title="SaviOrientation v1.0", page_icon="🤖", layout="centered")

st.title("🤖 SaviOrientation (v1.0)")
st.caption("Assistant d'orientation augmenté par IA — Lycée Français Dominique Savio (Douala)")
st.caption("🔒 *Session anonyme sécurisée. Aucune donnée nominative n'est mémorisée.*")
st.write("---")

# =============================================================================
# 2. APPEL SÉCURISÉ DU POOL D'API VIA VARIABLES D'ENVIRONNEMENT (PAS DE CLÉ DANS LE CODE)
# =============================================================================
# Pour exécuter ce code, vous devez définir ces variables dans votre terminal ou votre serveur :
# export GROQ_API_KEY_SAVIO_A="gsk_votre_cle_A..."
# export GROQ_API_KEY_SAVIO_B="gsk_votre_cle_B..."
# export GROQ_API_KEY_SAVIO_C="gsk_votre_cle_C..."

API_KEYS_POOL = [
    os.environ.get("GROQ_API_KEY_SAVIO_A"),
    os.environ.get("GROQ_API_KEY_SAVIO_B"),
    os.environ.get("GROQ_API_KEY_SAVIO_C"),
]
API_KEYS_POOL.extend(
    cle.strip()
    for cle in os.environ.get("GROQ_API_KEY", "").split(",")
    if cle.strip()
)
API_KEYS_POOL = [cle.strip() for cle in API_KEYS_POOL if cle and cle.strip()]
MODELE_GROQ = os.environ.get("GROQ_MODEL", "openai/gpt-oss-20b").strip()


def reponse_locale_orientation(prompt_utilisateur, orientation):
    """Répondre sans afficher de détail technique si l'IA est indisponible."""
    if "STMG" in orientation:
        return (
            "Rassure-toi, la filière STMG peut ouvrir vers plusieurs études intéressantes. "
            "Après le bac, tu peux notamment envisager un BTS, un BUT ou une licence dans la gestion, le management, le droit ou l'économie.\n\n"
            "Question suivante suggérée : Peux-tu me présenter les BTS et les BUT accessibles après un bac STMG ?"
        )
    triplette = orientation.replace("la triplette", "").strip().rstrip(".")
    return (
        f"Rassure-toi, la triplette {triplette} peut ouvrir vers plusieurs études scientifiques, informatiques ou technologiques. "
        "Par exemple, tu peux envisager une licence informatique, un BUT informatique, une école d'ingénieurs ou une classe préparatoire scientifique. "
        "Tu n'as pas besoin de tout choisir maintenant : ton projet pourra se préciser progressivement.\n\n"
        "Question suivante suggérée : Peux-tu me présenter les formations correspondant à cette triplette ?"
    )


def nettoyer_reponse_ia(texte):
    """Retirer les instructions éventuellement répétées par le modèle."""
    fragments_a_retirer = (
        "Vous pouvez demander au chatbot :",
        "N'utilise aucun tableau",
        "Réponds d'abord à la question",
        "Utilise exactement le format",
    )
    lignes = [
        ligne.strip()
        for ligne in (texte or "").splitlines()
        if ligne.strip()
        and not any(fragment in ligne for fragment in fragments_a_retirer)
    ]
    return "\n\n".join(lignes).strip()


def terminer_texte(texte, ponctuation="."):
    """Garantir un texte non vide et correctement terminé."""
    texte = texte.strip()
    if not texte:
            return "Rassure-toi, ton orientation peut se préciser progressivement avec l'aide du PRIO."
    if texte[-1] not in ".!?":
        texte += ponctuation
    return texte


def question_suivante_orientation(nombre_questions, voie):
    """Retourner une relance différente selon l'étape de l'échange."""
    if voie == "Voie technologique":
        questions = {
            1: "Peux-tu m'expliquer les matières de STMG ?",
            2: "Peux-tu me présenter les BTS et les BUT accessibles après un bac STMG ?",
            3: "Peux-tu me présenter les métiers liés à la filière STMG ?",
            4: "Peux-tu m'expliquer les qualités attendues dans ce métier ?",
            5: "Peux-tu me donner un exemple de parcours après un bac STMG ?",
            6: "Peux-tu m'aider à vérifier si mon projet correspond à la filière STMG ?",
            7: "Peux-tu m'aider à préparer mes questions pour le PRIO ?",
        }
    else:
        questions = {
            1: "Peux-tu m'expliquer le rôle de chaque matière dans cette triplette ?",
            2: "Peux-tu me présenter les formations accessibles après cette triplette ?",
            3: "Peux-tu me présenter les métiers liés à cette triplette ?",
            4: "Peux-tu comparer cette triplette avec une autre combinaison ?",
            5: "Peux-tu me donner un exemple de parcours après cette triplette ?",
            6: "Peux-tu m'aider à vérifier si mon projet correspond à cette triplette ?",
            7: "Peux-tu m'aider à préparer mes questions pour le PRIO ?",
        }
    return questions.get(
        nombre_questions,
        "Peux-tu me présenter les prochaines étapes pour préparer mon orientation ?",
    )


def executer_requete_groq_avec_rotation(
    prompt_systeme, prompt_utilisateur, historique=None, max_tokens=400
):
    """
    Exécute l'inférence sur le modèle Groq configuré.
    Bascule dynamiquement de clé d'environnement en cas de code d'erreur HTTP 429.
    """
    orientation = prompt_systeme.split("L'orientation proposée est :", 1)[-1]
    if not API_KEYS_POOL:
        return reponse_locale_orientation(prompt_utilisateur, orientation)

    cles_disponibles = API_KEYS_POOL.copy()
    random.shuffle(cles_disponibles)
    
    for cle in cles_disponibles:
        try:
            client = Groq(api_key=cle)
            debut_temps = time.time()
            
            completion = client.chat.completions.create(
                model=MODELE_GROQ,
                messages=(
                    [{"role": "system", "content": prompt_systeme}]
                    + (historique or [])
                    + [{"role": "user", "content": prompt_utilisateur}]
                ),
                temperature=0.1, # Température très basse pour garantir une fidélité stricte au texte ONISEP
                max_tokens=max_tokens
            )
            
            fin_temps = time.time()
            st.session_state.derniere_latence = fin_temps - debut_temps
            contenu = completion.choices[0].message.content
            if contenu and contenu.strip():
                return contenu.strip()
            return reponse_locale_orientation(prompt_utilisateur, orientation)
            
        except Exception as e:
            if "429" in str(e) or "rate_limit" in str(e).lower():
                continue # Rotation vers la variable système suivante
            else:
                return reponse_locale_orientation(prompt_utilisateur, orientation)
                
    return reponse_locale_orientation(prompt_utilisateur, orientation)

# =============================================================================
# 3. CONTEXTE RAG SYNTHÉTIQUE (ONISEP / PARCOURSUP / DOMINIQUE SAVIO)
# =============================================================================
BASE_CONNAISSANCES_SAVIO = {
    "📐 Mathématiques | 💻 NSI | 🧪 Physique-Chimie": {
        "contexte": "Référentiel ONISEP/Parcoursup : Option scientifique et technologique d'excellence. La spécialité NSI s'associe aux Mathématiques et à la Physique pour créer le profil de l'[...]
        "debouches": ["Écoles d'Ingénieurs (CPGE ou Post-Bac)", "Licence Informatique / Data Science", "BUT Réseaux et Télécommunications"]
    },
    "📐 Mathématiques | 💻 NSI | 📈 SES": {
        "contexte": "Référentiel AEFE/Savio : Profil interdisciplinaire axé sur l'économie quantitative, les sciences de données de masse (Big Data), l'actuariat et la modélisation statistique d[...]
        "debouches": ["Licence Économie-Gestion / MIASHS", "BUT Statistique et Décisionnel", "Écoles de Commerce (Filières de finance quantitative)"]
    },
    "📐 Mathématiques | 💻 NSI | 🌍 AMC": {
        "contexte": "Référentiel Interne Savio : Alliance de la programmation technique et de l'ouverture internationale bilingue via l'Anglais Monde Contemporain (AMC). Prépare aux carrières mond[...]
        "debouches": ["Bachelors en Informatique internationaux", "Cursus d'ingénierie bilingues", "Métiers de la Cybersécurité internationale"]
    },
    "📐 Mathématiques | 🧪 Physique-Chimie | 🌿 SVT": {
        "contexte": "Référentiel National ONISEP : Combinaison scientifique classique, indispensable pour l'accès aux études de recherche fondamentale, la modélisation de la matière et la compr[...]
        "debouches": ["Études médicales (PASS / L.AS)", "Classes Préparatoires BCPST / PCSI", "Licences de Sciences de la Vie / Recherche"]
    },
    "📐 Mathématiques | 🧪 Physique-Chimie | 📈 SES": {
        "contexte": "Référentiel AEFE : Parcours d'équilibre entre la rigueur cartésienne des sciences dures et les mécanismes économiques macro et micro-structurels.",
        "debouches": ["Classes Préparatoires Commerciales (ECG)", "Licence Éco-Gestion", "Filières universitaires de statistiques de marché"]
    },
    "📐 Mathématiques | 🧪 Physique-Chimie | 🌍 AMC": {
        "contexte": "Référentiel Savio : Profil de recherche ouvert aux publications internationales scientifiques et à l'ingénierie aéronautique ou énergétique mondiale.",
        "debouches": ["Licences de Sciences Physiques", "Écoles d'Ingénieurs internationales", "Filières technologiques à l'étranger"]
    },
    "📜 HLP | 🗺️ HGEOSP | 🔤 LLCE": {
        "contexte": "Référentiel ONISEP/Humanités : Profil littéraire, historique et linguistique complet. Humanités, Littérature et Philosophie (HLP) s'articule avec l'Histoire-Géographie, Gé[...]
        "debouches": ["Licences de Lettres / Sciences du Langage", "Écoles de Journalisme", "Sciences Po / Instituts d'Études Politiques"]
    },
    "📈 SES | 🔤 LLCE | 📜 HLP": {
        "contexte": "Référentiel AEFE : Profil hybride croisant la culture philosophique avec les sciences économiques et la maîtrise des langues étrangères.",
        "debouches": ["Licences de Sciences Sociales / Humanités", "Filières de Communication internationale", "Métiers de la Médiation Culturelle"]
    },
    "📜 HLP | 🗺️ HGEOSP | 📐 Mathématiques": {
        "contexte": "Référentiel Savio : Combinaison hautement équilibrée associant l'esprit critique philosophique à la logique d'analyse mathématique pure.",
        "debouches": ["Classes Préparatoires BL (Lettres et Sciences Sociales)", "Licence de Droit / Sciences Politiques", "Métiers du Conseil"]
    },
    "📈 SES | 🔤 LLCE | 🗺️ HGEOSP": {
        "contexte": "Référentiel ONISEP : Idéal pour analyser les enjeux contemporains, les relations internationales, la sociologie et la gouvernance globale.",
        "debouches": ["Sciences Po / IEP", "Facultés de Droit", "Écoles de Management et Commerce International"]
    },
    "📈 SES | 🔤 LLCE | 📐 Mathématiques": {
        "contexte": "Référentiel AEFE : Profil d'excellence managériale globale, mêlant l'économie, la négociation internationale et les outils quantitatifs mathématiques.",
        "debouches": ["Écoles de Commerce International", "Licences d'Éco-Gestion", "Classes Préparatoires ECG"]
    },
    "📊 Sciences de gestion et numérique | 💼 Management | ⚖️ Droit et économie": {
        "contexte": "Référentiel National STMG (Lycée Savio) : Parcours technologique d'excellence centré sur le fonctionnement concret, juridique, fiscal et financier des organisations, des entre[...]
        "debouches": ["BUT Gestion des Entreprises (GEA)", "Classes Préparatoires ECT", "Licences Professionnelles de Management"]
    }
}

# =============================================================================
# 4. INITIALISATION DE LA SÉCURITÉ DE SESSION
# =============================================================================
if "step" not in st.session_state:
    st.session_state.step = "ACCUEIL"
if "question_index" not in st.session_state:
    st.session_state.question_index = 0
if "scores" not in st.session_state:
    st.session_state.scores = {"R": 0, "I": 0, "A": 0, "S": 0, "E": 0, "C": 0}
if "matiere" not in st.session_state:
    st.session_state.matiere = ""
if "voie" not in st.session_state:
    st.session_state.voie = "Première générale"
if "filiere_retenue" not in st.session_state:
    st.session_state.filiere_retenue = ""
if "triplette_retenue" not in st.session_state:
    st.session_state.triplette_retenue = ""
if "historique_discussion" not in st.session_state:
    st.session_state.historique_discussion = []
if "question_suggeree" not in st.session_state:
    st.session_state.question_suggeree = ""
if "nombre_questions_eleve" not in st.session_state:
    st.session_state.nombre_questions_eleve = 0
if "rappel_prio_affiche" not in st.session_state:
    st.session_state.rappel_prio_affiche = False
if "bilan_prio_affiche" not in st.session_state:
    st.session_state.bilan_prio_affiche = False
if "derniere_latence" not in st.session_state:
    st.session_state.derniere_latence = 0.0
if "reponse_generee" not in st.session_state:
    st.session_state.reponse_generee = False

# Les 10 questions réglementaires d'exploration anonyme
QUESTIONS_RIASEC = [
    {"titre": "### Question 1/10 : Dans un projet de groupe au lycée, quelle mission te correspond le mieux ?", "choix": [{"texte": "🔧 Configurer le matériel informatique ou coder un script", "profil": "R"}, {"texte": "🧪 Concevoir et tester une expérience", "profil": "I"}, {"texte": "🎨 Créer un design ou des visuels", "profil": "A"}, {"texte": "🤝 Expliquer une notion et aider un camarade", "profil": "S"}, {"texte": "🌍 Défendre une idée devant les autres", "profil": "E"}, {"texte": "📊 Organiser les tâches et les délais", "profil": "C"}]},
    {"titre": "### Question 2/10 : Quelle activité te donne le plus d'énergie ?", "choix": [{"texte": "🤝 Expliquer une notion et aider un camarade", "profil": "S"}, {"texte": "📊 Organiser des données ou des objets", "profil": "C"}, {"texte": "🛠️ Réparer ou fabriquer quelque chose", "profil": "R"}, {"texte": "📚 Chercher des informations et apprendre", "profil": "I"}, {"texte": "🎨 Créer quelque chose de nouveau", "profil": "A"}, {"texte": "🗣️ Convaincre ou négocier avec d'autres", "profil": "E"}]},
    {"titre": "### Question 3/10 : Pour un nouveau projet, tu préfères...", "choix": [{"texte": "🛠️ Fabriquer et tester un prototype", "profil": "R"}, {"texte": "🧠 Résoudre un problème complexe", "profil": "I"}, {"texte": "🎼 Créer quelque chose d'artistique", "profil": "A"}, {"texte": "👥 Travailler en équipe et échanger", "profil": "S"}, {"texte": "🎯 Atteindre un objectif précis", "profil": "E"}, {"texte": "📋 Planifier et organiser étape par étape", "profil": "C"}]},
    {"titre": "### Question 4/10 : Face à un problème, tu commences par...", "choix": [{"texte": "🔩 Chercher une solution pratique et immédiatement testable", "profil": "R"}, {"texte": "🔎 Fouiller dans les causes pour bien comprendre", "profil": "I"}, {"texte": "✨ Imaginer plusieurs approches créatives", "profil": "A"}, {"texte": "🤝 Demander l'avis de quelqu'un de confiance", "profil": "S"}, {"texte": "💪 Prendre les choses en main rapidement", "profil": "E"}, {"texte": "📝 Faire une liste des étapes à suivre", "profil": "C"}]},
    {"titre": "### Question 5/10 : Dans une activité scolaire, tu aimerais surtout...", "choix": [{"texte": "🌍 Défendre une idée qui te tient à cœur", "profil": "E"}, {"texte": "🎼 Créer un projet original et personnel", "profil": "A"}, {"texte": "⚙️ Fabriquer un objet ou un système", "profil": "R"}, {"texte": "📚 Découvrir comment les choses fonctionnent", "profil": "I"}, {"texte": "💬 Discuter et écouter tes camarades", "profil": "S"}, {"texte": "🎯 Obtenir les meilleurs résultats possibles", "profil": "C"}]},
    {"titre": "### Question 6/10 : Quel rôle prends-tu naturellement dans un groupe ?", "choix": [{"texte": "🗣️ Encourager les autres et faciliter les échanges", "profil": "S"}, {"texte": "📅 Organiser le travail et vérifier le respect des délais", "profil": "C"}, {"texte": "🔧 Proposer des solutions pratiques et fonctionnelles", "profil": "R"}, {"texte": "💡 Apporter des idées originales et nouvelles", "profil": "A"}, {"texte": "🧠 Analyser en profondeur et poser les bonnes questions", "profil": "I"}, {"texte": "🎤 Prendre la parole et motiver le groupe", "profil": "E"}]},
    {"titre": "### Question 7/10 : Quel résultat te rendrait le plus fier ?", "choix": [{"texte": "⚙️ Un objet ou un système qui fonctionne réellement", "profil": "R"}, {"texte": "📐 Une démonstration logique et élégante", "profil": "I"}, {"texte": "🎨 Une création personnelle et originale", "profil": "A"}, {"texte": "🤝 Une bonne ambiance et une solidarité d'équipe", "profil": "S"}, {"texte": "🏆 Avoir atteint mon objectif et surpassé les autres", "profil": "E"}, {"texte": "✅ Un travail parfaitement structuré et sans erreurs", "profil": "C"}]},
    {"titre": "### Question 8/10 : Quelle tâche acceptes-tu volontiers ?", "choix": [{"texte": "📚 Lire, comparer et synthétiser plusieurs sources", "profil": "I"}, {"texte": "🗂️ Classer des données ou organiser un système", "profil": "C"}, {"texte": "🛠️ Manipuler, construire ou réparer un objet", "profil": "R"}, {"texte": "🎨 Dessiner, illustrer ou créer des visuels", "profil": "A"}, {"texte": "💬 Écouter quelqu'un qui a un problème", "profil": "S"}, {"texte": "📢 Présenter ton travail ou tes idées à un public", "profil": "E"}]},
    {"titre": "### Question 9/10 : Quel environnement de travail te convient le mieux ?", "choix": [{"texte": "🏗️ Un atelier, un laboratoire technique ou un espace de fabrication", "profil": "R"}, {"texte": "📖 Une bibliothèque calme pour réfléchir et analyser", "profil": "I"}, {"texte": "🎭 Un studio créatif avec du matériel artistique", "profil": "A"}, {"texte": "👫 Un espace collaboratif pour travailler avec d'autres", "profil": "S"}, {"texte": "🏢 Un bureau moderne avec des projets stimulants", "profil": "E"}, {"texte": "📋 Un espace bien organisé avec des processus clairs", "profil": "C"}]},
    {"titre": "### Question 10/10 : Pour choisir une orientation, tu accordes le plus d'importance à...", "choix": [{"texte": "🎨 La possibilité d'exprimer ta créativité", "profil": "A"}, {"texte": "🧠 Comprendre les phénomènes et les concepts", "profil": "I"}, {"texte": "⚙️ Fabriquer ou transformer des choses concrètes", "profil": "R"}, {"texte": "👥 Aider les autres et contribuer à la société", "profil": "S"}, {"texte": "💼 Réussir professionnellement et bien gagner ta vie", "profil": "E"}, {"texte": "✅ Avoir une carrière stable et prévisible", "profil": "C"}]}
]


def creer_questionnaire_aleatoire():
    questions = random.sample(QUESTIONS_RIASEC, len(QUESTIONS_RIASEC))
    return [
        {**question, "choix": random.sample(question["choix"], len(question["choix"]))}
        for question in questions
    ]


if "questions_aleatoires" not in st.session_state:
    st.session_state.questions_aleatoires = creer_questionnaire_aleatoire()


def reinitialiser_session():
    st.session_state.step = "ACCUEIL"
    st.session_state.question_index = 0
    st.session_state.scores = {profil: 0 for profil in "RIASEC"}
    st.session_state.matiere = ""
    st.session_state.voie = "Première générale"
    st.session_state.filiere_retenue = ""
    st.session_state.triplette_retenue = ""
    st.session_state.question_suggeree = ""
    st.session_state.historique_discussion = []
    st.session_state.nombre_questions_eleve = 0
    st.session_state.rappel_prio_affiche = False
    st.session_state.bilan_prio_affiche = False
    st.session_state.reponse_generee = False
    st.session_state.questions_aleatoires = creer_questionnaire_aleatoire()


def choisir_triplette():
    if st.session_state.voie == "Voie technologique":
        st.session_state.filiere_retenue = "STMG"
        return []

    specialites_technologiques = {
        "Sciences de gestion et numérique",
        "Management",
        "Droit et économie",
    }
    if st.session_state.voie == "Voie technologique":
        triplettes_disponibles = []
    else:
        triplettes_disponibles = [
            triplette
            for triplette in TRIPLETTES_PREMIERE
            if not any(specialite in specialites_technologiques for specialite in triplette)
            and all(specialite in SPECIALITES_SAVIO for specialite in triplette)
        ]

    if not triplettes_disponibles:
        triplettes_disponibles = TRIPLETTES_PREMIERE
    if not triplettes_disponibles:
        return []
    profil = max(st.session_state.scores, key=st.session_state.scores.get)
    priorites = {
        "R": ["Mathématiques", "Physique-Chimie", "NSI", "SVT"],
        "I": ["Mathématiques", "Physique-Chimie", "SVT", "NSI"],
        "A": ["LLCE", "HLP", "AMC", "HGEOSP"],
        "S": ["HLP", "SES", "LLCE", "HGEOSP"],
        "E": ["SES", "HGEOSP", "Mathématiques", "LLCE"],
        "C": ["Mathématiques", "SES", "HGEOSP", "NSI"],
    }
    matieres = {
        "Mathématiques / Sciences": {"Mathématiques", "Physique-Chimie", "SVT", "NSI"},
        "Lettres / Langues": {"LLCE", "HLP", "AMC", "HGEOSP"},
        "Sciences humaines / Économie": {"SES", "HGEOSP", "Mathématiques"},
    }
    priorite = priorites[profil]
    matiere = matieres.get(st.session_state.matiere, set())

    def score(triplette):
        return (
            sum(len(priorite) - priorite.index(s) for s in triplette if s in priorite),
            sum(s in matiere for s in triplette),
        )

    return max(triplettes_disponibles, key=score)


st.markdown(
    """
    <style>
    .hero { padding: 1.4rem 1.6rem; border-radius: 14px; background: linear-gradient(120deg, #0b3954, #087e8b); color: white; margin-bottom: 1rem; }
    .hero h2 { color: white; margin: 0; }
    .hero p { margin-bottom: 0; opacity: .88; }
    .result { padding: 1.2rem; border-left: 5px solid #f2a900; background: #fff8e7; border-radius: 8px; }
    [data-testid="stChatMessage"] {
        padding: 1rem 1.1rem;
        margin: .7rem 0;
        border: 1px solid #d9e2ec;
        border-radius: 12px;
        background: #ffffff;
    }
    [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] {
        color: #17202a;
        font-size: 1rem;
        line-height: 1.65;
        max-width: 72ch;
    }
    [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] p {
        margin: .25rem 0 .7rem;
    }
    [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] h1,
    [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] h2,
    [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] h3 {
        color: #0b3954;
        line-height: 1.3;
    }
    [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] ul,
    [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] ol {
        margin: .3rem 0 .7rem;
        padding-left: 1.4rem;
    }
    [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] table {
        display: block;
        max-width: 100%;
        overflow-x: auto;
        border-collapse: collapse;
        margin: .7rem 0;
    }
    [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] th,
    [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] td {
        padding: .45rem .65rem;
        border: 1px solid #cbd5e1;
        text-align: left;
    }
    [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] th {
        background: #e8f1f5;
        color: #0b3954;
    }
    [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] code {
        color: #0b3954;
        background: #edf2f7;
        padding: .1rem .3rem;
        border-radius: 4px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.subheader("Votre parcours")
    nombre_questions = len(st.session_state.questions_aleatoires)
    st.caption(f"Question {min(st.session_state.question_index + 1, nombre_questions)} sur {nombre_questions}")
    st.progress(min((st.session_state.question_index + 1) / nombre_questions, 1.0))
    if st.button("Recommencer", use_container_width=True):
        reinitialiser_session()
        st.rerun()
    if st.session_state.step == "RESULTAT":
        st.divider()
        st.subheader("Votre orientation")
        if st.session_state.voie == "Voie technologique":
            st.success("Filière STMG")
        else:
            triplette_laterale = (
                st.session_state.triplette_retenue or choisir_triplette()
            )
            st.success(" + ".join(triplette_laterale))

st.markdown(
    '<div class="hero"><h2>Une orientation qui part de vous</h2><p>Explorez vos préférences et découvrez une combinaison de spécialités cohérente.</p></div>',
    unsafe_allow_html=True,
)

if st.session_state.step == "ACCUEIL":
    st.subheader("Bienvenue")
    st.write("Ce parcours anonyme vous aide à identifier une première piste d'orientation.")
    col1, col2, col3 = st.columns(3)
    col1.metric("Questions", len(st.session_state.questions_aleatoires))
    col2.metric("Profils", "RIASEC")
    col3.metric("Triplettes", len(TRIPLETTES_PREMIERE))
    st.write("### Spécialités proposées à Savio")
    st.write(", ".join(SPECIALITES_SAVIO))
    if st.button("Commencer l'exploration", type="primary", use_container_width=True):
        st.session_state.step = "QUESTIONNAIRE"
        st.rerun()

elif st.session_state.step == "QUESTIONNAIRE":
    question = st.session_state.questions_aleatoires[st.session_state.question_index]
    st.info(f"Question {st.session_state.question_index + 1} sur {len(st.session_state.questions_aleatoires)}")
    st.write(question["titre"])
    choix = {option["texte"]: option["profil"] for option in question["choix"]}
    reponse = st.radio("Choisissez la réponse qui vous ressemble le plus", list(choix), label_visibility="collapsed")
    if st.button("Valider ma réponse", type="primary", use_container_width=True):
        st.session_state.scores[choix[reponse]] += 1
        if st.session_state.question_index + 1 < len(st.session_state.questions_aleatoires):
            st.session_state.question_index += 1
        else:
            st.session_state.step = "MATIERE"
        st.rerun()

elif st.session_state.step == "MATIERE":
    st.subheader("Votre entrée en première")
    st.session_state.voie = st.radio(
        "Quelle voie envisagez-vous pour la classe de première ?",
        ["Première générale", "Voie technologique"],
    )
    if st.session_state.voie == "Voie technologique":
        st.info("À Savio, la voie technologique proposée est la filière STMG.")
    else:
        st.info("La recommandation portera sur trois spécialités de première générale.")
    st.write("### Votre matière forte")
    st.session_state.matiere = st.radio(
        "Quelle famille de matières vous donne le plus confiance ?",
        ["Mathématiques / Sciences", "Lettres / Langues", "Sciences humaines / Économie"],
    )
    if st.button("Voir ma recommandation", type="primary", use_container_width=True):
        st.session_state.triplette_retenue = choisir_triplette()
        st.session_state.step = "RESULTAT"
        st.rerun()

elif st.session_state.step == "RESULTAT":
    st.subheader("Votre recommandation")
    triplette = st.session_state.triplette_retenue or choisir_triplette()
    st.session_state.triplette_retenue = triplette
    if st.session_state.voie == "Voie technologique":
        st.markdown(
            '<div class="result"><h3>Filière STMG</h3><p>À Savio, la voie technologique correspond à la filière Sciences et Technologies du Management et de la Gestion.</p></div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f"<div class=\"result\"><h3>{' + '.join(triplette)}</h3><p>Ces trois spécialités correspondent à votre entrée en première générale.</p></div>",
            unsafe_allow_html=True,
        )
    st.write("### Vos scores RIASEC")
    st.bar_chart(st.session_state.scores)
    st.write("### Échange avec votre conseiller IA")
    st.caption(
        "Posez une question sur les matières, les études ou les débouchés liés à votre orientation."
    )

    for message in st.session_state.historique_discussion:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if st.session_state.question_suggeree:
        st.info(
            f"Suggestion facultative à envoyer au chatbot : {st.session_state.question_suggeree}"
        )

    if st.session_state.rappel_prio_affiche:
        st.warning(
            "Pour approfondir cette recommandation, prenez également attache avec le PRIO de votre établissement."
        )
    if st.session_state.bilan_prio_affiche:
        st.info(
            "Bilan terminé. Ce chatbot donne une première information et ne remplace pas un professionnel de l'orientation. Prends rendez-vous avec le PRIO pour valider ton projet."
        )

    question_eleve = st.chat_input("Écrivez votre question...")
    if question_eleve:
        st.session_state.nombre_questions_eleve += 1
        if st.session_state.nombre_questions_eleve == 7:
            st.session_state.rappel_prio_affiche = True
        if st.session_state.nombre_questions_eleve >= 15:
            st.session_state.bilan_prio_affiche = True
        st.session_state.historique_discussion.append(
            {"role": "user", "content": question_eleve}
        )
        contexte_orientation = (
            "la filière STMG"
            if st.session_state.voie == "Voie technologique"
            else "la triplette " + " + ".join(triplette)
        )
        question_lower = question_eleve.lower()
        etape_conversation = question_suivante_orientation(
            st.session_state.nombre_questions_eleve,
            st.session_state.voie,
        )
        demande_etudes = "étude" in question_lower or "formation" in question_lower
        demande_triplette = "triplette" in question_lower
        bilan_final = st.session_state.nombre_questions_eleve >= 15
        if bilan_final:
            consigne_format = (
                "Fais maintenant un bilan clair de toute la conversation. "
                "Rappelle les intérêts et les points forts exprimés, l'orientation proposée, "
                "les pistes d'études ou de métiers évoquées, puis donne deux conseils concrets. "
                "Termine en conseillant à l'élève de rencontrer le PRIO, car tu n'es pas un professionnel de l'orientation. "
                "Tu peux utiliser un tableau si cela rend le bilan plus clair."
            )
        elif st.session_state.nombre_questions_eleve >= 8:
            consigne_format = (
                "Tu peux répondre plus en détail, en 3 à 6 paragraphes courts. "
                "Tu peux utiliser un seul tableau si cela aide vraiment l'élève. "
                "Reste progressif et ne donne pas toutes les informations d'un seul coup."
            )
        else:
            consigne_format = (
                "Réponds en 2 à 4 petits paragraphes, avec 120 mots maximum. "
                "Donne seulement l'information nécessaire à la question actuelle. "
                "N'utilise pas de tableau avant la huitième question."
            )
        if (
            st.session_state.voie == "Première générale"
            and demande_etudes
            and demande_triplette
            and not bilan_final
        ):
            reponse_brute = reponse_locale_orientation(
                question_eleve, contexte_orientation
            )
        else:
            reponse_brute = executer_requete_groq_avec_rotation(
                (
                "Tu es un conseiller d'orientation bienveillant pour un élève de 15 ans. "
                "Adresse-toi toujours directement à l'élève avec tu et ton. "
                "Commence si nécessaire par une phrase rassurante et encourageante, sans minimiser sa question. "
                "Ne juge jamais ses choix et rappelle que l'orientation se construit progressivement. "
                "Réponds progressivement en français, avec des informations concrètes et prudentes. "
                "Utilise des phrases simples et courtes. "
                "Chaque phrase doit être complète et se terminer par un point. "
                "N'interromps jamais une phrase et ne termine jamais une réponse au milieu d'une idée. "
                f"{consigne_format} "
                "Si un sujet comporte plusieurs étapes, commence par la première et garde les suivantes pour les prochains échanges. "
                "Lis l'historique pour comprendre le contexte, mais ne répète pas une réponse déjà donnée. "
                "Réponds précisément à la question actuelle, même si elle change de sujet. "
                f"Étape actuelle de l'échange : question {st.session_state.nombre_questions_eleve}. "
                f"La prochaine étape prévue est : {etape_conversation} "
                f"Les spécialités générales proposées au lycée Savio sont : {', '.join(SPECIALITES_SAVIO)}. "
                f"L'orientation proposée est : {contexte_orientation}. "
                "Réponds d'abord à la question, puis propose une seule suggestion facultative "
                "formulée comme une demande de l'élève adressée au chatbot, "
                "par exemple : Peux-tu me présenter les études correspondant à cette orientation ? "
                "Utilise exactement le format : Question suivante suggérée : [demande de l'élève] "
                "Utilise au maximum un seul tableau dans toute ta réponse."
                ),
                    question_eleve,
                    [
                        {"role": message["role"], "content": message["content"]}
                        for message in st.session_state.historique_discussion[:-1]
                    ],
                    max_tokens=900 if bilan_final or st.session_state.nombre_questions_eleve >= 8 else 400,
            )
        reponse_brute = nettoyer_reponse_ia(reponse_brute)
        marqueur = "Question suivante suggérée :"
        if marqueur in reponse_brute:
            reponse, _ = reponse_brute.split(marqueur, 1)
        else:
            reponse = reponse_brute
        reponse = nettoyer_reponse_ia(reponse)
        if not reponse:
            reponse_locale = reponse_locale_orientation(
                question_eleve, contexte_orientation
            )
            reponse, _ = reponse_locale.split(marqueur, 1)
        st.session_state.question_suggeree = question_suivante_orientation(
            st.session_state.nombre_questions_eleve,
            st.session_state.voie,
        )
        st.session_state.historique_discussion.append(
            {"role": "assistant", "content": terminer_texte(reponse)}
        )
        st.session_state.reponse_generee = True
        st.rerun()
