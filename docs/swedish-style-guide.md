# Svensk stilpolicy för översättningar

Den här policyn sammanfattar de regler som `svlang` använder från
*Snabba skrivregler* och *Svenska skrivregler*. Kontrollen delas upp i
maskinellt säkra regler och regler som kräver att granskaren bedömer
sammanhang, genre eller betydelse.

## Automatisk kontroll

- särskrivningar, vanliga stavfel samt de/dem
- mellanslag före skiljetecken och innanför parenteser
- tre punkter vid ellips; ett sammanhållet ellipstecken (`…`) är också möjligt
- svenska citatteckens öppning (`”`, inte `“`)
- stora tal med mellanslag som gruppavskiljare
- mellanslag före procenttecken
- tankstreck i talintervall
- svenska decimaltecken, datumformat och talformat i `l10n-lint`

## Granskningspunkter

Granskaren ska bedöma följande för varje relevant sträng:

1. Skiljetecknets funktion: punkt, frågetecken, utropstecken, komma,
   semikolon, kolon, bindestreck, tankstreck, parentes och snedstreck. Komma före `och` kan vara korrekt mellan huvudsatser och vid parentetiska inskott. Bedöm funktionen i sammanhanget.
2. Stor och liten bokstav i meningar, rubriker, namn, organisationer och
   sammansättningar med namn.
3. Samman- eller särskrivning, även nya och långa sammansättningar.
4. Förkortningar, böjning av förkortningar och punkt/kolon i förkortningar.
5. Tal: sifferform eller utskrivet tal, datum, tider, ordningstal, mått,
   valutor och telefonnummer.
6. Citat och repliker: svenska citattecken, interpunktion vid citat,
   replikstreck och återgivning utan att förvanska innebörden.
7. Stycken, rubriker, punktlistor, kursiv/fet stil och avstavning när
   formatet innehåller sådan struktur.

Översättningar innehåller ofta kod, korta etiketter och text med egen
layout. Därför visas sammanhangsberoende regler som granskningspunkter i
stället för automatiska fel.

## Avgränsning efter genomgång av *Svenska skrivregler*

Hela den tillhandahållna fjärde upplagan (2017), kapitel 1–18, har granskats
mot verktygens regler. Boken behandlar textform och texttyper (kap. 1–2), citat
och källhänvisningar (3–4), avstavning, stavning, böjning, versaler och
sammansättningar (5–9), förkortningar, tal, skiljetecken och symboler (10–13),
engelska ord och texter (14), främmande tecken (15), alfabetisk sortering (16),
teckeninmatning (17) och korrekturtecken (18).

Kapitel 5, delar av 1–4 och 15–18 gäller främst längre dokument, publicering,
referenshantering eller produktion och ger därför inte generella lintregler för
kort UI-text. Stavning, böjning, versaler, sammansättningar, tal och tecken kan
ge säkra automatiska kontroller när formatet och sammanhanget räcker. Bokens
råd om kommatering, lånord, ordval, citat och textform kräver ofta bedömning.
Förordet framhåller också att råden gäller normalfall och att alternativ och
särskilda omständigheter kan motivera andra val. Reglerna här ska därför ses
som säkra kontroller och granskningsstöd, inte som en fullständig maskinell
implementering av boken.

## Källor

- Isof/Språkrådet, [Frågelådan: Hur ska man kommatera?](https://frageladan.isof.se/faqs/30975).
- Isof/Språkrådet, [Frågelådan: Kan man ha kommatecken före och?](https://frageladan.isof.se/faqs/22623).
- Isof/Språkrådet, [Hur ska man använda skiljetecken som punkt, kolon, semikolon, komma och tankstreck i löptext?](https://frageladan.isof.se/faqs/26862).
- Isof, *Snabba skrivregler – i skolan och på jobbet* (2024).
- Ola Karlsson, *Svenska skrivregler*, fjärde upplagan (2017), kapitel 1–18;
  genomgången mot den EPUB som tillhandahölls för verktygsgranskningen.
