import pandas as pd
import random
import os
import sys
import csv
from datetime import datetime, timedelta

# --- CONFIGURAZIONE ---
INPUT_MATCHES = 'matches.csv'
OUTPUT_REVIEWS = 'reviews.csv'

# --- POOL DI RECENSIONI (Testi estratti da generate_artifacts.py) ---
review_pools = {
    5: [
        "The algorithm absolutely nailed this one! We have so much in common.",
        "Spot on recommendation. I wouldn't have found this connection on my own.",
        "Incredible accuracy. It feels like this match was hand-picked for me.",
        "10/10 matchmaking. We just clicked instantly.",
        "Finally, a match that actually makes sense! Great job.",
        "The compatibility score must be off the charts. Perfect match.",
        "I was skeptical about the algorithm, but this match proved me wrong.",
        "This is exactly the kind of person I was hoping to match with.",
        "A flawless suggestion. We hit it off immediately.",
        "The system really understood my preferences this time.",
        "Match of the year! The algorithm did its magic.",
        "Perfect alignment of interests and vibe. Great recommendation.",
        "I'm impressed by the algorithm's accuracy. A truly great match.",
        "This match exceeded all my expectations. Well done, algorithm!",
        "Ideally matched. It feels like the system knows me better than I know myself."
    ],
    4: [
        "Solid recommendation. We get along well, even if it's not perfect yet.",
        "The system understood my preferences pretty well. Good potential here.",
        "A surprisingly good match. Not 100% my type usually, but it worked.",
        "Good job on this one. We have a lot of compatible interests.",
        "Accurate matching. We had a great time.",
        "A strong match. The algorithm is definitely learning.",
        "We are quite compatible. A good suggestion overall.",
        "Nice work by the matching engine. We have good chemistry.",
        "The algorithm found someone who complements me well.",
        "Almost a perfect match. Very happy with this suggestion.",
        "Good filtering. This person was very much up my alley.",
        "A well-calculated match. We had a pleasant conversation.",
        "The predictive matching was pretty accurate here.",
        "Worth the match. We share a solid foundation.",
        "Deserves a high score. The algorithm did a good job connecting us."
    ],
    3: [
        "The algorithm kind of got it right, but the chemistry wasn't fully there.",
        "Technically a match on paper, but in reality, it was just okay.",
        "I see why we were matched, but the spark was missing.",
        "Not a bad suggestion, but not a great one either.",
        "Average match. We share interests, but that's about it.",
        "The algorithm tried, but we didn't quite click.",
        "A logical match based on data, but the vibe was neutral.",
        "The system matched us on hobbies, but personality-wise it was a miss.",
        "A fair attempt by the algorithm, but nothing special.",
        "Middle of the road. The match wasn't wrong, just not exciting.",
        "We have similar stats, but zero chemistry. Algorithm needs fine-tuning.",
        "Okay match, maybe for a friend, but not romance.",
        "The matching criteria seemed generic on this one.",
        "Not a total fail, but I wouldn't call it a success either.",
        "The algorithm found a match, just not 'the' match."
    ],
    2: [
        "I don't think the algorithm understood what I'm looking for.",
        "Not sure why we were matched. We are very different people.",
        "This recommendation felt pretty random. Not a fan.",
        "The compatibility score must have been off. It didn't work.",
        "Poor matching. We barely had anything to talk about.",
        "Algorithm failure. We have nothing in common.",
        "Why did the system think we would match? Very confusing.",
        "Bad suggestion. The parameters must be wrong.",
        "I expected better matching. This was a letdown.",
        "The algorithm missed the mark completely on personality.",
        "Not compatible. The system needs to learn better.",
        "A weak match. Felt like a random pick.",
        "Please improve the matching logic. This was a waste.",
        "Incorrect profiling. We shouldn't have been matched.",
        "The algorithm is hallucinating if it thinks we are a match."
    ],
    1: [
        "Completely wrong match. Did the algorithm even read my profile?",
        "Terrible recommendation. Zero compatibility.",
        "This match makes no sense. Total waste of time.",
        "Please stop sending matches like this. It's the opposite of what I want.",
        "The algorithm failed hard on this one. Disappointing.",
        "Broken matchmaking. We are polar opposites.",
        "Worst suggestion ever. Fix the algorithm.",
        "I question the logic behind this match. 1/10.",
        "Absolute mismatch. The system is broken.",
        "Did you match us by accident? Horrible.",
        "The algorithm needs a serious update. This was awful.",
        "Zero relevance. Why was this suggested?",
        "A complete failure of the matching engine.",
        "I'm unsubscribing if the matches continue to be this bad.",
        "Algorithmic disaster. Avoid."
    ]
}

