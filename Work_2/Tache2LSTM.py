# -*- coding: utf-8 -*-
"""LSTM.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1ci_GEtMfLaF2OKbUF4-uoxafoCz9RBVf
"""

#On charge nos données à partir du pc
from google.colab import files
uploaded=files.upload()

"""#1-La Création du jeu de données et des fonctions utilitaires"""

proverbs_fn = "proverbes.txt"
test1_fn = "test_proverbes.txt"

#On charge les données
import json
def load_proverbs(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        raw_lines = f.readlines()
    return [x.strip() for x in raw_lines]


def load_tests(filename):
    with open(filename, 'r') as fp:
        test_data = json.load(fp)
    return test_data

proverbs = load_proverbs(proverbs_fn)
print("\nNombre de proverbes pour entraîner les modèles : ", len(proverbs))
test_proverbs = load_tests(test1_fn)

from sklearn.model_selection import train_test_split
X_train, X_valid = train_test_split(proverbs, test_size=0.1, shuffle=True,random_state=42)

print("Nb exemples d'entraînement: {}, Nb d'exemples de validation: {}.".format(len(X_train), len(X_valid)))

!python3 -m spacy download en_core_web_md

#On débute pour ajouter les jetons de padding et mot inconnu

import spacy

nlp = spacy.load('en_core_web_md')
embedding_size = nlp.meta['vectors']['width']

import numpy as np

padding_token = "<PAD>"   # mot 0
unk_token = "<UNK>"    # mot 1
zero_vec_embedding = np.zeros(embedding_size, dtype=np.float64)

id2word = {}
id2word[0] = padding_token 
id2word[1] = unk_token 

word2id = {}
word2id[padding_token] = 0
word2id[unk_token] = 1

id2embedding = {}
id2embedding[0] = zero_vec_embedding
id2embedding[1] = zero_vec_embedding

word_index = 2
vocab = word2id.keys()
for proverb in X_train:
    for word in nlp(proverb):
        if word.text not in vocab:
            word2id[word.text] = word_index
            id2word[word_index] = word.text
            id2embedding[word_index] = word.vector
            word_index += 1



import torch

from torch import LongTensor
from torch.nn.utils.rnn import pad_sequence
from torch.utils.data import DataLoader, Dataset

class ProverbDataset(Dataset):
    def __init__(self, data , word_to_id, spacy_model):
        self.data = data
        self.sequences = [None for _ in range(len(data))]
        self.word2id = word_to_id
        self.tokenizer = spacy_model
    
    def __len__(self):
        return len(self.data)

    def __getitem__(self, index):
        if self.sequences[index] is None:
            self.sequences[index] = self.tokenize(self.data[index]) 
        return LongTensor(self.sequences[index])

    def tokenize(self, sentence):
        tokens = [word.text for word in self.tokenizer(sentence)]
        return [self.word2id.get(token, 1) for token in tokens]  # get(token, 1) retourne 1 par défaut si mot inconnu
    
train_dataset = ProverbDataset(X_train, word2id, nlp)
valid_dataset = ProverbDataset(X_valid, word2id, nlp)

valid_dataset[10]

import torch.nn as nn
from torch.nn.utils.rnn import pack_padded_sequence, pad_packed_sequence

class SimpleLSTMTagger(nn.Module):
    def __init__(self, embeddings, hidden_state_size, output_dim):
        super(SimpleLSTMTagger, self).__init__()
        self.embedding_layer = nn.Embedding.from_pretrained(embeddings)
        self.embedding_size = embeddings.size()[1] 
        self.lstm_layer = nn.LSTM(self.embedding_size, hidden_state_size, batch_first=True)  # Défini W et U
        self.fc = nn.Linear(hidden_state_size, output_dim)  # Correspond à V
        self.Softmax = nn.Softmax()
    
    def forward(self, x, h):
        x = self.embedding_layer(x)
        packed_batch = pack_padded_sequence(x, h, batch_first=True, enforce_sorted=False)
        out, h = self.lstm(x, h)
        out = self.fc(self.Softmax(out))   # V est appliqué à chacun des états cachés = étiquetage de tous les mots
        return out, h
    def init_hidden(self):
        # LSTM h and c
        weight = next(self.parameters()).data
        return weight.new_zeros(1,self.hidden_state_size), weight.new_zeros(1, self.hidden_state_size)



train_dataloader = DataLoader(train_dataset, batch_size=40, shuffle=False)
valid_dataloader = DataLoader(valid_dataset, batch_size=40, shuffle=False)

print("Ensemble de train: {} séquences de longueur {} et {} minibatches".format(len(train_dataset), 40, len(train_dataloader)))

#Maintenant on construit la table d'embeddings qui sera passée en argument au modèel lors de sa création.
vocab_size = len(id2embedding)
embedding_layer = np.zeros((vocab_size, embedding_size), dtype=np.float32)
for token_id, embedding in id2embedding.items():
    embedding_layer[token_id,:] = embedding
embedding_layer = torch.from_numpy(embedding_layer)

print("Taille de la couche d'embeddings:", embedding_layer.shape)

!pip install poutyne

import torch
START_VOCAB = ["_UNK"]
UNK_ID = 0
DEVICE = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

#Finalement on construit notre modèle de classification de questions.

from poutyne import set_seeds
output_dimension = 1
set_seeds(42)
hidden_size = 100  # choisi arbitrairement
model = SimpleLSTMTagger(embedding_layer, hidden_size, output_dimension)



experiment = Experiment("./", model, optimizer = "SGD",task='reg', loss_function=cross_entropy,
    batch_metrics=["acc"])
logging = experiment.train(train_dataloader, valid_dataloader, epochs=25,disable_tensorboard=True)

input_dimension = 4
hidden_dimension = 3

lstm_layer = nn.LSTM(input_size=input_dimension, hidden_size=hidden_dimension, batch_first=True)

hidden0 = torch.zeros(1, 1, 3)
context0 = torch.zeros(1, 1, 3)

#output, (hidden, context) = lstm_layer(inputs, (hidden0, context0))

lstm_layer











import contextlib
import gzip
import os
import pickle
import re
import shutil
import sys
import warnings
from io import TextIOBase
import requests
import torch
import torch.nn as nn
import torch.optim as optim
from poutyne import set_seeds
from poutyne.framework import Experiment
from torch.nn.functional import cross_entropy
from torch.nn.utils.rnn import pack_padded_sequence, pad_packed_sequence, pad_sequence
from torch.utils.data import DataLoader





from poutyne.framework import Experiment

experiment = Experiment("./", model, optimizer = "SGD", loss_function=cross_entropy,
    batch_metrics=["acc"])
logging = experiment.train(train_dataloader, valid_dataloader, epochs=25, disable_tensorboard=True)

dimension = 300
num_layer = 1
bidirectional = False

lstm_network = nn.LSTM(
    input_size=dimension,
    hidden_size=dimension,
    num_layers=num_layer,
    bidirectional=bidirectional,
    batch_first=True,
)

input_dim = dimension  # the output of the LSTM
tag_dimension = 8

fully_connected_network = nn.Linear(input_dim, tag_dimension)





input_dimension = 4
hidden_dimension = 3
output_dimension = 1
emb1 = [0.9, 0.8, 0.7 , 0.6]
emb2 = [0.1, 0.2, 0.3 , 0.4]
sequencer = [[emb1, emb2]]
inputs = torch.FloatTensor(sequencer)
hidden0 = torch.zeros(1, 1, 3)
context0 = torch.zeros(1, 1, 3)
output_dimension = 1
pou = SimpleLSTMTagger(input_dimension, hidden_dimension, output_dimension)
#print(inputs)

pou

hidden0 = torch.zeros(1, 1, 3)
context0 = torch.zeros(1, 1, 3)

output, (hidden, context) = pou(inputs, (hidden0, context0))

output

(hidden, context)

lstm_layer = nn.LSTM(input_size=input_dimension, hidden_size=hidden_dimension, batch_first=True)

hidden0 = torch.zeros(1, 1, 3)
context0 = torch.zeros(1, 1, 3)

output, (hidden, context) = lstm_layer(inputs, (hidden0, context0))
