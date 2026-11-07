# MAYO1 Lab

Projet pédagogique en Python organisé autour d'une implémentation existante du
schéma de signature MAYO1. Les calculs cryptographiques sont séparés de
l'orchestration et de l'affichage afin de faciliter leur test et une éventuelle
interface pédagogique ultérieure.

> **Important :** ce projet n'est ni une implémentation certifiée ni une
> affirmation de conformité à la spécification officielle MAYO Round 3. Les
> paramètres et les encodages de l'implémentation d'origine ont été préservés.
> Des points restent à confirmer par comparaison à des vecteurs officiels,
> notamment la valeur `F_TAIL = [8, 1, 1, 0]` et les conventions de compteur
> utilisées pour l'expansion AES. Ne l'utilisez pas pour protéger des données
> réelles.

## Architecture

```text
core/       Arithmétique GF(16), matrices, algèbre linéaire et formes quadratiques
crypto/     AES, aléatoire, hachage et encodage
keys/       Paramètres, génération et expansion des clés
scheme/     Émulsificateur, recherche de solution, signature et vérification
tests/      Tests pytest isolés du code de production
app.py      Orchestration de démonstration, sans dépendance d'interface
main.py     Point d'entrée en ligne de commande
```

`app.run_demo(message)` retourne un `DemoResult` contenant les clés compactes
et étendues, la signature et le résultat de vérification. Les fonctions
cryptographiques ne dépendent pas de Streamlit ni d'une autre interface.

## Installation

Python 3.10 ou plus récent est requis.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Sous Windows, activez l'environnement avec `.venv\Scripts\activate`.

## Exécution

Depuis la racine du dépôt :

```bash
python main.py
python main.py "message à signer"
```

La commande affiche les tailles des artefacts et le résultat de la vérification,
sans afficher les clés ni la signature.

## Tests

```bash
python -m pytest -v
```

Les tests vérifient les opérations de corps fini et de matrices, la génération
et l'expansion des clés, puis les chemins de signature et de vérification.

## Trace pédagogique de Sign

`sign(esk, message)` conserve son comportement historique et renvoie seulement
les octets de signature. Pour demander la trace, appeler :

```python
signature, trace = sign(esk, message, return_trace=True)
```

### Structure des objets

La définition de `TraceStep` dans `scheme/trace.py` est :

```python
@dataclass(frozen=True)
class TraceStep:
    number: int
    name: str
    description: str
    data: TraceData = field(default_factory=dict)
    dimensions: Dimensions = field(default_factory=dict)
    status: str = "completed"
```

Les alias de types sont :

```python
TraceData = dict[
    str,
    str | int | bool | list[int] | list[list[int]] | None,
]
Dimensions = dict[str, tuple[int, ...]]
```

`SignTrace` est une dataclass mutable contenant `steps: list[TraceStep]`.
Sa méthode `add_step(name, description, *, data=None, dimensions=None,
status="completed")` ajoute une étape et lui attribue le prochain numéro,
commençant à 1. `TraceStep` est immuable, mais ses dictionnaires `data` et
`dimensions` restent des objets Python mutables. `SignTraceError`, utilisée
pour une signature qui échoue lorsque le traçage est activé, est une sous-classe
de `RuntimeError` qui conserve la trace partielle dans `error.trace`.

### Exemple réel exécuté

Une exécution a généré une nouvelle paire de clés, signé le message
`"Bonjour MAYO1"` avec `return_trace=True`, puis vérifié la signature. Résultat
observé : **464 octets**, vérification **`0`** (valide), et **10 étapes**.
Les clés n’ont pas été affichées. Le sel est une composante publique de la
signature, mais son hexadécimal est masqué dans ce rapport par prudence. Les
aléas et coefficients secrets ou dérivés de secrets ne sont pas inclus dans la
trace.

La trace complète expurgée de cette exécution est :

