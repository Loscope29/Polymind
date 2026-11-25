# Déploiement sur Google Cloud Run

Guide pas à pas pour mettre Polymind en ligne sur Cloud Run. Les commandes sont écrites pour
**PowerShell (Windows)**. Sous macOS/Linux (bash), définissez les variables sans espaces autour
de `=` (`PROJECT_ID="..."`), remplacez le backtick `` ` `` de fin de ligne par `\` et les boucles
`foreach` par des boucles `for`.

Durée : ~45 min la première fois, dont ~20 min de build.

## Architecture

```text
                       ┌──────────── Google Cloud (région europe-west1) ────────────┐
 Code source           │                                                             │
 (poste ou GitHub) ──▶ │  Cloud Build ──▶ Artifact Registry ──▶ Cloud Run            │
                       │  (build Docker)  (image polymind:v1)   service « polymind » │
                       │                                        2 vCPU · 4 Gio       │
                       │                                        0 à 2 instances      │
                       │                       Secret Manager ──▶ GEMINI_API_KEY     │
                       └─────────────────────────────────────────────┬───────────────┘
                                                                     │
  Utilisateurs ── HTTPS (https://polymind-xxxx.run.app) ─────────────┘
                                                                     ├──▶ API Gemini
                                                                     ├──▶ Yahoo Finance
                                                                     └──▶ LangSmith (optionnel)
```

| Composant | Rôle |
|---|---|
| **Cloud Build** | Construit l'image Docker dans le cloud (pas d'envoi de 2 Go depuis votre poste) |
| **Artifact Registry** | Stocke les images versionnées |
| **Cloud Run** | Exécute le conteneur, fournit HTTPS, s'arrête à zéro instance sans trafic |
| **Secret Manager** | Garde la clé Gemini hors de l'image et du code |
| **Compte de service `polymind-run`** | Identité du conteneur : il ne peut que lire ses secrets |

Choix de configuration et raisons :

| Paramètre | Valeur | Pourquoi |
|---|---|---|
| Mémoire | 4 Gio | Pic mesuré à 1,9 Go avec tous les modèles chargés |
| CPU | 2 vCPU | Whisper et Chronos tournent sur CPU |
| Instances | min 0, max 2 | 0 € sans trafic ; plafond de coût et de consommation Gemini |
| Affinité de session | activée | Streamlit garde l'état de chaque utilisateur dans une instance |
| Timeout | 3600 s | Durée maximale d'une connexion WebSocket Streamlit (reconnexion automatique ensuite) |
| Upload max | 30 Mo | Cloud Run refuse les requêtes HTTP/1 de plus de 32 Mio |
| Environnement | 2e génération | Meilleure compatibilité Linux pour TensorFlow et PyTorch |

## 0. Prérequis

- Un compte Google avec la facturation activée (l'essai gratuit offre 300 $ de crédits).
- Google Cloud SDK installé (`gcloud --version`).
- Une clé API Gemini : <https://aistudio.google.com/apikey>.

## 1. Variables

À adapter puis coller dans chaque nouvelle session PowerShell. L'identifiant de projet doit être
unique au monde (6 à 30 caractères, minuscules, chiffres, tirets).

```powershell
$PROJECT_ID = "polymind-demo-123"      # à changer
$REGION     = "europe-west1"           # Belgique, tarifs de niveau 1
$SERVICE    = "polymind"
$REPO       = "polymind"
$IMAGE      = "$REGION-docker.pkg.dev/$PROJECT_ID/$REPO/polymind"
$RUN_SA     = "polymind-run@$PROJECT_ID.iam.gserviceaccount.com"
```

## 2. Projet et API

```powershell
gcloud auth login
gcloud projects create $PROJECT_ID --name="Polymind"
gcloud config set project $PROJECT_ID

# Lier un compte de facturation (identifiant affiché par la première commande)
gcloud billing accounts list
gcloud billing projects link $PROJECT_ID --billing-account=XXXXXX-XXXXXX-XXXXXX

gcloud services enable run.googleapis.com artifactregistry.googleapis.com `
    cloudbuild.googleapis.com secretmanager.googleapis.com
```

## 3. Registre d'images

```powershell
gcloud artifacts repositories create $REPO --repository-format=docker `
    --location=$REGION --description="Images Docker de Polymind"
```

## 4. Secret Gemini

Le plus simple est la console : **Security → Secret Manager → Create secret**, nom
`gemini-api-key`, collez la clé. En ligne de commande :

```powershell
# Fichier temporaire SANS retour à la ligne (PowerShell en ajoute un si on passe par un pipe)
[System.IO.File]::WriteAllText("$PWD\gemini.key", "VOTRE_CLE_GEMINI")
gcloud secrets create gemini-api-key --replication-policy=automatic --data-file=gemini.key
Remove-Item gemini.key
```

Optionnel, pour le tracing LangSmith : même procédure avec un secret `langsmith-api-key`.

## 5. Compte de service de l'application

Le conteneur tourne avec une identité dédiée qui n'a qu'un droit : lire ses secrets.

```powershell
gcloud iam service-accounts create polymind-run --display-name="Polymind (Cloud Run)"

gcloud secrets add-iam-policy-binding gemini-api-key `
    --member="serviceAccount:$RUN_SA" --role="roles/secretmanager.secretAccessor"
```

## 6. Build de l'image avec Cloud Build

À lancer depuis la racine du projet. Les fichiers ignorés par `.gitignore` (`.venv/`, `.env`,
`data/`) ne sont pas envoyés.

```powershell
gcloud builds submit --tag "${IMAGE}:v1" --timeout=3600s
```

Le build prend environ 20 minutes (installation de PyTorch et TensorFlow, téléchargement des
modèles). Les 2 500 premières minutes de build par mois sont gratuites.

> **Erreur de permission sur Artifact Registry ?** Sur certains projets récents, le compte de
> service de Cloud Build n'a pas les droits par défaut. Donnez-les-lui :
>
> ```powershell
> $PROJECT_NUMBER = gcloud projects describe $PROJECT_ID --format="value(projectNumber)"
> $BUILD_SA = "$PROJECT_NUMBER-compute@developer.gserviceaccount.com"
> foreach ($role in "roles/artifactregistry.writer", "roles/logging.logWriter", "roles/storage.objectViewer") {
>     gcloud projects add-iam-policy-binding $PROJECT_ID --member="serviceAccount:$BUILD_SA" --role=$role
> }
> ```

**Alternative sans Cloud Build** (envoi de ~2 Go depuis votre poste) :

```powershell
gcloud auth configure-docker "$REGION-docker.pkg.dev"
docker build -t "${IMAGE}:v1" .
docker push "${IMAGE}:v1"
```

## 7. Déploiement

```powershell
gcloud run deploy $SERVICE `
    --image="${IMAGE}:v1" `
    --region=$REGION `
    --service-account=$RUN_SA `
    --port=8501 `
    --cpu=2 --memory=4Gi `
    --execution-environment=gen2 `
    --cpu-boost `
    --min-instances=0 --max-instances=2 `
    --concurrency=10 `
    --timeout=3600 `
    --session-affinity `
    --set-secrets="GEMINI_API_KEY=gemini-api-key:latest" `
    --set-env-vars="STREAMLIT_SERVER_MAX_UPLOAD_SIZE=30" `
    --allow-unauthenticated
```

Pour LangSmith, ajoutez `LANGSMITH_API_KEY=langsmith-api-key:latest` dans `--set-secrets`
(séparé par une virgule), après avoir donné l'accès à ce secret au compte `polymind-run`
comme à l'étape 5.

La commande affiche l'URL du service (`https://polymind-xxxxx.europe-west1.run.app`).

## 8. Vérification

```powershell
$URL = gcloud run services describe $SERVICE --region=$REGION --format="value(status.url)"
curl.exe -s "$URL/_stcore/health"        # doit afficher : ok
Start-Process $URL
```

Testez les quatre pages. Le premier accès après une période sans trafic prend 30 s à 1 min
(démarrage à froid : chargement de l'image de 2 Go), puis chaque modèle se charge à sa première
utilisation.

## 9. Garde-fous de coût

L'URL est publique : n'importe qui peut consommer votre quota Gemini et du temps de calcul.
`--max-instances=2` plafonne déjà Cloud Run. Ajoutez une alerte de budget :

```powershell
gcloud services enable billingbudgets.googleapis.com
gcloud billing budgets create --billing-account=XXXXXX-XXXXXX-XXXXXX `
    --display-name="Polymind" --budget-amount=10EUR `   # devise = celle du compte de facturation
    --threshold-rule=percent=0.5 --threshold-rule=percent=0.9 --threshold-rule=percent=1.0
```

Une alerte prévient par e-mail mais ne coupe rien. Côté Gemini, surveillez la consommation
dans Google AI Studio.

**Restreindre l'accès** (par exemple jusqu'à la soutenance) :

```powershell
gcloud run services remove-iam-policy-binding $SERVICE --region=$REGION `
    --member="allUsers" --role="roles/run.invoker"

# Accès local pour vous (ou un membre du jury ayant gcloud et le rôle run.invoker) :
gcloud run services proxy $SERVICE --region=$REGION --port=8080
# puis ouvrir http://localhost:8080
```

Pour réouvrir : `gcloud run services add-iam-policy-binding` avec les mêmes options.
Un accès par comptes Google depuis le navigateur est possible avec Identity-Aware Proxy (IAP),
mais demande plus de configuration (écran de consentement OAuth).

## 10. Mettre à jour l'application

```powershell
gcloud builds submit --tag "${IMAGE}:v2" --timeout=3600s
gcloud run deploy $SERVICE --image="${IMAGE}:v2" --region=$REGION
```

Les autres paramètres (mémoire, secrets, compte de service…) sont conservés.
Retour arrière vers la version précédente :

```powershell
gcloud run revisions list --service=$SERVICE --region=$REGION
gcloud run services update-traffic $SERVICE --region=$REGION --to-revisions=NOM_REVISION=100
```

Chaque image stockée coûte ~0,10 $/Go/mois au-delà de 0,5 Go gratuit : supprimez les
anciennes versions (`gcloud artifacts docker images list $IMAGE`, puis
`gcloud artifacts docker images delete "${IMAGE}:v1"`).

## 11. Journaux et suivi

```powershell
gcloud run services logs read $SERVICE --region=$REGION --limit=50
```

La console Cloud Run (onglets **Metrics** et **Logs**) montre les requêtes, la latence, la
mémoire et les démarrages à froid.

## 12. Coût estimé

Ordres de grandeur pour `europe-west1` (tarifs à vérifier sur <https://cloud.google.com/run/pricing>) :

| Poste | Coût |
|---|---|
| Cloud Run sans trafic | 0 € (zéro instance) |
| Cloud Run en usage (2 vCPU, 4 Gio) | ~25 h d'usage par mois dans le niveau gratuit, puis ~0,20 $/h |
| Artifact Registry | ~0,15 $/mois par image de 2 Go conservée |
| Cloud Build | gratuit jusqu'à 2 500 min/mois |
| Secret Manager | gratuit à ce volume |
| Gemini 2.5 Flash | selon votre offre AI Studio |

Une instance est facturée tant qu'un onglet Streamlit reste ouvert (la connexion WebSocket
compte comme une requête en cours) : fermez l'onglet après une démo.

Pour supprimer l'application (ou tout le projet) :

```powershell
gcloud run services delete $SERVICE --region=$REGION
gcloud artifacts repositories delete $REPO --location=$REGION
gcloud projects delete $PROJECT_ID              # supprime tout, irréversible après 30 jours
```

## 13. Optionnel : déploiement continu avec GitHub Actions

À chaque push sur `main`, GitHub construit l'image avec Cloud Build et la déploie. GitHub
s'authentifie par **Workload Identity Federation** : aucune clé de compte de service à stocker.
Faites d'abord un déploiement manuel (étapes 1 à 7).

### 13.1 Identité de déploiement

```powershell
$GITHUB_REPO    = "Loscope29/Polymind"
$PROJECT_NUMBER = gcloud projects describe $PROJECT_ID --format="value(projectNumber)"
$DEPLOY_SA      = "polymind-deployer@$PROJECT_ID.iam.gserviceaccount.com"

gcloud iam service-accounts create polymind-deployer --display-name="Polymind (GitHub Actions)"

# Lancer un build, lire ses journaux, pousser l'image, déployer sur Cloud Run
foreach ($role in "roles/cloudbuild.builds.editor", "roles/storage.objectAdmin", "roles/viewer", `
                  "roles/serviceusage.serviceUsageConsumer", "roles/artifactregistry.writer", `
                  "roles/run.developer") {
    gcloud projects add-iam-policy-binding $PROJECT_ID --member="serviceAccount:$DEPLOY_SA" --role=$role
}
# Autoriser le déployeur à utiliser le compte polymind-run (Cloud Run)
# et le compte de service par défaut de Cloud Build
foreach ($sa in $RUN_SA, "$PROJECT_NUMBER-compute@developer.gserviceaccount.com") {
    gcloud iam service-accounts add-iam-policy-binding $sa `
        --member="serviceAccount:$DEPLOY_SA" --role="roles/iam.serviceAccountUser"
}
```

### 13.2 Confiance envers GitHub

```powershell
gcloud iam workload-identity-pools create github --location=global --display-name="GitHub"

gcloud iam workload-identity-pools providers create-oidc github-provider `
    --location=global --workload-identity-pool=github `
    --issuer-uri="https://token.actions.githubusercontent.com" `
    --attribute-mapping="google.subject=assertion.sub,attribute.repository=assertion.repository" `
    --attribute-condition="assertion.repository=='$GITHUB_REPO'"

# Seul ce dépôt GitHub peut emprunter l'identité du déployeur
gcloud iam service-accounts add-iam-policy-binding $DEPLOY_SA `
    --role="roles/iam.workloadIdentityUser" `
    --member="principalSet://iam.googleapis.com/projects/$PROJECT_NUMBER/locations/global/workloadIdentityPools/github/attribute.repository/$GITHUB_REPO"

# Valeur à copier dans les secrets GitHub (WIF_PROVIDER)
"projects/$PROJECT_NUMBER/locations/global/workloadIdentityPools/github/providers/github-provider"
```

Dans GitHub : **Settings → Secrets and variables → Actions**, créez :

| Secret | Valeur |
|---|---|
| `WIF_PROVIDER` | la ligne affichée ci-dessus |
| `DEPLOY_SA` | `polymind-deployer@<PROJECT_ID>.iam.gserviceaccount.com` |
| `GCP_PROJECT_ID` | votre `PROJECT_ID` |

### 13.3 Workflow

Créez `.github/workflows/deploy.yml` :

```yaml
name: Déploiement Cloud Run

on:
  push:
    branches: [main]
  workflow_dispatch:

permissions:
  contents: read
  id-token: write   # jeton OIDC pour Workload Identity Federation

concurrency:
  group: deploy
  cancel-in-progress: false

env:
  REGION: europe-west1
  SERVICE: polymind

jobs:
  deploy:
    runs-on: ubuntu-latest
    timeout-minutes: 70
    steps:
      - uses: actions/checkout@v4

      - uses: google-github-actions/auth@v2
        with:
          workload_identity_provider: ${{ secrets.WIF_PROVIDER }}
          service_account: ${{ secrets.DEPLOY_SA }}

      - uses: google-github-actions/setup-gcloud@v2

      - name: Build (Cloud Build)
        run: |
          IMAGE="$REGION-docker.pkg.dev/${{ secrets.GCP_PROJECT_ID }}/polymind/polymind:${GITHUB_SHA::7}"
          echo "IMAGE=$IMAGE" >> "$GITHUB_ENV"
          gcloud builds submit --tag "$IMAGE" --timeout=3600s

      - name: Déploiement
        run: gcloud run deploy "$SERVICE" --image="$IMAGE" --region="$REGION"

      - name: Vérification
        run: |
          URL=$(gcloud run services describe "$SERVICE" --region="$REGION" --format='value(status.url)')
          curl -fsS --retry 5 --retry-delay 10 "$URL/_stcore/health"
```

Les images sont étiquetées par le hash du commit : chaque révision Cloud Run correspond à un
commit précis. Pensez à purger les anciennes images (étape 10). Vérifiez au passage les
dernières versions des actions `actions/checkout` et `google-github-actions/*`.
