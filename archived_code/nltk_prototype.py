#!/usr/bin/env python
# coding: utf-8

# In[52]:


import nltk, pymongo, re
# REFERENCES
# https://www.nltk.org/book/ch07.html


# In[53]:


client = pymongo.MongoClient()


# In[54]:


# Read in pymongo entries
# Produce a cleaned noun phrase matrix
# Noun sources: 
# 1. annotated nouns in double brackets that are already present in the page data
# 1. NLP-extracted noun phrases 


# In[55]:


def grab_first_n_entries(n=1):
    return client['prod']['languages'].find()


# In[56]:


# Pull all the bracketed nouns out of the wikipedia entry using a regex
bracketed_nouns = """\\[\\[.*?\\]\\]"""
noun_matcher = re.compile(bracketed_nouns)


cursor = grab_first_n_entries()


# In[59]:


sentence = next(cursor)['value']


# In[64]:


sentence
noun_phrases = re.compile(bracketed_nouns)

noun_phrases.findall(sentence)


# In[68]:


re.subn(noun_matcher, "", sentence)


# In[ ]:




