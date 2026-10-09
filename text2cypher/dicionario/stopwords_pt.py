"""
Lista de stopwords em português do Snowball, sem acentos
(https://snowballstem.org/algorithms/portuguese/stop.txt). A única mudança em relação à
lista original foi tirar os acentos, para casar com o tokenizar do retriever.py.

Licença do Snowball (https://snowballstem.org/license.html):

Copyright (c) 2001, Dr Martin Porter,
Copyright (c) 2002, Richard Boulton.
All rights reserved.

Redistribution and use in source and binary forms, with or without modification, are
permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this list of
   conditions and the following disclaimer.
2. Redistributions in binary form must reproduce the above copyright notice, this list of
   conditions and the following disclaimer in the documentation and/or other materials
   provided with the distribution.
3. Neither the name of the copyright holder nor the names of its contributors may be used
   to endorse or promote products derived from this software without specific prior
   written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS
OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF
MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR
TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

STOPWORDS = {'a', 'ao', 'aos', 'aquela', 'aquelas', 'aquele', 'aqueles', 'aquilo', 'as', 'ate',
             'com', 'como', 'da', 'das', 'de', 'dela', 'delas', 'dele', 'deles', 'depois', 'do',
             'dos', 'e', 'ela', 'elas', 'ele', 'eles', 'em', 'entre', 'era', 'eram', 'eramos',
             'essa', 'essas', 'esse', 'esses', 'esta', 'estamos', 'estao', 'estas', 'estava',
             'estavam', 'estavamos', 'este', 'esteja', 'estejam', 'estejamos', 'estes', 'esteve',
             'estive', 'estivemos', 'estiver', 'estivera', 'estiveram', 'estiveramos',
             'estiverem', 'estivermos', 'estivesse', 'estivessem', 'estivessemos', 'estou', 'eu',
             'foi', 'fomos', 'for', 'fora', 'foram', 'foramos', 'forem', 'formos', 'fosse',
             'fossem', 'fossemos', 'fui', 'ha', 'haja', 'hajam', 'hajamos', 'hao', 'havemos',
             'hei', 'houve', 'houvemos', 'houver', 'houvera', 'houveram', 'houveramos',
             'houverao', 'houverei', 'houverem', 'houveremos', 'houveria', 'houveriam',
             'houveriamos', 'houvermos', 'houvesse', 'houvessem', 'houvessemos', 'isso', 'isto',
             'ja', 'lhe', 'lhes', 'mais', 'mas', 'me', 'mesmo', 'meu', 'meus', 'minha', 'minhas',
             'muito', 'na', 'nao', 'nas', 'nem', 'no', 'nos', 'nossa', 'nossas', 'nosso',
             'nossos', 'num', 'numa', 'o', 'os', 'ou', 'para', 'pela', 'pelas', 'pelo', 'pelos',
             'por', 'qual', 'quando', 'que', 'quem', 'sao', 'se', 'seja', 'sejam', 'sejamos',
             'sem', 'sera', 'serao', 'serei', 'seremos', 'seria', 'seriam', 'seriamos', 'seu',
             'seus', 'so', 'somos', 'sou', 'sua', 'suas', 'tambem', 'te', 'tem', 'temos',
             'tenha', 'tenham', 'tenhamos', 'tenho', 'tera', 'terao', 'terei', 'teremos',
             'teria', 'teriam', 'teriamos', 'teu', 'teus', 'teve', 'tinha', 'tinham', 'tinhamos',
             'tive', 'tivemos', 'tiver', 'tivera', 'tiveram', 'tiveramos', 'tiverem', 'tivermos',
             'tivesse', 'tivessem', 'tivessemos', 'tu', 'tua', 'tuas', 'um', 'uma', 'voce',
             'voces', 'vos'}
