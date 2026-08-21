# filo — istruzioni per lo sviluppo

## Cosa è questo repository
Ricostruisce la catena di provenienza di modelli e dataset su Hugging Face,
raccoglie le licenze dichiarate con le evidenze, emette CycloneDX 1.6/1.7.
CONSTATA I FATTI. Non valuta compatibilità, non emette giudizi giuridici.

## Invarianti — non violare mai
1. Nessuna asserzione senza EvidenceRef. Se il tipo lo consente, il tipo è sbagliato.
2. L'assenza è uno stato con evidenza (LicenseConfidence.ABSENT + searched_locations),
   mai None, mai stringa vuota, mai confusa con un errore di rete.
3. Solo constatazioni. Nessuna stringa di output può contenere "violates",
   "non-compliant", "illegal", "infringing" o simili.
4. Ogni limite applicato all'attraversamento è dichiarato in Chain.traversal.
   Un troncamento silenzioso è un difetto bloccante.
5. Nessun import da repository privati o interni. Questo codice è pubblico.
6. Nessuna chiamata di rete nei test. Solo cassette registrate.
7. Intestazione SPDX-License-Identifier: Apache-2.0 su ogni file sorgente.
8. Output rivolto all'utente in inglese, in file di catalogo separati dalla logica.

## Ordine di costruzione
ir.py e evidence.py per primi. Tutto il resto è un adattatore da o verso di loro.
Non costruire CycloneDX direttamente dalle risposte dell'API.

## Modifiche allo schema
Aggiungere campi facoltativi: nessun cambio di schema_version.
Rimuovere campi o cambiarne la semantica: incrementare schema_version
e scrivere la nota di migrazione in schemas/MIGRATIONS.md.

## Test di accettazione
Il test di accettazione fa camminare una catena reale che contiene un anello
a licenza mancante documentato: lo strumento deve individuare l'artefatto a
monte che non dichiara licenza, con l'evidenza dei percorsi cercati. Se non lo
fa, lo strumento non funziona. La catena concreta vive nelle fixture in `tests/`.

## Cosa non fare
Non scaricare pesi di modelli. Non aggiungere una base di conoscenza delle
licenze. Non aggiungere logica di compatibilità. Quelle stanno altrove
e devono restarci.
