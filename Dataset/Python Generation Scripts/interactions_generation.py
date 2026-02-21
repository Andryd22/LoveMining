import pandas as pd
import numpy as np
import random
import time
import sys

# --- CONFIGURAZIONE ---
INPUT_FILE = 'dataset1.csv' # dataset di INPUT
OUTPUT_LIKES = 'likes.csv'
OUTPUT_DISLIKES = 'dislikes.csv'
OUTPUT_MATCHES = 'matches.csv'

random.seed(42) # Seed per riproducibilità

# Caricamento
print("Caricamento dataset...")
try:
    df = pd.read_csv(INPUT_FILE)

    # Rimuove l'admin se la colonna 'is_admin' esiste
    if 'is_admin' in df.columns:
        initial_count = len(df)
        # Filtra via chi ha is_admin == 'true' (case insensitive)
        df = df[df['is_admin'].astype(str).str.lower() != 'true']
        final_count = len(df)
        print(f"Filtrati {initial_count - final_count} utenti admin.")

    print(f"Utenti caricati: {len(df)}")
except FileNotFoundError:
    print(f"Errore: Il file {INPUT_FILE} non è stato trovato.")
    sys.exit()

# --- GENERAZIONE ATTRIBUTI SINTETICI ---

# A Activity Score (Gaussiana: Media 20, Dev 10, Min 0)
# Quanti swipe fa un utente?
df['swipes'] = np.random.normal(20, 10, len(df)).astype(int)
df['swipes'] = df['swipes'].clip(lower=0)

# B. Popularity Score (Gaussiana: Media 0.5, Dev 0.2)
# np.clip serve a tagliare i valori < 0.05 o > 0.95 (es. se esce 1.1 diventa 0.95)
df['popularity'] = np.clip(np.random.normal(0.5, 0.2, len(df)), 0.05, 0.95)

# Liste per salvare i risultati
likes_list = []
dislikes_list = []

# Set per lookup veloce (per la logica "chi mi ha messo like")
# Conterrà tuple: (source_id, target_id)
likes_lookup = set()

# Funzione Core: Logica di Compatibilità Sessuale
def is_sexually_compatible(user, candidate):
    u_sex, u_ori = user['sex'], user['orientation']
    c_sex, c_ori = candidate['sex'], candidate['orientation']
    
    # 1. Controlliamo chi cerca l'UTENTE (User -> Candidate)
    user_interested = False
    if u_ori == 'straight':
        user_interested = (u_sex != c_sex) # Cerca sesso opposto
    elif u_ori == 'gay':
        user_interested = (u_sex == c_sex) # Cerca stesso sesso
    elif u_ori == 'bisexual':
        user_interested = True # Cerca tutti
        
    if not user_interested: return False

    # 2. Controlliamo chi cerca il CANDIDATO (Candidate -> User)
    # L'app non mostra il profilo se l'altra persona non può essere interessata a te
    cand_interested = False
    if c_ori == 'straight':
        cand_interested = (c_sex != u_sex)
    elif c_ori == 'gay':
        cand_interested = (c_sex == u_sex)
    elif c_ori == 'bisexual':
        cand_interested = True
        
    return user_interested and cand_interested

# --- LOGICA DI RAGGRUPPAMENTO ---
# 1. Raggruppiamo per STATO (così abbiamo accesso a tutti i vicini se serve)
grouped_by_state = df.groupby('state')

print("Inizio generazione interazioni")
start_time = time.time()

# Contatore per monitorare il progresso
total_processed = 0

