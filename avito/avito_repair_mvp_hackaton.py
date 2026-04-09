import ast
import re
import warnings

import hdbscan
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer
from sklearn.metrics import classification_report, confusion_matrix

warnings.filterwarnings("ignore")
pd.set_option("display.max_colwidth", 160)

DATA_PATH = "rnc_dataset.csv"


def clean_text(text: str) -> str:
    text = str(text).lower()
    text = text.replace("\n", " ")
    text = re.sub(r"[^а-яёa-z0-9 ]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def parse_list(x):
    try:
        value = ast.literal_eval(str(x))
        return value if isinstance(value, list) else []
    except Exception:
        return []


def choose_hdbscan_params(group_size: int) -> dict:
    min_cluster_size = max(8, min(40, int(round(group_size * 0.03))))
    min_samples = max(3, int(round(min_cluster_size * 0.4)))
    return {
        "min_cluster_size": min_cluster_size,
        "min_samples": min_samples,
        "metric": "euclidean",
        "cluster_selection_method": "eom",
    }


def cluster_one_group(group: pd.DataFrame, all_embeddings: np.ndarray) -> pd.DataFrame:
    group = group.copy()
    idx = group.index.to_numpy()
    group_size = len(group)

    if group_size < 25:
        group["cluster_label"] = -1
        group["n_clusters_found"] = 0
        group["noise_share"] = 1.0
        group["pred_shouldSplit"] = False
        return group

    params = choose_hdbscan_params(group_size)
    emb = all_embeddings[idx]

    clusterer = hdbscan.HDBSCAN(**params)
    labels = clusterer.fit_predict(emb)

    n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
    noise_share = float((labels == -1).mean())
    pred_should_split = (n_clusters >= 2) and (noise_share <= 0.55)

    group["cluster_label"] = labels
    group["n_clusters_found"] = n_clusters
    group["noise_share"] = noise_share
    group["pred_shouldSplit"] = pred_should_split
    return group


def main():
    df = pd.read_csv(DATA_PATH)
    df["text_clean"] = df["description"].apply(clean_text)
    df["targetDetectedMcIds_list"] = df["targetDetectedMcIds"].apply(parse_list)
    df["targetSplitMcIds_list"] = df["targetSplitMcIds"].apply(parse_list)

    embedder = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
    embeddings = embedder.encode(
        df["text_clean"].tolist(),
        show_progress_bar=True,
        normalize_embeddings=True
    )

    result = (
        df.groupby("sourceMcTitle", group_keys=False)
          .apply(lambda g: cluster_one_group(g, embeddings))
          .reset_index(drop=True)
    )

    print("Confusion matrix:")
    print(confusion_matrix(result["shouldSplit"], result["pred_shouldSplit"]))
    print()
    print(classification_report(result["shouldSplit"], result["pred_shouldSplit"], digits=3))

    result.to_csv("rnc_dataset_with_mvp_predictions.csv", index=False)
    print("\nSaved: rnc_dataset_with_mvp_predictions.csv")


if __name__ == "__main__":
    main()
