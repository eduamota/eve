#!/usr/bin/python

from nltk.stem.snowball import SnowballStemmer
import string
from nltk.corpus import stopwords

def parseOutText(f):
    """ given an opened email file f, parse out all text below the
        metadata block at the top
        (in Part 2, you will also add stemming capabilities)
        and return a string that contains all the words
        in the email (space-separated) 
        
        example use case:
        f = open("email_file_name.txt", "r")
        text = parseOutText(f)
        
        """

    ### split off metadata
    #content = all_text.split("X-FileName:")
    content = f
    
    if len(content) > 0:
        ### remove punctuation
        text_string = content.translate({ord(c): None for c in string.punctuation})
        text_string = text_string.translate({ord(c): None for c in {"0","1","2","3","4","5","6","7","8","9"}})
        
        stemmer = SnowballStemmer("spanish")
        stop = set(stopwords.words('spanish'))
        ### project part 2: comment out the line below
        #words = text_string

        ### split the text string into individual words, stem each word,
        ### and append the stemmed word to words (make sure there's a single
        ### space between each stemmed word)
        #text_string = text_string.replace('\n',' ')
        text_array = text_string.split()
        text_result = ""
        for word in text_array:
            if len(word) > 0 and word not in stop:
                text_result = text_result + " " + stemmer.stem(word.lower())

        #print text_result


    return text_result.strip().replace('\n','')

    

def main():
    ff = open("../text_learning/test_email.txt", "r")
    text = parseOutText(ff)
    print text



if __name__ == '__main__':
    main()

