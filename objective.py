import re
import nltk
import numpy as np
from nltk.corpus import wordnet as wn


class ObjectiveTest:

    def __init__(self, filepath, noOfQues):
        self.summary = filepath
        self.noOfQues = noOfQues

    def get_trivial_sentences(self):
        """Tokenize text into sentences and extract trivial ones."""
        sentences = nltk.sent_tokenize(self.summary)
        trivial_sentences = []
        for sent in sentences:
            trivial = self.identify_trivial_sentences(sent)
            if trivial:
                trivial_sentences.append(trivial)
        return trivial_sentences

    def identify_trivial_sentences(self, sentence):
        """Identify trivial sentences and generate question-answer pairs."""
        tokens = nltk.word_tokenize(sentence)
        if not tokens or len(tokens) < 4:
            return None

        tags = nltk.pos_tag(tokens)
        if tags[0][1] == "RB":  # Ignore adverb-starting sentences
            return None

        noun_phrases = []
        grammar = r"""
            CHUNK: {<NN>+<IN|DT>*<NN>+}
                   {<NN>+<IN|DT>*<NNP>+}
                   {<NNP>+<NNS>*}
        """
        chunker = nltk.RegexpParser(grammar)
        tree = chunker.parse(tags)

        for subtree in tree.subtrees():
            if subtree.label() == "CHUNK":
                phrase = " ".join(word for word, pos in subtree)
                noun_phrases.append(phrase.strip())

        replace_nouns = []
        for word, _ in tags:
            for phrase in noun_phrases:
                if phrase.startswith("'"):
                    break
                if word in phrase:
                    replace_nouns.extend(phrase.split()[-2:])
                    break
            if not replace_nouns:
                replace_nouns.append(word)
            break

        if not replace_nouns:
            return None

        val = min(len(i) for i in replace_nouns)
        trivial = {"Answer": " ".join(replace_nouns), "Key": val}

        # Generate similar word options
        if len(replace_nouns) == 1:
            trivial["Similar"] = self.answer_options(replace_nouns[0])
        else:
            trivial["Similar"] = []

        replace_phrase = " ".join(replace_nouns)
        blanks_phrase = ("__________ " * len(replace_nouns)).strip()
        expression = re.compile(re.escape(replace_phrase), re.IGNORECASE)
        sentence = expression.sub(blanks_phrase, str(sentence), count=1)
        trivial["Question"] = sentence

        return trivial

    @staticmethod
    def answer_options(word):
        """Generate similar words using WordNet."""
        synsets = wn.synsets(word, pos="n")
        if not synsets:
            return []

        synset = synsets[0]
        hypernyms = synset.hypernyms()
        if not hypernyms:
            return []

        hypernym = hypernyms[0]
        hyponyms = hypernym.hyponyms()
        similar_words = []

        for hyponym in hyponyms:
            similar_word = hyponym.lemmas()[0].name().replace("_", " ")
            if similar_word != word:
                similar_words.append(similar_word)
            if len(similar_words) >= 8:
                break
        return similar_words

    def generate_test(self):
        """Generate question-answer pairs for the objective test."""
        trivial_pair = self.get_trivial_sentences()
        question_answer = [
            qa for qa in trivial_pair if qa["Key"] > int(self.noOfQues)
        ]

        question = []
        answer = []
        while len(question) < int(self.noOfQues) and question_answer:
            rand_num = np.random.randint(0, len(question_answer))
            qa_item = question_answer[rand_num]
            if qa_item["Question"] not in question:
                question.append(qa_item["Question"])
                answer.append(qa_item["Answer"])
        return question, answer
