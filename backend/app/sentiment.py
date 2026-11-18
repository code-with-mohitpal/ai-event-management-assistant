"""TF-IDF + logistic regression sentiment classifier, NMF topics, lexicon complaints."""
import json, random, re
from pathlib import Path
import joblib
from sklearn.decomposition import NMF
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

MODEL_DIR = Path(__file__).resolve().parent.parent / "models"
MODEL_PATH, METRICS_PATH = MODEL_DIR / "sentiment.joblib", MODEL_DIR / "metrics.json"
VERSION = "tfidf-lr-1.0"

ASPECTS = ["speaker", "venue", "timing", "food", "content", "organisation", "sound system", "registration process"]
POS = ["The {a} was excellent and very well handled.", "I really enjoyed the {a}, it was great.", "Loved the {a}, truly outstanding work.",
       "The {a} was amazing and exceeded my expectations.", "Fantastic {a}, very helpful and engaging.", "Great {a}, I would recommend this event to everyone."]
NEG = ["The {a} was terrible and very disappointing.", "I did not like the {a}, it was poor.", "The {a} was bad and badly managed.",
       "Very disappointed with the {a}, it needs serious improvement.", "The {a} was awful and a waste of time.", "Poor {a}, I would not attend again."]
NEU = ["The {a} was okay, nothing special.", "The {a} was average and acceptable.", "The {a} was fine, neither good nor bad.",
       "I found the {a} ordinary and as expected.", "The {a} was decent, just normal.", "The {a} was moderate, about what I expected."]

def synth(n=620, seed=7):
    rnd = random.Random(seed); rows = []
    for i in range(n):
        lab = ["Positive", "Negative", "Neutral"][i % 3]
        t = rnd.choice({"Positive": POS, "Negative": NEG, "Neutral": NEU}[lab]).format(a=rnd.choice(ASPECTS))
        if rnd.random() < .3: t += " " + rnd.choice(["Overall a good day.", "Thanks to the team.", "Will see next time.", "That is my view."])
        rows.append((t, lab))
    return rows

def train_and_evaluate(rows):
    X = [r[0] for r in rows]; y = [r[1] for r in rows]
    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, stratify=y, random_state=42)
    model = Pipeline([("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=2, sublinear_tf=True, stop_words="english")),
                      ("clf", LogisticRegression(max_iter=1000, class_weight="balanced"))])
    model.fit(X_tr, y_tr); pred = model.predict(X_te)
    labels = ["Positive", "Neutral", "Negative"]
    m = {"accuracy": accuracy_score(y_te, pred), "report": classification_report(y_te, pred, output_dict=True, labels=labels, zero_division=0),
         "confusion": confusion_matrix(y_te, pred, labels=labels).tolist(), "labels": labels,
         "train_size": len(X_tr), "test_size": len(X_te), "dataset": "synthetic template-generated sentences", "version": VERSION}
    MODEL_DIR.mkdir(exist_ok=True); joblib.dump(model, MODEL_PATH); METRICS_PATH.write_text(json.dumps(m, indent=2))
    return m

def get_model():
    if not MODEL_PATH.exists(): train_and_evaluate(synth())
    return joblib.load(MODEL_PATH)

def metrics():
    if not METRICS_PATH.exists(): get_model()
    return json.loads(METRICS_PATH.read_text())

TOPIC_LEX = {"Speaker": ["speaker", "talk", "session", "presenter", "trainer"], "Venue": ["venue", "hall", "seat", "room", "auditorium", "ac"],
             "Timing": ["time", "timing", "late", "delay", "long", "schedule", "start"], "Food": ["food", "lunch", "snacks", "refreshment", "tea"],
             "Content": ["content", "topic", "workshop", "material", "demo"], "Organisation": ["organisation", "organization", "management", "volunteer", "coordination"],
             "Sound": ["sound", "mic", "audio", "microphone"], "Registration": ["registration", "queue", "entry", "check-in"]}
NEG_WORDS = ["bad", "poor", "terrible", "late", "delay", "delayed", "crowded", "disappointing", "awful", "boring", "noisy", "slow", "waste", "not", "no ", "worst", "long", "hot", "cold", "mismanaged"]

def topics_for(text):
    t = text.lower()
    return [k for k, ws in TOPIC_LEX.items() if any(re.search(r"\b" + re.escape(w.strip()) + r"\b", t) for w in ws)]

def analyse_one(text):
    model = get_model(); text = (text or "").strip()
    if not text: return {"sentiment": "Neutral", "confidence": 0.0, "topics": [], "complaints": []}
    proba = model.predict_proba([text])[0]; i = proba.argmax(); lab = model.classes_[i]
    tops = topics_for(text); comp = []
    if lab == "Negative" or any(w in text.lower() for w in NEG_WORDS[:12]): comp = tops or ["General"]
    return {"sentiment": str(lab), "confidence": round(float(proba[i]), 3), "topics": tops, "complaints": comp if lab == "Negative" else []}

def nmf_topics(texts, k=3):
    texts = [t for t in texts if t and len(t.split()) > 2]
    if len(texts) < 6: return []
    v = TfidfVectorizer(stop_words="english", min_df=2, max_df=.9); X = v.fit_transform(texts)
    if X.shape[1] < k: return []
    nmf = NMF(n_components=k, init="nndsvd", random_state=42, max_iter=300).fit(X); f = v.get_feature_names_out()
    return [[f[j] for j in c.argsort()[-4:][::-1]] for c in nmf.components_]

if __name__ == "__main__":
    m = train_and_evaluate(synth()); print(json.dumps({k: m[k] for k in ("accuracy", "train_size", "test_size", "confusion")}, indent=1))
