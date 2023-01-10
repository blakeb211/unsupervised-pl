#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
* EDA - experiment 1 - connection graph and heatmap of bracketed nouns
"""

from sklearn.feature_extraction.text import TfidfTransformer
from scipy.spatial.distance import cdist
import os
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import networkx as nx
import re
from pprint import pprint as pp
import seaborn as sns
from wrappers.storage_wrapper import StorageWrapper

def create_test_data():
    """ Return test data to test the pipeline """
    return pd.DataFrame([[0, 1, 1, 0], [1, 0, 0, 1], [1, 0, 1, 1], [1, 1, 0, 0]], columns=(
        "The", "Ball", "Player", "Wife"), index=("The Ball Player", "The Wife", "Player Wife", "The Ball"))


def make_frame(USE_TEST_DATA=False):
    """ Reads in cached data from the ingestion script.
    Creates dataframe of word and noun features with
    programming languages as rows."""
    X = pd.DataFrame()

    if USE_TEST_DATA == True:
        X = create_test_data()
    else:
        # Pull all the bracketed nouns out of the wikipedia entry using a regex
        bracketed_nouns = """\\[\\[.*?\\]\\]"""
        noun_matcher = re.compile(bracketed_nouns)

        wrapper = StorageWrapper("prod")
        wrapper.open_or_create("languages")

        total_noun_set = set()
        for pl in wrapper.keys():
            text, date = wrapper.find(pl)
            nouns = noun_matcher.findall(text)
            nouns = [n.lower().strip() for n in nouns]
            total_noun_set.update(nouns)

        X = pd.DataFrame(columns=list(total_noun_set))
        # Name the columns so that there is one for each noun

        for pl in wrapper.keys():
            text, date = wrapper.find(pl)
            nouns = noun_matcher.findall(text)
            nouns = [n.lower() for n in nouns]
            # Create blank row
            curr_row = np.zeros(shape=len(total_noun_set), dtype=np.float16)
            # Build count matrix
            for idx, n in enumerate(X.columns.to_list()):
                if n in nouns:
                    curr_row[idx] += 1.0
            X.loc[pl, :] = curr_row
    return X


def remove_low_variance(X: pd.DataFrame):
    """ Remove low variance nouns, e.g. all 1 or all 0 """
    # does nothing right now intentionally
    return X


def create_most_frequent_bar_graph(stats: dict):
    top_nouns = list(stats['sorted_noun_freq'].keys())[0:50]
    top_values = list(stats['sorted_noun_freq'].values())[0:50]

    plt.barh(y=top_nouns, width=top_values)
    plt.xlabel(f"Occurence out of {len(X)} total documents")
    plt.show()


def convert_count_matrix_to_tfid(X: pd.DataFrame):
    old_index = list(X.index)
    X = TfidfTransformer().fit_transform(X).todense()
    X = pd.DataFrame(X, index=old_index)
    return X


def create_dist_matrix(X, metric='cityblock'):
    """ Create a distance matrix for X """
    X = X.convert_dtypes().astype(float)
    lang_names = np.char.title(X.index.tolist())
    print(f"lang names sorted:{sorted(lang_names)}")
    dist_mat = pd.DataFrame(cdist(X, X, metric=metric),
                            columns=lang_names, index=lang_names)
    assert len(dist_mat.index) == len(dist_mat.columns)
    return dist_mat


def return_sorted_most_freq(X: pd.DataFrame):
    """ Created sorted count dictionary from count matrix
     (features as cols, instances as rows) """
    sorted_noun_freq = sorted(
        X.sum().to_dict().items(), key=lambda item: item[1], reverse=True)
    return dict(sorted_noun_freq)


def plot_distance_matrix(dist_mat: pd.DataFrame):
    """ Create networkx undirected graph """
    assert dist_mat.shape[0] == dist_mat.shape[1]
    # CONFIGURABLE PARAMS START
    DISTANCE_THRESHOLD = 35
    FONT_SIZE = 15 
    # CONFIGURABLE PARAMS END
    X_row_labels = list(dist_mat.index)
    dist_mat = dist_mat.to_numpy()

    # Save number of rows in distance matrix
    n = len(dist_mat)
    G = nx.Graph()
    G.add_nodes_from(range(n))
    # Create the edge list, skipping edges longer than a threshold
    for i in range(n):
        for j in range(i + 1, n):
            wgt = dist_mat[i][j]
            if wgt > DISTANCE_THRESHOLD:
                continue
            else:
                G.add_edge(i, j, weight=wgt)

    # Let networkx decide node positions
    pos = nx.spring_layout(G, iterations=5000, seed=42)
    # Grab edge weights fr/om the distance matrix
    weights = [G[u][v]['weight'] for u, v in G.edges()]

    # Scale the weights to 0--1
    weights = np.asarray(weights)
    weight_min = weights.min()
    weights = (weights - weight_min)
    weight_max = weights.max()
    weights = weights / weights.max()
    # weights are now 0 to 1
    print(f"minmaxed weights, min = {weights.min()}, {weights.max()}")

    # Make weights inversely proportional to distance
    def inverse_range_faster_than_linear(x):
        """ Convert range from """
        return 15 - 14 * x + 5 * x**2 - 5
    assert np.isclose(inverse_range_faster_than_linear(0), 10, atol=0.1)
    assert np.isclose(inverse_range_faster_than_linear(1), 1, atol=0.1)

    weights = inverse_range_faster_than_linear(weights)
    print(f"inverted weights, min = {weights.min()}, {weights.max()}")
    # Remove thin weights (only slightly related) to make the graph
    # lines easier to see. If False, draw all edges
    if False:
        for idx, w in enumerate(weights):
            if w < 7:
                weights[idx] = 0

    # Draw the figure
    plt.figure(figsize=(11, 7))
    nx.draw_networkx_nodes(G, pos)
    # Draw the edges
    colors = ['#FFA07A'] * len(G.edges())
    nx.draw_networkx_edges(G, pos, edgelist=G.edges(),
                           style='-', alpha=0.4, width=weights, edge_color=colors)
    # Draw the edge labels
    labels = {(u, v): f"{w:.1f}" for u, v, w in G.edges(data='weight')}
    # nx.draw_networkx_edge_labels(G, pos, edge_labels=labels,alpha=0.7,font_size=FONT_SIZE)
    # Draw the node labels
    node_labels = {idx: X_row_labels[idx] for idx in G.nodes()}
    nx.draw_networkx_labels(
        G, pos=pos, labels=node_labels, font_size=FONT_SIZE + 3)
    plt.savefig("./figures/eda_graph.png")
    plt.close()
    plt.clf()
    plt.cla()


def plot_minimal_spanning_tree():
    # for a future iteration
    pass

if __name__ == "__main__":
    np.random.seed(42)
    X = make_frame()
    print(f"Dataframe shape {X.shape}")
    X = convert_count_matrix_to_tfid(X)
    print(f"TFIDF matrix shape {X.shape}")
    dist_mat = create_dist_matrix(X)

    print(dist_mat.index)
    print(dist_mat.columns)
    print(
        f"Dist matrix shape {dist_mat.shape}, type {type(dist_mat)}, max value {dist_mat.max().max():.2f} ")
    print(dist_mat.head(n=3))

    sns.heatmap(dist_mat)
    plt.savefig(f"./figures/eda_heatmap.png")
    plot_distance_matrix(dist_mat)
