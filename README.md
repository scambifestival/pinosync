# Cosa fa questo script
`updatingdata.py` è in grado di aggiornare automaticamente i file esportati da Pino (l'istanza _selfhostata_ di Baserow) in formato `JSON` o `CSV` sulla base di alcuni semplici file di configurazione.

## Come usare questo script
Il corretto funzionamento di questo script è strettamente determinato dalla corretta formattazione dei file di configurazione `toUpdate.yml` e `tablesInfos.yml`, 
i quali devono essere inseriti all'interno della directory remota `.pino/` della repository [scambi.org](https://github.com/scambifestival/scambi.org/tree/main/.pino).

`toUpdate.yml` contiene un elenco dei file da aggiornare, mentre `tablesInfos.yml` contiene le informazioni delle tabelle su Pino cui lo script fa riferimento.

### Installazione
È consigliabile usare un ambiente virtuale per eseguire questo script, dacché potrebbero crearsi conflitti con versioni di Python successive a quella adoperata per programmarlo.

#### _tablesInfos.yml_

Questo file contiene i riferimenti alle tabelle su Baserow su cui si basa lo script per aggiornare i file. **È cruciale** che tale file sia presente e correttamente formattato, altrimenti lo script non funziona.

`tablesInfos` è così formattato:

>tables:
>>nome_riferimento_tabella#1:
>>
>>>name: "_nomeTabellaSuBaserow_" (stringa)
>>>
>>>id: _identificativoTabella_ (intero)
>>>
>>>view_id: _identificativoView_ (intero)
>>>
>>>included: "_lista,Di,Colonne,Della,Tabella,Da,Includere,Nel,File,Aggiornato_" (stringa) **case sensitive**
>>>
>>>filters: "_lista,di,filtri,da,applicare,alle,righe_" (stringa)
>>>
>>nome_riferimento_tabella#2:
>>...

I nomi dei campi _name_, _id_, _view_id_, _included_ e _filters_ **devono rimanere invariati**; l'ordine dei campi è ininfluente, ma devono essere tutti presenti.

Nel dettaglio: 
- Il campo _name_ è un riferimento arbitrario alla tabella di riferimento su Pino.
- Il campo _id_ è l'identificativo della tabella su Pino. **Deve** essere un intero positivo. 
- Il campo _view_id_ è l'identificativo di una view relativa a una tabella su Pino. Può essere lasciato a `0`, qualora non sia necessario fare riferimento a una view.   
- Il campo _included_ contiene l'insieme dei nomi delle colonne da includere nel file in uscita. Può essere una stringa vuota, qualora si desideri includere tutte le colonne.
- Il campo _filters_ contiene gli eventuali (ulteriori) filtri da applicare, altrimenti è una stringa vuota.

Nota: _Non è consentito omettere il valore, seppur nullo, dei campi appena riportati._

##### Il campo _filters_

Il campo _filters_ contiene ulteriori eventuali filtri da applicare (se non già applicati all'interno della view indicata). Si sconsiglia di usare 
questo campo (è complicato) e si di applicare tutti i filtri desiderati all'interno di una view creata _ad hoc_ dall'interfaccia di Pino.

Qualora si desideri usare il campo _filters_, ecco le cose da sapere:
1. Tale campo è una stringa contente uno o più filtri, separati da una virgola.
2. Un filtro è indicato nel formato `filter__{field}__{filtertype}=value` dove:
>- `{field}` è l'identificativo del campo su cui applicare il filtro.
>- `{filtertype}` è il tipo di filtro da applicare.
>- `value` è il valore di riferimento.
3. Se un filtro non ha una sintassi corretta, viene ignorato.

Per conoscere tali informazioni, si faccia riferimento alla [documentazione dell'API di Pino](https://pino.scambi.org/api-docs/database/61).

Nota: _lo script non è in grado di gestire filtri che coninvolgano matrici o tipi di dato differenti da stringhe o interi._

##### Gestione degli errori
1. Qualora uno dei campi _name_, _id_, _view_id_, _included_ e _filters_ dovesse essere omesso nel file di configurazione:
> Il file associato alla tabella di riferimento non potrà essere aggiornato né creato.
2. Qualora il campo _name_ non corrisponda al nome reale della tabella su Pino:
> Va bene lo stesso, ma serebbe utile per ausiliare l'utente nell'utilizzo dello script.
3. Qualora il campo _id_ contenga un valore errato (non esistente o scorretto):
> Se il valore è inesistente, il file associato a tale tabella non può essere aggiornato né creato; se il valore esiste ma appartiene a un'altra tabella, il file verrà aggiornato (o creato), 
> ma facendo riferimento a una tabella errata.
4. Qualora il _view_id_ non sia corretto:
> Non verrà considerato dallo script.
5. Qualora il campo _included_ contenga elementi non esistenti nella tabella su Pino:
> Tali elementi vengono ignorati.

#### _toUpdate.yml_
`toUpdate.yml` contiene i nomi dei file da aggiornare o creare; tali nomi sono quelli visualizzati all'avvio di `updatingdata.py`. È così formattato:

>tables:  
>>_nomeRiferimentoTabella#1_: 
>>>file: _nome_file_da_aggiornare#1_  
>>>format: _ESTENSIONE_IN_USCITA_
> 
>>_nomeRiferimentoTabella#2_:  
>>>file: _nome_file_da_aggiornare#2_  
>>>format: _ESTENSIONE_IN_USCITA_

>>...  

`updatingdata.py` usa la configurazione specificata in `tablesInfos.yml` per richiedere il contenuto di una tabella su Pino da inserire all'interno del file indicato in `toUpdate.yml`.

Siccome `updatingdata.py` opera basandosi sui file di configurazione, qualora `toUpdate.yml` non sia presente nella [directory indicata](#come-usare-questo-script), lo script si arresta.

Un _nomeRiferimentoTabella_ è arbitrario; l'unico vincolo è che esso sia uguale in entrambi i file di configurazione, per garantire il collegamento tra tabella su Pino e file da aggiornare.

##### **Creazione di un nuovo file**
Se un _nome_file_da_aggiornare_ non è specificato, verrà creato un nuovo file col formato e la tabella indicati. Si osservi l'esempio:

> Nel seguente esempio, usando le coordinate associate a `relations` (specificate in `tablesInfos.yml`), verrà creato il file `relations.csv`.

>`relations`:
>>`file:` ""  
>>`format`: CSV

Come mostrato nell'esempio, qualora non si voglia indicare il nome di un file per lo scopo appena descritto, è consigliabile inserire comunque una stringa vuota (`""`).

Nota: _in fase di aggiornamento, `updatingdata.py` verifica la presenza di file omonimi ma con formato errato. Si osservi l'esempio:_

> Nel seguente esempio, `updatingdata.py` cercherà il file `relations.json` e chiederà se eliminarlo dalla repository.

> relations:
>> file: relations.csv  
>> format: CSV

> Analogamente qualora il nome di un file non sia indicato.

### Features
`updatingdata.py` ha come funzione principale quella di aggiornare (o creare) i file indicati su `toUpdate.yml` usando le coordinate specificate su `tablesInfos.yml`:
lo script, all'avvio, mostra i file da aggiornare (o creare) e offre la possibilità di eseguire l'aggiornamento con i contenuti attuali delle tabelle su Pino.

Al fine di consentire una maggiore usabilità, `updatingdata.yml` offre anche le seguenti possibilità:
1. `(U)` Aggiorna la configurazione dei file da processare.
2. `(S)` Dei file indicati su `toUpdate.yml`, selezionare solamente alcuni di essi per eseguire l'aggiornamento.
3. `(C)` Dei file indicati su `toUpdate.yml`, cambiare il formato (evidenziato in giallo) dei file in uscita.
4. `(E)` Modificare `toUpdate.yml` da linea di comando.
5. `(T)` Modificare `tablesInfos.yml` da linea di comando.

#### _Auto-update_ di `toUpdate.yml`
Dopo l'aggiornamento remoto, `updatingdata.py` aggiorna il contenuto di `toUpdate.yml` in base alle modifiche apportate alla repository:
- Se un file è stato creato, il suo nome viene aggiunto al file di configurazione al posto del campo vuoto:
> _Prima_  
> `relations`:
>> `file`: ""  
>> `format`: CSV

> _Dopo_  
> `relations`:
>> `file`: relations.csv
>> `format`: CSV

- Se un file cambia estensione, il suo nome viene cambiato con l'estensione del file creato:
> _Prima_  
> `relations`:
>> `file`: relations.csv  
>> `format`: JSON

> _Dopo_  
> `relations`:
>> `file`: relations.json  
>> `format`: JSON

Nota: _le modifiche vengono apportate qualora l'aggiornamento del file processato vada a buon fine._

##### Gestione degli errori

1. Qualora il nome di un file venga esplicitato su `toUpdate.yml`, ma non sia effettivamente presente nella repository remota:
> Lo script tenta di reperire comunque il file indicato in `toUpdate.yml`; se tale file non viene trovato, lo script procederà alla creazione di 
> `nomeRiferimentoTabella.json`, usando la tabella col nome di riferimento indicato.
2. Qualora un file venga indicato come non presente ma sia, in realtà, presente nella repository:
> Lo script tenta comunque di creare un file `nomeRiferimentoTabella.json`; se è già presente un file omonimo, lo script usa il file già presente come file di riferimento.

> Nota: se il file già presente nella repository ha un nome diverso da `nomeRiferimentoTabella.json` , verrà ignorato.
3. Qualora sia specificato un file in formato diverso da quello del file presente nella repository:
> Se il formato del file indicato è `CSV`, ma è presente un omonimo file `JSON`, lo script tenta di creare un nuovo file `JSON` ma, accorgendosi del duplicato,
> devia dalla sua creazione per usare semplicemente il file `JSON` già presente all'interno della repository. Se il formato indicato è `JSON` ma, nella repository, 
> è presente un file `CSV` con lo stesso nome, lo script chiede se rimuovere il `CSV` dalla repository e crea un nuovo file `JSON`.
4. Qualora venga usato un `nomeRiferimentoTabella` non presente all'interno di `tablesInfos`:
> Il relativo file non viene aggiornato.

#### Modalità manuale

Lo script offre due modalità di aggiornamento manuale:
1. **Lista di nomi**: l'utente indica una lista di file da aggiornare nel formato `nomeRiferimentoTabella#1:nomeFile#1,nomeRiferimentoTabella#2:nomeFile#2,...`;
2. **Lista di numeri**: l'utente visualizza un elenco numerato di file disponibili e indica una lista di numeri, ognuno corrispondente a un file all'interno 
dell'elenco, nel formato `#1 #2 ...`.

Nessuna delle modalità manuali consente la creazione di file _ex novo_, per cui l'unico modo per creare file è sfruttare la modalità automatica.

##### Lista di nomi - Gestione degli errori e funzionamento
Lo script riconosce la lista di nomi se al suo interno è presente il carattere `:`.

1. Se il `nomeRiferimentoTabella` di un elemento nella lista indicata non esiste, lo script richiede all'utente di scriverne uno esistente (viene mostrata un lista di nomi di riferimento disponibili).
2. Se il `nomeFile` di un elemento della lista non contiene l'estensione (o la contiene, ma non è `.json` o `.csv`), lo script richiede all'utente di riscrivere il nome del file indicando anche la sua estensione.
3. Se la lista indicata non è formattata correttamente (più di un `:` o nessun `:` per elemento della lista, primo e/o secondo argomento di un elemento della lista non specificato), lo script richiede all'utente di riscrivere l'elemento nella formattazione prevista.

Dopo la correzione di eventuali errori, lo script rimuove dalla lista eventuali elementi duplicati (un elemento è duplicato se possiede entrambi gli argomenti uguali a un altro elemento già presente).

Prima di procedere, lo script chiede all'utente se i file indicati siano corretti (qualora non lo siano, l'utente può eventualmente tornare al menu principale).

Nota: _se un file indicato nella lista non è presente nella repository, lo script ignora quel file e passa al successivo._

#### Lista di numeri - Gestione degli errori e funzionamento

L'utente indica la volontà di voler inserire una lista di numeri digitando `list` nel menù principale.

Viene mostrata una lista numerata di file `JSON` e `CSV` disponibili all'interno della cartella `data`. L'utente può, quindi, indicare una lista di numeri separati da spazi associati ai file da aggiornare.

Se la lista contiene più spazi del necessario, lo script li ignora. 
Se un elemento della lista contiene caratteri non numerici, lo script chiede all'utente di riscrivere tale numero.
Se un elemento della lista non è presente nell'elenco numerato proposto, oppure se un elemento della lisa è duplicato, lo script lo ignora.

Prima di procedere, lo script mostra all'utente i file che saranno soggetti ad aggiornamento.

La selezione della tabella su Pino cui lo script fa riferimento per aggiornare i file indicati in questa modalità avviene verificando se, nel nome del file in esame, sia presente una sottostringa contenente un nome di riferimento esistente.
Qualora non sia presente alcun nome, oppure l'utente desideri fare riferimento a un'altra tabella rispetto a quella suggerita, lo script chiede all'utente d'indicare il nome di riferimento associato alla tabella desiderata (è visualizzabile una lista di nomi disponibili inviando `list`).

Nota: _l'elenco numerato proposto contiene TUTTI i file JSON e CSV presenti nella cartella `data`; sta all'utente assicurarsi di selezionare correttamente i file desiderati._

Nota: _l'aggiornamento automatico di `toUpdate.yml` interessa solamente le righe già presenti all'interno di quel file di configurazione. Se si aggiorna un file usando un nome di riferimento non presente su `toUpdate.yml`, quest'ultimo resterà invariato._

## Funzioni aggiuntive
### Elenco tabelle disponibili
L'utente può richiedere di visualizzare un elenco di nomi di riferimento delle tabelle disponibili digitando `tables` quando concesso.

Dopo aver visionato tale elenco, l'utente può procedere all'indicazione della modalità di aggiornamento desiderata.