for state, state_group in grouped_by_state:
    
    # Trasformiamo tutto il gruppo stato in lista per velocità
    users_in_state = state_group.to_dict('records')
    
    # 2. Pre-calcoliamo i bucket per città dentro questo stato
    #    (Serve per recuperare velocemente gli utenti se la città è grande)
    city_buckets = {}
    for u in users_in_state:
        c = u.get('city', 'unknown_city')
        if c not in city_buckets:
            city_buckets[c] = []
        city_buckets[c].append(u)
    
    # Iteriamo su ogni utente dello stato
    for user in users_in_state:
        # Barra di avanzamento testuale
        total_processed += 1
        if total_processed % 1000 == 0:
            print(f"Processati {total_processed} utenti...")

        my_city = user.get('city', 'unknown_city')
        my_city_users = city_buckets.get(my_city, [])
        
        # --- LOGICA SIZE CITTA' ---
        # Se la città ha >= 100 utenti -> cerco solo nella mia città
        # Se la città ha < 100 utenti -> cerco in tutto lo stato
        if len(my_city_users) >= 100:
            candidate_pool = my_city_users
        else:
            candidate_pool = users_in_state
            
        # Sampling: Non posso scorrere 35k utenti. Prendo un campione dal pool scelto.
        sample_size = min(len(candidate_pool), 200) 
        candidates = random.sample(candidate_pool, sample_size)
        
        swipes_limit = user['swipes']
        swipes_count = 0
        
        for candidate in candidates: 
            # Skip se stesso
            if user['_id'] == candidate['_id']: continue

            # Stop se ha finito i swipe
            if swipes_count >= swipes_limit: break
            
            # --- FILTRO 1: COMPATIBILITÀ SESSUALE ---
            if not is_sexually_compatible(user, candidate):
                continue # Il profilo non viene nemmeno mostrato -> Niente swipe
            
            ## --- FILTRO 2: SWIPE (LIKE o DISLIKE?) ---
            # La probabilità di Like dipende dalla popolarità del candidato
            # Esempio: Popolarità 0.8 -> 40% chance di Like (0.8 * 0.5)
            # Abbiamo messo un moltiplicatore 0.5 perché i Like sono rari
            prob_like = candidate['popularity'] * 0.5

            # BOOST INTERESSI 
            # Gestione stringhe e pulizia
            u_str = str(user.get('interests', ''))
            c_str = str(candidate.get('interests', ''))
            # Rimuoviamo caratteri indesiderati se il CSV li ha salvati male (es. parentesi quadre o apici)
            # Esempio: "['music', 'sport']" diventa "music, sport"
            u_str = u_str.replace('[','').replace(']','').replace("'", "")
            c_str = c_str.replace('[','').replace(']','').replace("'", "")
            # Creazione Set puliti (strip toglie spazi, lower uniforma minuscolo)
            u_set = set(x.strip().lower() for x in u_str.split(',') if x.strip())
            c_set = set(x.strip().lower() for x in c_str.split(',') if x.strip())
            # Calcolo intersezione
            common_interests_count = len(u_set & c_set)
            if common_interests_count > 0:
                # +0.05 per OGNI interesse in comune
                boost = common_interests_count * 0.05
                prob_like += boost
            
            # BOOST Geo-Spatial
            # Se sto cercando nello stato (perché la mia città è piccola), 
            # do un piccolo bonus se trovo qualcuno PROPRIO della mia città piccola.
            if user['city'] == candidate['city']:
                prob_like += 0.1 

            # Se il candidato mi ha GIA' messo like in precedenza, 
            # aumento la probabilità che io ricambi il like.
            # Cerco la coppia (Candidato -> Utente) nel set dei like esistenti
            if (candidate['_id'], user['_id']) in likes_lookup:
                prob_like += 0.2

            # Controllo Soglia Massima (Cap a 0.9)
            if prob_like > 0.9:
                prob_like = 0.9

            roll = random.random()
            
            if roll < prob_like:
                # Registro il like nella lista per il CSV
                likes_list.append({
                    'source_id': user['_id'], 'target_id': candidate['_id']
                })
                # Aggiungo al set per la lookup veloce futura
                likes_lookup.add((user['_id'], candidate['_id']))
            else:
                dislikes_list.append({
                    'source_id': user['_id'], 'target_id': candidate['_id']
                })
            
            swipes_count += 1

# --- SALVATAGGIO ---
likes_df = pd.DataFrame(likes_list)
dislikes_df = pd.DataFrame(dislikes_list)

# Calcolo Matches
print("Calcolo Matches...")
matches_df = pd.DataFrame() # Inizializzazione sicura
if not likes_df.empty:
    # 1. Trova Match Reciproci (crea righe doppie: A-B e B-A)
    matches_df = likes_df.merge(
        likes_df,
        left_on=['source_id', 'target_id'],
        right_on=['target_id', 'source_id'],
        suffixes=('_sent', '_received')
    )
    matches_df = matches_df[['source_id_sent', 'target_id_sent']]
    matches_df.columns = ['source_id', 'target_id']

    # 2. DEDUPLICAZIONE: Tieni solo una riga per coppia
    # Mantiene la riga solo se l'ID sinistra è "minore" dell'ID destra (alfabeticamente)
    if not matches_df.empty:
        initial_matches = len(matches_df)
        matches_df = matches_df[matches_df['source_id'] < matches_df['target_id']]


print(f"Generati: {len(likes_df)} Likes, {len(dislikes_df)} Dislikes, {len(matches_df)} Matches Unici.")

# Export finale su CSV
print("Salvataggio file CSV in corso...")
likes_df.to_csv(OUTPUT_LIKES, index=False)
dislikes_df.to_csv(OUTPUT_DISLIKES, index=False)
matches_df.to_csv(OUTPUT_MATCHES, index=False)

print(f"Finito! Tempo totale: {round(time.time() - start_time, 2)} secondi.")