# Guida a `bc-al-data` — spiegata semplice

Questa cartella contiene **una fabbrica di esempi didattici** per insegnare a un
modello AI a scrivere codice per Business Central senza inventarsi la sintassi.
Qui sotto ti spiego cos'è ogni pezzo, senza dare per scontati i termini.

---

## 1. L'obiettivo, in una frase

Il modello che gira sul tuo server sa programmare in generale, ma quando scrive
in **AL** (il linguaggio di Business Central) si inventa comandi che non
esistono. Per correggerlo dobbiamo **mostrargli tanti esempi di AL vero e
verificato**. Questa cartella è la macchina che produce quegli esempi.

Il risultato finale sarà un file di migliaia di righe tipo:

```
domanda: "scrivi una procedura che fa X"   →   risposta: <codice AL corretto>
```

Poi quel file lo si dà in pasto all'addestramento (il "fine-tuning" di cui
abbiamo parlato nel piano). Quella è una fase separata, che richiede una GPU
potente e la faremo dopo.

---

## 2. I mattoni, uno per uno

### Il compilatore AL (`al`)
È il programma di Microsoft che trasforma il codice AL in qualcosa di
eseguibile. Per noi è soprattutto un **giudice automatico**: gli diamo un pezzo
di codice, e lui ci dice "questo va bene" oppure "riga 7, errore: la funzione
`Pippo` non esiste". Ogni esempio che produciamo deve passare da questo giudice
prima di entrare nel dataset. Se non compila, si butta.

### I "simboli" di Business Central
Business Central è enorme: migliaia di tabelle, funzioni, oggetti già pronti. I
**simboli** sono dei file (`.app`) che descrivono tutta questa roba già esistente,
così il compilatore sa cosa esiste e cosa no. Li abbiamo già in cache
(9 GB, versione 28.0, nessun download necessario).

### Gli "analyzer" / linter (ALCops, CodeCop)
Il compilatore dice solo se il codice è *sbagliato*. Gli **analyzer** vanno
oltre: dicono se il codice è *brutto* pur essendo giusto — "questa procedura è
troppo complicata", "manca la documentazione", "usa questo metodo invece di
quello". Sono ~500 regole in totale. Le usiamo per insegnare al modello anche lo
*stile* buono, non solo la sintassi valida.

### `tree-sitter`
Una libreria che legge un file di codice AL e lo trasforma in una specie di
**indice strutturato**: "in questo file c'è un oggetto chiamato X, dentro ci sono
3 procedure, la seconda si chiama `Calcola` e va dalla riga 40 alla 55". Ci serve
per ritagliare pezzi di codice con precisione (una procedura intera, il corpo di
una funzione) senza sbagliare.

### La mappa degli errori (`data/al_error_map.json`)
Un elenco di **tutti i 919 tipi di errore** che il compilatore AL può dare (più
le ~400 regole degli analyzer), ognuno con:
- cosa significa
- quanto è probabile che un'AI ci caschi ("alta / media / bassa")
- come si potrebbe correggere automaticamente

È la "enciclopedia degli sbagli" che guida tutto il resto.

---

## 3. I generatori — le 8 macchine che producono esempi

Ogni generatore prende codice AL vero (da BCApps, il codice open source di
Business Central, licenza libera) e ne ricava un tipo di esempio. Le chiamiamo
**G1, G2, ...** solo per comodità.

| nome | cosa produce | come |
|---|---|---|
| **G1** – completa il corpo | "ecco l'inizio di una procedura, scrivi tu il resto" → il corpo vero | prende una procedura vera, nasconde il corpo, chiede di ricostruirlo |
| **G2** – dall'intento al codice | "questa procedura deve fare X (spiegazione), implementala" → il codice vero | usa i commenti-documentazione già presenti come "intento" |
| **G3** – spiega il codice | "spiega questa procedura" → una spiegazione in italiano/inglese | i *fatti* (quali funzioni chiama, quali tabelle usa) li estrae in modo automatico, la *prosa* la scrive il modello (partendo dai fatti, così non inventa) |
| **G4** – domande sulla documentazione | "in AL, come si fa X?" → la risposta dalla documentazione ufficiale | spezzetta i manuali Microsoft in domande/risposte |
| **G5** – dall'errore alla correzione | codice ROTTO → codice GIUSTO | prende codice giusto e ci introduce **una** rottura precisa (vedi sotto) |
| **G6** – dalla specifica all'oggetto | "crea una tabella con questi campi" → la tabella vera | usa tabelle/enumerazioni piccole e autocontenute |
| **G7** – dagli sbagli del modello stesso | codice sbagliato che ha prodotto il modello → la versione corretta | fa generare il modello, tiene solo ciò che NON compila, lo aggiusta |
| **G8** – dal codice brutto al codice pulito | codice che gli analyzer bocciano → la versione ripulita | usa la funzione "correggi automaticamente" degli analyzer |

