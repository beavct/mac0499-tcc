"""
Funções de casamento entre a pergunta e os valores do banco, do BRIDGE (Lin et al., 2020),
usadas também pelo value retriever do CodeS (Li et al., 2024). Copiadas do repositório
original, https://github.com/salesforce/TabularSemanticParsing (src/common/content_encoder.py
e src/utils/utils.py).

Alterações: só as funções usadas aqui foram trazidas, num arquivo só (por isso utils.x()
virou x()); as stopwords em inglês foram trocadas pela lista em português do Snowball, sem
acentos, e as palavras comuns ("no", "yes", "many"), pelas equivalentes em português.

---------------------------------------------------------------------------------------------
Código da Salesforce:

BSD 3-Clause License

Copyright (c) 2020, Salesforce.com, Inc.
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this
   list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

3. Neither the name of the copyright holder nor the names of its
   contributors may be used to endorse or promote products derived from
   this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

---------------------------------------------------------------------------------------------
Lista de stopwords em português do Snowball (https://snowballstem.org/algorithms/portuguese/
stop.txt), sob a licença BSD:

Copyright (c) 2001, Dr Martin Porter,
Copyright (c) 2002, Richard Boulton.
All rights reserved.

Redistribution and use in source and binary forms, with or without modification, are
permitted provided that the following conditions are met: 1. Redistributions of source code
must retain the above copyright notice, this list of conditions and the following
disclaimer. 2. Redistributions in binary form must reproduce the above copyright notice,
this list of conditions and the following disclaimer in the documentation and/or other
materials provided with the distribution. 3. Neither the name of the copyright holder nor
the names of its contributors may be used to endorse or promote products derived from this
software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS
OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF
MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE
GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED
AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED
OF THE POSSIBILITY OF SUCH DAMAGE.
"""

import difflib
from rapidfuzz import fuzz

# fmt: off
_stopwords = {'a', 'ao', 'aos', 'aquela', 'aquelas', 'aquele', 'aqueles', 'aquilo', 'as', 'ate',
              'com', 'como', 'da', 'das', 'de', 'dela', 'delas', 'dele', 'deles', 'depois', 'do',
              'dos', 'e', 'ela', 'elas', 'ele', 'eles', 'em', 'entre', 'era', 'eram', 'eramos',
              'essa', 'essas', 'esse', 'esses', 'esta', 'estamos', 'estao', 'estas', 'estava',
              'estavam', 'estavamos', 'este', 'esteja', 'estejam', 'estejamos', 'estes',
              'esteve', 'estive', 'estivemos', 'estiver', 'estivera', 'estiveram', 'estiveramos',
              'estiverem', 'estivermos', 'estivesse', 'estivessem', 'estivessemos', 'estou',
              'eu', 'foi', 'fomos', 'for', 'fora', 'foram', 'foramos', 'forem', 'formos',
              'fosse', 'fossem', 'fossemos', 'fui', 'ha', 'haja', 'hajam', 'hajamos', 'hao',
              'havemos', 'hei', 'houve', 'houvemos', 'houver', 'houvera', 'houveram',
              'houveramos', 'houverao', 'houverei', 'houverem', 'houveremos', 'houveria',
              'houveriam', 'houveriamos', 'houvermos', 'houvesse', 'houvessem', 'houvessemos',
              'isso', 'isto', 'ja', 'lhe', 'lhes', 'mais', 'mas', 'me', 'mesmo', 'meu', 'meus',
              'minha', 'minhas', 'muito', 'na', 'nao', 'nas', 'nem', 'no', 'nos', 'nossa',
              'nossas', 'nosso', 'nossos', 'num', 'numa', 'o', 'os', 'ou', 'para', 'pela',
              'pelas', 'pelo', 'pelos', 'por', 'qual', 'quando', 'que', 'quem', 'sao', 'se',
              'seja', 'sejam', 'sejamos', 'sem', 'sera', 'serao', 'serei', 'seremos', 'seria',
              'seriam', 'seriamos', 'seu', 'seus', 'so', 'somos', 'sou', 'sua', 'suas', 'tambem',
              'te', 'tem', 'temos', 'tenha', 'tenham', 'tenhamos', 'tenho', 'tera', 'terao',
              'terei', 'teremos', 'teria', 'teriam', 'teriamos', 'teu', 'teus', 'teve', 'tinha',
              'tinham', 'tinhamos', 'tive', 'tivemos', 'tiver', 'tivera', 'tiveram', 'tiveramos',
              'tiverem', 'tivermos', 'tivesse', 'tivessem', 'tivessemos', 'tu', 'tua', 'tuas',
              'um', 'uma', 'voce', 'voces', 'vos'}