# Funzione per generare date realistiche (ultimi 2 anni)
def random_date(start_year=2023, end_year=2025):
    """Genera una data casuale ISO format nel range specificato."""
    start = datetime(start_year, 1, 1)
    end = datetime(end_year, 12, 31)
    delta = end - start
    random_days = random.randrange(delta.days)
    random_seconds = random.randrange(86400)
    dt = start + timedelta(days=random_days, seconds=random_seconds)
    return dt.isoformat()


def generate_reviews():
    print("--- Generazione Recensioni ---")
    
    # 1. Verifica input
    if not os.path.exists(INPUT_MATCHES):
        print(f"ERRORE: Il file {INPUT_MATCHES} non è stato trovato.")
        sys.exit(1)

    matches_df = pd.read_csv(INPUT_MATCHES)
    print(f"Caricati {len(matches_df)} match da elaborare.")

    generated_reviews = []
    
    # Parametri  
    # Definiscono la probabilità che A recensisca B, B recensisca A, o entrambi
    THRESH_NONE = 0.30      # 30% probabilità nessuna review
    THRESH_A_TO_B = 0.50    # 20% probabilità solo A->B (0.50 - 0.30)
    THRESH_B_TO_A = 0.70    # 20% probabilità solo B->A (0.70 - 0.50)
    # Il restante 30% è recensione bidirezionale (Both)

    # Pesi per lo score (1 a 5)
    score_weights = [0.05, 0.10, 0.30, 0.35, 0.20]

    random.seed(42) # Seed per riproducibilità

    # 2. Iterazione sui match
    for _, row in matches_df.iterrows():
        # Assicuriamoci che gli ID siano stringhe
        user_a = str(row['source_id'])
        user_b = str(row['target_id'])

        r = random.random()
        
        # Helper interno per creare l'oggetto review
        def create_entry(reviewer, target):
            rating = random.choices([1, 2, 3, 4, 5], weights=score_weights, k=1)[0]
            desc = random.choice(review_pools[rating])
            return {
                "reviewer_id": reviewer,
                "target_id": target,
                "rating": rating,
                "comment": desc,
                "review_date": random_date()
            }

        if r < THRESH_NONE:
            continue
        elif r < THRESH_A_TO_B:
            generated_reviews.append(create_entry(user_a, user_b))
        elif r < THRESH_B_TO_A:
            generated_reviews.append(create_entry(user_b, user_a))
        else:
            # Bidirezionale
            generated_reviews.append(create_entry(user_a, user_b))
            generated_reviews.append(create_entry(user_b, user_a))

    # 3. Creazione DataFrame e salvataggio
    reviews_df = pd.DataFrame(generated_reviews)
    
    # Colonne
    final_columns = ['reviewer_id', 'target_id', 'rating', 'comment', 'review_date']
    
    if not reviews_df.empty:
        reviews_df = reviews_df[final_columns]
        reviews_df.to_csv(OUTPUT_REVIEWS, index=False, quoting=csv.QUOTE_NONNUMERIC)        
        print(f"File '{OUTPUT_REVIEWS}' generato con successo.")
        print(f"Totale recensioni create: {len(reviews_df)}")
    else:
        print("Nessuna recensione generata (probabile dataset vuoto o threshold alti).")

if __name__ == "__main__":
    generate_reviews()