### Le "mutazioni" di G5 (il pezzo su cui abbiamo lavorato molto)

G5 ha bisogno di codice *rotto in modo prevedibile*. Abbiamo scritto **14
"mutazioni"**: ognuna prende codice giusto e fa un danno specifico che genera un
tipo di errore noto. Esempi:

- `m_rename_call` — rinomina una funzione chiamata (`Calcola` → `CalcolaX`) → errore "questa funzione non esiste" (esattamente ciò che il modello fa quando si inventa i nomi)
- `m_delete_semicolon` — toglie un punto e virgola → errore di sintassi
- `m_remove_var_decl` — cancella la dichiarazione di una variabile che poi viene usata → errore "nome sconosciuto"
- `m_rename_trigger` — cambia il nome di un trigger in uno inventato → errore "trigger non valido"
- `m_swap_argument_count` — toglie o aggiunge un parametro a una chiamata → errore "numero di argomenti sbagliato"
- ... e altre 9

Ogni mutazione è stata **calibrata**: l'abbiamo eseguita su ~100 pezzi di codice
veri per verificare che produca davvero l'errore atteso. 12 su 14 funzionano in
modo affidabile.

### L'auto-correttore di G7 (`autofix.py`)

Quando il modello scrive codice sbagliato, invece di dargli semplicemente "la
risposta giusta originale", proviamo a **correggere il SUO codice**. Prova in
ordine:
1. correzioni meccaniche (aggiungi il `;` mancante, togli quello di troppo)
2. correzioni "per somiglianza" — se il modello ha scritto `Calcolaa` e nel
   codice vicino c'è `Calcola`, capisce che intendeva quello e lo corregge
3. le correzioni automatiche degli analyzer
4. se niente funziona, ripiega sulla risposta originale

Così l'esempio diventa "il tuo codice era così, ecco come si aggiusta" — molto
più istruttivo di "ecco una risposta completamente diversa".

---

## 4. Come scorre tutto — la catena di montaggio

```
1. sources     →  scarica il codice sorgente (BCApps, ecc.), fissato a una versione precisa
2. blocklist   →  fa la lista di ciò che NON va usato (vedi "contaminazione" nel glossario)
3. baselines   →  compila ogni "app" di BCApps una volta, per sapere quali partono già pulite
4. corpus      →  ritaglia ogni procedura/funzione dalle app pulite in una riga di database
5. generate    →  le 8 macchine (G1-G8) producono migliaia di esempi candidati
6. verify      →  OGNI esempio passa dal compilatore; si tiene solo ciò che compila come deve
7. filter      →  toglie i doppioni e ciò che è contaminato o con licenza non libera
8. assemble    →  impacchetta tutto in train / validazione / test, con una scheda riassuntiva
```

Ogni passo si può rifare senza ripartire da capo (i risultati sono in cache).
Il comando è sempre `uv run bcaldata <passo>` (es. `uv run bcaldata corpus`).

Il passo lento è **verify**: compilare costa 15-45 secondi a esempio. Per G1, G2
e G6 c'è una scorciatoia (se l'esempio è codice originale verbatim e la sua app
compilava già pulita, è verificato all'istante). Il costo vero è G5 e G7.

---

## 5. Dove sta cosa

```
bc-al-data/
├── env.sh                  variabili d'ambiente — da caricare per prima cosa
├── run_pipeline.sh         esegue tutta la catena di montaggio
├── PIPELINE.md             dettaglio tecnico di ogni passo
├── MORNING_REPORT.md       cos'è stato fatto stanotte
├── GUIDA.md                questo file
│
├── src/bcaldata/           il codice della fabbrica
│   ├── alparse.py          legge i file AL (tree-sitter)
│   ├── corpus.py           ritaglia le procedure
│   ├── generators.py       le 8 macchine G1-G8
│   ├── mutations.py        le 14 rotture di G5
│   ├── autofix.py          l'auto-correttore di G7
│   ├── compile_gate.py     parla col compilatore AL
│   ├── verify_inapp.py     il "giudice": compila ogni esempio nella sua app vera
│   ├── verify.py           orchestratore della verifica
│   ├── filter.py           toglie doppioni e contaminati
│   ├── assemble.py         impacchetta il dataset finale
│   ├── mcp_client.py       parla con gli analyzer ALCops
│   ├── alsp.py             parla col servizio di navigazione del codice AL
│   ├── llm.py              parla col modello sul server (NON usato finché non liberi la GPU)
│   └── cli.py              i comandi `uv run bcaldata ...`
│
├── data/
│   ├── al_error_map.json           l'enciclopedia dei 1324 tipi di errore
│   ├── al_error_map.summary.md      la classifica dei 40 errori più comuni
│   ├── g5_calibration.md            quale mutazione produce quale errore
│   ├── corpus.jsonl                 le procedure ritagliate (una per riga)
│   ├── candidates/                  esempi prodotti dai generatori (non ancora verificati)
│   ├── verified/                    esempi che hanno passato il compilatore
│   ├── filtered/                    esempi dopo la pulizia
│   └── dataset/                     il prodotto finale: train.jsonl, val.jsonl, ecc.
│
├── vendor/
│   ├── BCApps/              il codice sorgente di Business Central (open source, MIT)
│   ├── Analyzers/           il codice degli analyzer ALCops
│   └── mcp-server/          il server degli analyzer (compilato in bin/)
│
├── bin/
│   ├── alcops-mcp           avvia il server degli analyzer
│   └── build-alcops-mcp.sh  lo ricompila se serve
│
└── tests/                   i test automatici (uv run pytest)
```