```json
{
  "steps": [
    {
      "number": 1,
      "name": "secret_key_prepared",
      "description": "La clé étendue a été analysée en mémoire; ses éléments secrets ne sont pas copiés dans la trace.",
      "data": {
        "expanded_key_bytes": 155544,
        "polynomial_count": 80,
        "linking_matrix_count": 80
      },
      "dimensions": {
        "O": [80, 8],
        "P1": [80, 80, 80],
        "L": [80, 80, 8]
      },
      "status": "completed"
    },
    {
      "number": 2,
      "name": "message_digest",
      "description": "SHAKE256 calcule le digest du message.",
      "data": {
        "digest_bytes": 32,
        "digest_preview_hex": "dbc08571cce50ff9"
      },
      "dimensions": {},
      "status": "completed"
    },
    {
      "number": 3,
      "name": "salt_generated",
      "description": "Le sel est dérivé du digest, d'un aléa éphémère et de la graine secrète; seuls le sel public et la taille de l'aléa sont tracés.",
      "data": {
        "salt_bytes": 24,
        "salt_hex": "[masqué]",
        "random_input_bytes": 24
      },
      "dimensions": {},
      "status": "completed"
    },
    {
      "number": 4,
      "name": "target_and_lambda_derived",
      "description": "Le vecteur cible t et la matrice Lambda sont dérivés du digest et du sel.",
      "data": {
        "t_preview": [14, 12, 14, 13, 13, 3, 10, 1],
        "lambda_preview": [[3, 9, 13, 11], [0, 2, 12, 6]]
      },
      "dimensions": {
        "t": [80],
        "Lambda": [80, 88]
      },
      "status": "completed"
    },
    {
      "number": 5,
      "name": "emulsifier_loaded",
      "description": "La table des matrices E est récupérée pour combiner les blocs du système.",
      "data": {
        "block_count": 10
      },
      "dimensions": {
        "E_table": [10, 10],
        "E_entry": [80, 80]
      },
      "status": "completed"
    },
    {
      "number": 6,
      "name": "attempt_values_generated",
      "description": "SHAKE256 dérive les blocs vinegar et le vecteur aléatoire de la tentative; leurs coefficients ne sont pas enregistrés.",
      "data": {
        "attempt": 1,
        "counter": 0,
        "random_output_bytes": 440,
        "vinegar_block_count": 10,
        "random_vector_elements": 80
      },
      "dimensions": {
        "vinegar_blocks": [10, 80],
        "r": [80]
      },
      "status": "completed"
    },
    {
      "number": 7,
      "name": "intermediate_matrices_built",
      "description": "Les matrices intermédiaires liées aux blocs vinegar et les produits W sont construits; leurs coefficients sensibles sont omis.",
      "data": {
        "M_matrix_count": 10,
        "W_matrix_count": 800,
        "coefficients_recorded": false
      },
      "dimensions": {
        "M_matrices": [10, 80, 8],
        "W": [10, 80, 80]
      },
      "status": "completed"
    },
    {
      "number": 8,
      "name": "linear_system_built",
      "description": "Les contributions des blocs sont accumulées pour former A x = y; les coefficients ne sont pas exposés.",
      "data": {
        "matrix_coefficients": 6400,
        "target_elements": 80,
        "coefficients_recorded": false
      },
      "dimensions": {
        "A": [80, 80],
        "y": [80],
        "r": [80]
      },
      "status": "completed"
    },
    {
      "number": 9,
      "name": "sample_solution",
      "description": "SampleSolution cherche une solution en utilisant r pour les variables libres.",
      "data": {
        "attempt": 1,
        "solution_found": true,
        "reason": "solution_found"
      },
      "dimensions": {
        "solution": [80]
      },
      "status": "solved"
    },
    {
      "number": 10,
      "name": "signature_encoded",
      "description": "Les blocs de signature sont assemblés, encodés puis concaténés au sel.",
      "data": {
        "vector_elements": 880,
        "encoded_vector_bytes": 440,
        "salt_bytes": 24,
        "signature_bytes": 464
      },
      "dimensions": {
        "signature_blocks": [10, 88],
        "signature_vector": [880]
      },
      "status": "completed"
    }
  ]
}
```

Les valeurs de digest, de `t` et de `Lambda` ci-dessus sont les aperçus réels
de cette exécution. Le sel est explicitement expurgé ici. Les dimensions et les
tailles sont des métadonnées; aucune valeur de matrice secrète, graine, clé ou
vecteur aléatoire interne n’est montrée.

### Récupérer et parcourir la trace depuis un autre module

Par exemple, une future interface peut importer `sign`, récupérer les étapes
et afficher leurs champs sans intégrer de code d’interface dans les modules
cryptographiques :


```python
from scheme.sign import sign

signature, trace = sign(expanded_secret_key, "Bonjour MAYO1", return_trace=True)

for step in trace.steps:
    print(step.number, step.name, step.status)
    print(step.description)
    print("Données :", step.data)
    print("Dimensions :", step.dimensions)
```

Ne pas afficher ou enregistrer `expanded_secret_key`, la clé compacte, ni les
variables locales de la fonction de signature.

### Sérialisation JSON

`SignTrace` et `TraceStep` sont des dataclasses, mais ne sont pas directement
sérialisables avec `json.dumps(trace)` : cet appel lève `TypeError`. Convertir
d’abord la dataclass en types composés standard avec `dataclasses.asdict` :

```python
import json
from dataclasses import asdict

json_text = json.dumps(asdict(trace), ensure_ascii=False, indent=2)
```

Cette conversion fonctionne pour la trace actuelle : les tuples de dimensions
sont encodés comme des tableaux JSON. Il faut toutefois maintenir le filtrage
des données sensibles avant toute persistance ou transmission de la trace.

## Paramètres et encodages conservés

Les paramètres actuellement utilisés incluent `Q=16`, `N=88`, `M=80`,
`O_DIM=8`, `K=10`, des graines de 24 et 16 octets, et une signature de
464 octets. Les tailles et formats sont ceux de l'implémentation préexistante;
leur présence ici ne constitue pas une attestation de conformité normative.
