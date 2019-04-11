import nltk
from . import pos_tagger, ner, utils, gender_number, tokenizer
import sys
import os
import re
import functools
__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))

class Token:
    value = None
    pos_tag = None
    ne_tag = None

    def __init__(self, value, pos_tag, ne_tag):
        self.value = value
        self.pos_tag = pos_tag
        self.ne_tag = ne_tag

    def __str__(self):
        return self.value

    def __eq__(self, obj):
        return str(self) == str(obj)

    def isPronoun(self):
        return self.pos_tag[:3] == "PRP"


class Mention:
    id = 0

    def __init__(
        self, tokens, sentence_position, start_position, end_position, ne=None, dummy=False
    ):

        self.number = []
        self.gender = []
        self.nested = []
        self.animate = []
        self.parent = None
        self.ne = None
        self.speaker = None

        self.self_id = Mention.id
        self.entity_id = Mention.id
        self.tokens = tokens
        self.sentence_position = sentence_position
        self.start_position = start_position
        self.end_position = end_position
        if ne:
            self.ne = ne

        if not dummy:
            Mention.id += 1

    def position(self):
        return (self.sentence_position, self.start_position, self.end_position)

    @classmethod
    def mention_from_object(Mention, mention):
        new_mention = Mention(mention.tokens, mention.sentence_position, mention.start_position, mention.end_position, ne=mention.ne)
        new_mention.parent = mention.parent
        new_mention.nested = mention.nested
        for obj in new_mention.nested:
            obj.parent = new_mention
        del mention
        return new_mention

    @classmethod
    def check_i_in_i(Mention, mention1, mention2):
        return ((mention1.parent is not None and mention1.parent==mention2) or (mention2.parent is not None and mention2.parent==mention1))

    @classmethod
    def textual_order(Mention, obj1, obj2):
        return -1 if obj1.position()<=obj2.position() else 1

    def __str__(self):
        return utils.join(self.tokens)

    def summary(self):
        return [
            str(self),
            (self.entity_id, self.self_id),
            (self.sentence_position, self.start_position, self.end_position),
            self.ne,
            self.gender,
            self.number,
            self.animate,
        ]

    def info(self, short=False):
        if len(self.nested) == 0 or short:
            return "[" + str(self) + "]" + str((self.entity_id, self.self_id))

        last = 0
        cur = "["
        for mention in sorted(self.nested, key=functools.cmp_to_key(Mention.textual_order)):
            if mention == self:
                continue
            start = mention.start_position - self.start_position
            end = mention.end_position - self.start_position
            if start > last:
                if cur == "[":
                    cur += utils.join(self.tokens[last:start])
                else:
                    cur += " " + utils.join(self.tokens[last:start])
            if cur == "[":
                cur += mention.info()
            else:
                cur += " " + mention.info()

            last = end + 1

        if last < len(self.tokens):
            cur += " " + utils.join(self.tokens[last:])

        cur += "]" + str((self.entity_id, self.self_id))

        return cur

    def __lt__(self, obj):
        return self.self_id < obj.self_id

    def __gt__(self, obj):
        return self.self_id > obj.self_id

    def __le__(self, obj):
        return self.__lt__() or self.__eq__()

    def __ge__(self, obj):
        return self.__gt__() or self.__eq__()

    def __eq__(self, obj):
        return self.self_id == obj.self_id

    def lower(self):
        return str(self).lower()

    def merge(self, obj):
        obj.entity_id = self.entity_id

    def isPronoun(self):
        return len(self.tokens) == 1 and self.tokens[0].isPronoun()

    def isQuote(self):
        return str(self.tokens[0]) == '"' and str(self.tokens[-1]) == '"'

    def modifiers(self):
        state=-1
        cur = []
        for token in self.tokens:
            if token.pos_tag[:2]=="JJ":
                if state<=1:
                    cur.append(token)
                state = 1
            elif state==1:
                break
        return cur

    def head_words(self):
        if self.isPronoun():
            return self.tokens

        state=-1
        cur = []
        for token in self.tokens:
            if token.pos_tag[:2]=="NN":
                if state<=1:
                    cur.append(token)
                state = 1
            elif state==1:
                break
        return cur