---

## 6. Glossario — i termini che tornano

- **AL** — il linguaggio di programmazione di Business Central.
- **BCApps** — il repository pubblico con tutto il codice sorgente di Business
  Central, licenza MIT (libera). È il nostro giacimento di codice vero.
- **compilare** — passare il codice al programma `al` che verifica se è valido.
- **simboli** — i file che descrivono ciò che esiste già in Business Central.
- **corpus** — l'insieme di tutte le procedure ritagliate dal codice sorgente,
  una per riga di database, pronte da usare nei generatori.
- **dataset** — il prodotto finale: le domande/risposte per l'addestramento.
- **candidato** — un esempio prodotto da un generatore ma non ancora verificato.
- **verify / gate** — il passo in cui ogni candidato viene compilato; solo chi
  passa entra nel dataset.
- **mutazione** — una modifica precisa che rompe del codice giusto in modo
  prevedibile (per il generatore G5).
- **SFT (Supervised Fine-Tuning)** — l'addestramento "normale": mostri
  domanda + risposta giusta e il modello impara a imitare.
- **preference pair (coppia di preferenza)** — invece di una sola risposta, ne
  dai due: "questa è meglio di quest'altra". Il modello impara cosa *evitare*.
  G5 e G7 producono questo tipo di esempio.
- **contaminazione** — quando un esempio di addestramento è troppo simile a un
  test di valutazione. Se succede, la valutazione non vale più niente (il modello
  ha "visto le risposte"). Il passo `blocklist` costruisce la lista di cosa
  escludere, basandosi su **BC-Bench** (il benchmark che abbiamo già).
- **decontaminazione** — il processo di togliere gli esempi contaminati.
- **held-out (tenuto da parte)** — alcune app di BCApps vengono riservate e non
  entrano mai nell'addestramento, così possiamo testarci onestamente sopra.
- **licenza libera** — MIT, Apache, ecc.: codice che si può legalmente riusare.
  Il passo `filter` scarta tutto ciò che non ha una licenza libera.
- **analyzer / linter / cop** — programmi che segnalano codice brutto ma valido.
  ALCops è la raccolta principale (LinterCop, FormattingCop, ecc.).
- **LSP** — un servizio che dà informazioni sul codice (dove è definita questa
  funzione, che tipo ha questa variabile). Lo usiamo per l'auto-correttore.
- **MCP** — un modo standard con cui programmi diversi si parlano. Gli analyzer
  ALCops offrono un server di questo tipo, con cui chiediamo "correggi questo".

---

## 7. Stato attuale (2026-09-03)

**Funziona e testato:**
- la catena di montaggio completa (comandi `uv run bcaldata ...`)
- G1 (completa il corpo): 100% degli esempi verificati passa
- G5 (errore→correzione): ~96% passa, e produce gli errori giusti (funzione
  inventata, nome sconosciuto, sintassi, ecc.)
- l'enciclopedia degli errori, le 14 mutazioni, l'auto-correttore, gli analyzer

**Da sistemare (dettagli in `MORNING_REPORT.md`):**
- scaricare gli altri sorgenti (`uv run bcaldata sources`) — ora c'è solo BCApps
- G2 e G6 perdono ~35% in verifica per un controllo troppo severo — da allentare
- il run completo della pipeline (lungo, va lanciato quando la GPU è libera e il
  server non serve)
- G3 e G7 usano il modello: da lanciare quando liberi la GPU

**Niente di tutto questo tocca la GPU.** Il modello sul server è usato solo da
`llm.py`, che finora non abbiamo eseguito.