# fmt: on

_commonwords = {
    'nao', 'sim', 'muitos'
}

string_types = (type(b''), type(u''))


def is_number(s):
    try:
        float(s.replace(',', ''))
        return True
    except:
        return False


def is_stopword(s):
    return s.strip() in _stopwords


def is_commonword(s):
    return s.strip() in _commonwords


def is_common_db_term(s):
    return s.strip() in ['id']


class Match(object):
    def __init__(self, start, size):
        self.start = start
        self.size = size


def is_span_separator(c):
    return c in '\'"()`,.?! '


def split(s):
    return [c.lower() for c in s.strip()]


def prefix_match(s1, s2):
    i, j = 0, 0
    for i in range(len(s1)):
        if not is_span_separator(s1[i]):
            break
    for j in range(len(s2)):
        if not is_span_separator(s2[j]):
            break
    if i < len(s1) and j < len(s2):
        return s1[i] == s2[j]
    elif i >= len(s1) and j >= len(s2):
        return True
    else:
        return False


def get_effecitve_match_source(s, start, end):
    _start = -1

    for i in range(start, start - 2, -1):
        if i < 0:
            _start = i + 1
            break
        if is_span_separator(s[i]):
            _start = i
            break

    if _start < 0:
        return None

    _end = -1
    for i in range(end - 1, end + 3):
        if i >= len(s):
            _end = i - 1
            break
        if is_span_separator(s[i]):
            _end = i
            break

    if _end < 0:
        return None

    while(_start < len(s) and is_span_separator(s[_start])):
        _start += 1
    while(_end >= 0 and is_span_separator(s[_end])):
        _end -= 1

    return Match(_start, _end - _start + 1)


def get_matched_entries(s, field_values, m_theta=0.85, s_theta=0.85):
    if not field_values:
        return None

    if isinstance(s, str):
        n_grams = split(s)
    else:
        n_grams = s

    matched = dict()
    for field_value in field_values:
        if not isinstance(field_value, string_types):
            continue
        fv_tokens = split(field_value)
        sm = difflib.SequenceMatcher(None, n_grams, fv_tokens)
        match = sm.find_longest_match(0, len(n_grams), 0, len(fv_tokens))
        if match.size > 0:
            source_match = get_effecitve_match_source(n_grams, match.a, match.a + match.size)
            if source_match and source_match.size > 1:
                match_str = field_value[match.b:match.b + match.size]
                source_match_str = s[source_match.start:source_match.start+source_match.size]
                c_match_str = match_str.lower().strip()
                c_source_match_str = source_match_str.lower().strip()
                c_field_value = field_value.lower().strip()
                if c_match_str and not is_number(c_match_str) and not is_common_db_term(c_match_str):
                    if is_stopword(c_match_str) or is_stopword(c_source_match_str) or \
                            is_stopword(c_field_value):
                        continue
                    if c_source_match_str.endswith(c_match_str + '\'s'):
                        match_score = 1.0
                    else:
                        if prefix_match(c_field_value, c_source_match_str):
                            match_score = fuzz.ratio(c_field_value, c_source_match_str) / 100
                        else:
                            match_score = 0
                    if (is_commonword(c_match_str) or is_commonword(c_source_match_str) or
                            is_commonword(c_field_value)) and match_score < 1:
                        continue
                    s_match_score = match_score
                    if match_score >= m_theta and s_match_score >= s_theta:
                        if field_value.isupper() and match_score * s_match_score < 1:
                            continue
                        matched[match_str] = (field_value, source_match_str, match_score, s_match_score, match.size)

    if not matched:
        return None
    else:
        return sorted(matched.items(), key=lambda x:(1e16 * x[1][2] + 1e8 * x[1][3] + x[1][4]), reverse=True)