class CoreferenceResolution:

    sentences = None
    processed_sentences = []
    mentions = []

    def __init__(self, sentences=None):
        Mention.id = 0
        self.processed_sentences = []
        self.mentions = []
        if sentences:
            self.sentences = sentences

    def pre_process(self, word_tokenized=False):
        tokenized_sentences = nltk.sent_tokenize(self.sentences)
        for sentence in tokenized_sentences:
            if not word_tokenized:
                tokenized_sentence = tokenizer.tokenize(sentence)
            else:
                tokenized_sentence = sentence.split(" ")
            pos_tagged_sentence = pos_tagger.pos_tag(tokenized_sentence)
            ne_tagged_sentence = ner.named_entities(tokenized_sentence)
            self.processed_sentences.append(
                [
                    Token(*token)
                    for token in zip(
                        tokenized_sentence, pos_tagged_sentence, ne_tagged_sentence
                    )
                ]
            )

    def assign_gender_number(self, mention):
        if mention.ne:
            gender, number = gender_number.get_gender_number(str(mention))
            if gender == "U":
                gender, number = gender_number.get_gender_number(
                    str(mention.tokens[0])
                )
            mention.gender.append(gender)
            if mention.ne == "PERSON":
                mention.animate.append(True)
            else:
                mention.animate.append(False)

            mention.number.append("S")

        elif mention.isPronoun():
            token = mention.tokens[0]

            gender, number = gender_number.get_gender_number(
                str(token), (token.pos_tag[:3] == "PRP")
            )

            mention.gender.append(gender)
            mention.number.append(number)

            if token.pos_tag[:3] == "PRP":
                mention.animate.append(True)
            else:
                mention.animate.append(False)

            #TODO: Remove hardcoding
            if str(token).lower()[:2] in ["it", "th"]:
                mention.animate.append(False)

        else:
            for token in mention.tokens:
                if token.pos_tag[:2] == "NN":
                    gender, number = gender_number.get_gender_number(str(token))
                    mention.gender.append(gender)
                    if "M" in mention.gender or "F" in mention.gender:
                        mention.animate.append(True)
                    else:
                        mention.animate.append(False)
                    if token.pos_tag[:3] == "NNP":
                        mention.animate.append(True)
                        if token.pos_tag == "NNP":
                            mention.number.append("S")
                        else:
                            mention.number.append("P")
                        break
                    elif token.pos_tag in ["NN", "NNS"]:
                        if token.pos_tag == "NN":
                            mention.number.append("S")
                        else:
                            mention.number.append("P")
                        
                    break

    def mention_detection(self):
        def extract_ne_pronoun(mention):

            def dt_correlation(m1, m2):
                return m1.tokens[0].pos_tag=="DT" and m1.tokens[1:]==m2

            start = 0
            cur = []
            nested = []
            cur_tag = ""
            for (i, token) in enumerate(mention.tokens):

                if token.isPronoun():
                    this_mention = Mention([token], mention.sentence_position, i, i)
                    nested.append(this_mention)

                ne_tag = token.ne_tag.split("-")
                if len(ne_tag) == 2:
                    if ne_tag[0] == "B":
                        if len(cur_tag) and len(cur) < len(mention.tokens) and not dt_correlation(mention, cur):
                            this_mention = Mention(
                                cur,
                                mention.sentence_position,
                                start,
                                start + len(cur) - 1,
                                cur_tag,
                            )
                            nested.append(this_mention)
                        elif len(cur_tag):
                            mention.ne = cur_tag
                        cur = []
                        start = i
                        cur_tag = ne_tag[1]
                    cur.append(token)

            if len(cur_tag) and len(cur) < len(mention.tokens) and not dt_correlation(mention, cur):
                this_mention = Mention(
                    cur, mention.sentence_position, start, start + len(cur) - 1, cur_tag
                )
                nested.append(this_mention)
            elif len(cur_tag):
                mention.ne = cur_tag

            mention.nested = []

            for this_mention in nested:
                this_mention.parent = mention
                this_mention.start_position += mention.start_position
                this_mention.end_position += mention.start_position
                self.assign_gender_number(this_mention)
                mention.nested.append(this_mention)
                self.mentions.append(this_mention)

            return mention

        def extract_noun_pronoun_phrases(i, tokens):
            state = -1
            cur = []
            start = -1
            prepositions = ["of", "for"]

            for (j, token) in enumerate(tokens):
                
                if state == -1 and token.pos_tag == "PDT":
                    state = 0
                    start = j
                    cur.append(token)
                elif (state <= 0 or state == 3) and (token.pos_tag[:2] == "DT")  or (state==2 and cur[-1].pos_tag == "CC"):
                    if state <= 0 and start<0:
                        start = j
                    state = 1
                    cur.append(token)
                elif (
                    (state <= 1 or state == 3)
                    and (
                        token.pos_tag[:2] == "JJ"
                        or token.pos_tag == "CD"
                        or token.pos_tag == "PRP$"
                    )
                ):
                    if state == -1:
                        start = j
                    if state <= 0:
                        state = 1
                    cur.append(token)
                elif state <= 4 and (
                    token.pos_tag[:2] == "NN"
                    or token.pos_tag == "SYM"
                    or (state==2 and token.pos_tag == "CC")
                    or (state==2 and token.pos_tag == "POS")
                ):
                    if state == -1:
                        start = j
                    state = 2
                    cur.append(token)
                elif state == 2 and token in prepositions:
                    state = 3
                    cur.append(token)
                else:
                    if state == 3:
                        cur = cur[:-1]
                        end = j - 2
                    else:
                        end = j - 1

                    if state == 2 or state == 4 and len(cur):
                        new_mention = extract_ne_pronoun(Mention(cur, i, start, end, dummy=True))
                        new_mention = Mention.mention_from_object(new_mention)
                        self.assign_gender_number(new_mention)
                        self.mentions.append(new_mention)

                    if token.pos_tag[:3] == "PRP":
                        new_mention = Mention([token], i, j, j)
                        self.assign_gender_number(new_mention)
                        self.mentions.append(new_mention)

                    cur = []
                    start = -1
                    state = -1

            if state == 2 or state == 4 and token.pos_tag[:2] == "NN":
                if len(cur):
                    new_mention = extract_ne_pronoun(
                        Mention(cur, i, start, start + len(cur) - 1, dummy=True)
                    )
                    new_mention = Mention.mention_from_object(new_mention)
                    self.assign_gender_number(new_mention)
                    self.mentions.append(new_mention)

            return None, "X", ""

        for (i, tokens) in enumerate(self.processed_sentences):
            extract_noun_pronoun_phrases(i, tokens)

    def speaker_identification(self):
        for j in range(0, len(self.mentions)):
            current_mention = self.mentions[j]
            if not current_mention.isPronoun():
                continue
            if current_mention.self_id != current_mention.entity_id:
                continue
            for i in range(j - 1, -1, -1):
                candidate = self.mentions[i]

                
                if Mention.check_i_in_i(current_mention, candidate) or not candidate.isPronoun():
                    continue

                if current_mention.speaker==candidate.speaker:
                    if "i" in utils.find_pronoun_group(current_mention.tokens[0]) and utils.check_pronoun_group(current_mention.tokens[0], candidate.tokens[0]):
                        candidate.merge(current_mention)


    def exact_string_match(self):
        for j in range(0, len(self.mentions) - 1):
            if self.mentions[j].isPronoun():
                continue

            for i in range(j - 1, -1, -1):
                if self.mentions[i].isPronoun():
                    continue

                if self.mentions[j].lower() == self.mentions[i].lower():
                    self.mentions[i].merge(self.mentions[j])
                    break

    def approx_string_match(self):
        def check_relative_clause(tokens):
            pass

        for j in range(0, len(self.mentions)):

            current_mention = self.mentions[j]

            if current_mention.isPronoun():
                continue

            if current_mention.self_id != current_mention.entity_id:
                continue

            cleaned_j = utils.join(utils.remove_stopwords(current_mention.tokens)).lower()

            for i in range(j - 1, -1, -1):


                candidate = self.mentions[i]

                if Mention.check_i_in_i(current_mention, candidate) or candidate.isPronoun():
                    continue

                cleaned_i = utils.join(
                    utils.remove_stopwords(candidate.tokens)
                ).lower()

                if cleaned_i == cleaned_j and len(cleaned_i) and len(cleaned_j):
                    candidate.merge(current_mention)
                    break

    def precise_constructs_match(self):
        def isAppositive(mention1, mention2):
            return (
                mention1.sentence_position == mention2.sentence_position
                and (mention2.start_position - mention1.end_position == 2)
                and (
                    mention1.ne is not None
                    or mention2.ne is not None
                    or mention1.tokens[0].pos_tag[:3] == "NNP"
                    or mention2.tokens[0].pos_tag[:3] == "NNP"
                )
                and (
                    mention1.tokens[0].pos_tag == "dt"
                    or mention2.tokens[0].pos_tag == "dt"
                )
                and str(
                    self.processed_sentences[mention1.sentence_position][
                        mention1.end_position + 1
                    ]
                )
                == ","
            )

        def isRoleAppositive(mention1, mention2):
            return (
                mention1.sentence_position == mention2.sentence_position
                and (mention2.start_position - mention1.end_position == 2)
                and (mention1.ne is not None or mention1.tokens[0].pos_tag[:3] == "NNP")
                and mention2.tokens[0].pos_tag == "DT"
                and str(
                    self.processed_sentences[mention1.sentence_position][
                        mention1.end_position + 1
                    ]
                )
                == ","
            )

        def check_nominative(mention1, mention2):
            mid = self.processed_sentences[mention1.sentence_position][
                mention1.end_position + 1 : mention2.start_position
            ]
            be = ["is", "was", "had been", "will be"]
            negatives = ["not", "no", "never", "neither"]
            return (
                mention1.sentence_position == mention2.sentence_position
                and len(mid) <= 3
                and True in [a in mention2.animate for a in mention1.animate]
                and True in [w in utils.join(mid) for w in be]
                and True not in [str(w) not in be and w.pos_tag[:2]=="VB" for w in mid]
                and True not in [w in utils.join(mid) for w in negatives]
                and "," not in utils.join(mid)
            )

        def isAcronym(mention1, mention2):
            cleaned_1 = str(mention1)
            cleaned_2 = utils.join(utils.remove_stopwords(mention2.tokens))

            if " " in cleaned_1:
                return False

            return "".join([str(token)[0] for token in cleaned_2]) == cleaned_1

        for j in range(0, len(self.mentions)):
            current_mention = self.mentions[j]
            if current_mention.isPronoun():
                continue

            for i in range(j - 1, -1, -1):
                candidate = self.mentions[i]
                if Mention.check_i_in_i(current_mention, candidate):
                    continue

                if not candidate.isPronoun() and isAppositive(candidate, current_mention) or isRoleAppositive(
                    candidate, current_mention
                ):
                    candidate.merge(current_mention)
                    break

                if not candidate.isPronoun() and isAcronym(current_mention, candidate):
                    candidate.merge(current_mention)
                    break

                if check_nominative(candidate, current_mention):
                    candidate.merge(current_mention)
                    break

    def strict_head_match(self, relax_word_inclusion=False, relax_modifiers_match=False):
        for j in range(0, len(self.mentions)):

            current_mention = self.mentions[j]


            if current_mention.self_id != current_mention.entity_id:
                continue

            for i in range(j - 1, -1, -1):

                candidate = self.mentions[i]

                if Mention.check_i_in_i(current_mention, candidate):
                    continue
                    
                candidate_entity = self.mentions[candidate.entity_id]

                cleaned_i = utils.remove_stopwords(candidate_entity.tokens)
                if not len(cleaned_i) or candidate_entity.isPronoun():
                    continue

                cleaned_j = utils.remove_stopwords(current_mention.tokens)
                if not len(cleaned_j) or current_mention.isPronoun():
                    continue

                if (
                    (
                        relax_word_inclusion
                        or False not in [str(w) in utils.str_list(cleaned_i) for w in cleaned_j]
                    )
                    and (
                        len(current_mention.head_words()) and False
                        not in [
                            str(w) in utils.str_list(candidate_entity.head_words())
                            for w in current_mention.head_words()
                        ]
                    )
                    and (
                        relax_modifiers_match
                        or False
                        not in [
                            str(w) in utils.str_list(candidate.modifiers())
                            for w in current_mention.modifiers()
                        ]
                    )
                ):
                    candidate.merge(current_mention)
                    break

    def proper_head_match(self):
        for j in range(0, len(self.mentions)):

            current_mention = self.mentions[j]

            if current_mention.self_id != current_mention.entity_id:
                continue

            for i in range(j - 1, -1, -1):

                candidate = self.mentions[i]

                if Mention.check_i_in_i(current_mention, candidate) or (
                        self.mentions[i].ne
                        and self.mentions[j].ne
                        and self.mentions[i] != self.mentions[j]
                    ):
                    continue
                    

                if (
                    len(current_mention.head_words()) and False
                    not in [
                        str(w) in utils.str_list(candidate.head_words())
                        for w in current_mention.head_words()
                    ]
                ) and (
                    False not in [
                        str(w) in utils.str_list(candidate.modifiers())
                        for w in current_mention.modifiers()
                    ]
                ):
                    candidate.merge(current_mention)
                    break

    def relaxed_head_match(self):
        for j in range(0, len(self.mentions)):

            current_mention = self.mentions[j]

            if current_mention.self_id != current_mention.entity_id:
                continue

            for i in range(j - 1, -1, -1):

                candidate = self.mentions[i]

                if Mention.check_i_in_i(current_mention, candidate):
                    continue

                if len(current_mention.head_words()) and False not in [
                    str(w) in utils.str_list(candidate.tokens) for w in current_mention.head_words()
                ]:
                    candidate.merge(current_mention)
                    break


    def pronominal_resolution(self):

        for j in range(1, len(self.mentions)):
            current_mention = self.mentions[j]
            if not current_mention.isPronoun() or (
                current_mention.self_id != current_mention.entity_id
            ):
                continue
            
            max_score = 0

            for i in range(j - 1, -1, -1):
                candidate = self.mentions[i]

                score = 0

                if candidate.isPronoun():
                    if (
                        utils.check_pronoun_group(
                            candidate.tokens[0], current_mention.tokens[0]
                        )
                        and current_mention.sentence_position - candidate.sentence_position
                        <= 3
                    ):
                        candidate.merge(current_mention)
                        break

                else:
                    if current_mention.sentence_position - candidate.sentence_position > 2:
                        break

                    score += (current_mention.number[0] in candidate.number)
                    score += (current_mention.gender[0] in candidate.gender)
                    score += (True in [a in candidate.animate for a in current_mention.animate])

                    if max_score<score and score>2 and current_mention.self_id == current_mention.entity_id:
                        candidate.merge(current_mention)
                        max_score = score

    def coreference_links(self):
        links = {}
        for mention in self.mentions:
            if mention.self_id == mention.entity_id:
                links[mention.entity_id] = [(mention.sentence_position, mention.start_position, mention.end_position)]
        for mention in self.mentions:
            if mention.self_id != mention.entity_id:
                links[mention.entity_id].append((mention.sentence_position, mention.start_position, mention.end_position))
        
        for link in links.values():
            link.sort()

        return {links[i][0]:links[i][1:] for i in links}

    def merge(self):

        for mention in self.mentions:
            cur = mention

            while cur.self_id != cur.entity_id:
                this_cur = self.mentions[cur.entity_id]
                if this_cur.entity_id < cur.entity_id:
                    this_cur.merge(cur)
                    cur = this_cur
                else:
                    break

            mention.entity_id = cur.entity_id
    
    def remove_singleton_clusters(self):
        singleton = {}
        for i in range(len(self.mentions)):
            singleton[i] = True
        for i in range(len(self.mentions)-1, -1, -1):
            mention = self.mentions[i]
            if mention.self_id!=mention.entity_id:
                singleton[mention.self_id] = False
                singleton[mention.entity_id] = False
        for i in range(len(self.mentions)-1, -1, -1):
            if singleton[i]:
                for m in self.mentions[i].nested:
                    m.parent = None
                del self.mentions[i]

    def summary(self):
        return [mention.summary() for mention in self.mentions]

    def result(self):
        last = 0
        result = ""
        i = -1
        if len(self.mentions) == 0:
            result = " ".join([utils.join(s) for s in self.processed_sentences])
        for mention in self.mentions:
            if mention.parent:
                continue
            if i < mention.sentence_position:
                if i >= 0 and last < len(self.processed_sentences[i]):
                    result += " " + utils.join(self.processed_sentences[i][last:])
                i = mention.sentence_position
                last = 0

            start = mention.start_position
            end = mention.end_position

            if start > last:
                result += " " + utils.join(self.processed_sentences[i][last:start])

            result += " " + mention.info()

            last = end + 1

        if i>=0 and  i < len(self.processed_sentences) and last < len(self.processed_sentences[i]):
            result += " " + utils.join(self.processed_sentences[i][last:])
            i+=1

        while i>=0 and i < len(self.processed_sentences): 
            result += " "+utils.join(self.processed_sentences[i])
            i+=1

        return result

    def resolve(self, debug=False, test=False):

        if not test:
            self.pre_process()
            self.mention_detection()
        
        self.mentions.sort()

        self.speaker_identification()

        self.exact_string_match()

        self.approx_string_match()

        self.precise_constructs_match()

        self.strict_head_match()

        self.strict_head_match(relax_modifiers_match=True)

        self.strict_head_match(relax_word_inclusion=True)

        self.proper_head_match()

        self.relaxed_head_match()

        self.pronominal_resolution()

        self.merge()


        if debug:
            print(self.summary())

        return self.result()

    def test(self):
        with open(
            os.path.join(__location__, "data/train.english.v4_gold_conll"),
            "r",
            encoding="utf8",
        ) as f:
            dataset = f.read()
        f.close()

        true_positive = 0
        false_positive = 0
        false_negative = 0

        precision = 0
        recall = 0 
        f1 = 0

        document_position = -1
        prange = {10*i:list() for i in range(11)}
        last_speaker = None

        for document in dataset.split("\n\n#end document"):
            annotated = {}
            predicted = {}
            sentence_position = -1
            document_position += 1
            entity_map = {}
            entity_id = 0
            cur_ne_tag = ""
            start=False
            self.mentions = []
            self.processed_sentences = []
            Mention.id = 0

            for annotations in document.split("\n\n"):
                phrase_reference = {}
                words = []
                tokens = []
                sentence_position += 1
                
                for annotation in annotations.split("\n"):
                    annotation = re.sub(r"\s+", r"\t", annotation)
                    annotation = annotation.split("\t")
                    if len(annotation) <= 10:
                        continue

                    word_position = int(annotation[2])
                    word = annotation[3]
                    words.append(word)
                    pos_tag = annotation[4]
                    coreference = annotation[-1]
                    speaker = annotation[9]

                    if len(annotation)>=11:
                        ne_tag = annotation[10]
                        if ne_tag[0]=='(':
                            cur_ne_tag = ne_tag[1:-1]
                            if ne_tag[-1]!=')':
                                start = True
                            else:
                                start=False
                            ne_tag='B-'+cur_ne_tag
                        elif ne_tag=='*' and start:
                            ne_tag='I-'+cur_ne_tag
                        elif ne_tag=='*)':
                            ne_tag='I-'+cur_ne_tag
                            start=False
                            cur_ne_tag=''
                        else:
                            cur_ne_tag=''
                            ne_tag='O'
                    else:
                        cur_ne_tag=''
                        ne_tag='O'

                    token = Token(word, pos_tag, ne_tag)
                    tokens.append(token)                

                    if "-" in coreference:
                        continue
                    for c in coreference.split("|"):
                        link = re.findall("\d+", c)[0]
                        if c[0] == "(":
                            if link in phrase_reference:
                                phrase_reference[link].append(word_position)
                            else:
                                phrase_reference[link] = [word_position]
                        if c[-1] == ")":
                            if link in phrase_reference:
                                start_position = phrase_reference[link].pop()
                                phrase = tokens[start_position:]
                                end_position = start_position + len(phrase) - 1
                                
                                mention = Mention(phrase, sentence_position, start_position, end_position)
                                mention.speaker = speaker
                                self.assign_gender_number(mention)
                                self.mentions.append(mention)

                                if link not in entity_map:
                                    entity_map[link] = entity_id
                                    annotated[entity_map[link]] = []
                                    entity_id+=1

                                annotated[entity_map[link]].append((sentence_position, start_position, end_position))

                self.processed_sentences.append(tokens)

            for (i, mention1) in enumerate(self.mentions):
                for mention2 in self.mentions[:i]:
                    if mention1!=mention2 and mention1.sentence_position == mention2.sentence_position and mention.start_position <= mention2.start_position and mention2.end_position <= mention1.end_position:
                        mention2.parent = mention1
                        mention1.nested.append(mention2)


            self.resolve(test=True)

            predicted = []

            for (i, m1) in enumerate(self.mentions):
                for m2 in self.mentions[i+1:]:
                    if m1.self_id!=m2.self_id and m1.entity_id==m2.entity_id:
                        a_i = (m1.sentence_position, m1.start_position, m1.end_position)
                        a_j = (m2.sentence_position, m2.start_position, m2.end_position)
                        p = sorted((a_i, a_j))
                        if  p not in predicted:
                            predicted.append(p)

            link_size = 0
            for e in annotated:
                for (i, m1) in enumerate(annotated[e]):
                    for m2 in annotated[e][i+1:]:
                        if sorted((m1, m2)) in predicted:
                            link_size += 1
                            true_positive += 1
                        else:
                            false_negative += 1   

            if len(predicted)>link_size:
                false_positive += len(predicted) - link_size


            precision = true_positive/(true_positive + false_positive)
            recall = true_positive/(true_positive + false_negative)
            f1 = 2*(precision*recall)/(precision+recall)

            print(document_position, precision, recall, f1)

        print()
        print("Precision: ", precision*100)
        print("Recall: ", recall*100)
        print("F1: ", f1*100)
        
        return ((precision, recall, f1))



if __name__ == "__main__":
    sentences = "I think it is very hard , as joint development and sovereignty of the islands are , ah , two concepts . It won't work , either , eh , eh . But this is relevant . Uh-huh . Oh , as I just mentioned , it was against a large background that Russia first proposed it . Uh-huh . With , quite a troubled economy , Russia needed Japanese investment , needed Japan to get involved through this channel . Uh-huh . Well , now that its economy has greatly improved , Russia does not need to take this diplomatic risk . Uh-huh . This is one . Second , Russia should be seen as a rather strong nation . Well , this place , the four northern islands , is a very sensitive region for the Russian psyche . Any small , small diplomatic or economic action will affect the psyche of Russian citizens . Uh-huh ."

    cr = CoreferenceResolution(sentences)
    cr.resolve()
